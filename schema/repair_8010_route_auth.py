#!/usr/bin/env python3
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
APP = ROOT / "app.py"
REG = ROOT / "client_registry.json"
ROLLBACK = ROOT / "work_memory" / "rollback.md"
BACKUP_ROOT = Path("/Users/wesleyshu/ep_backups")
STAMP = time.strftime("%Y%m%d_%H%M%S")
SESSION_BACKUP_DIR = BACKUP_ROOT / f"ep_8010_route_auth_repair_{STAMP}"
LOG = Path("/private/tmp/ep_api_8010_route_auth_repair.log")
REPORT = ROOT / f"ep_8010_route_auth_repair_report_{STAMP}.json"
BASE = "http://127.0.0.1:8010"

TARGETS = [
    ("get", "/v1/ep/health"),
    ("get", "/v1/ep/providers"),
    ("post", "/v1/ep/respond"),
    ("post", "/v1/ep/analyze"),
]

def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)

def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

def py_compile_ok(path: Path) -> bool:
    r = run(["/usr/bin/python3", "-m", "py_compile", str(path)])
    return r.returncode == 0

def find_latest_good_backup() -> Path:
    candidates = []
    for p in BACKUP_ROOT.rglob("app.py.bak"):
        s = str(p)
        if any(k in s for k in ["8010", "request_fix", "auth_gate", "fix_8010"]):
            try:
                candidates.append((p.stat().st_mtime, p))
            except FileNotFoundError:
                pass
    candidates.sort(reverse=True)
    for _, p in candidates:
        if py_compile_ok(p):
            return p
    raise FileNotFoundError("NO_COMPILEABLE_APP_BACKUP_FOUND")

def ensure_depends_import(text: str) -> str:
    m = re.search(r"^from fastapi import ([^\n]+)$", text, flags=re.M)
    if not m:
        fail("FASTAPI_IMPORT_NOT_FOUND", 2)
    names = [x.strip() for x in m.group(1).split(",") if x.strip()]
    if "Depends" not in names:
        names.append("Depends")
    newline = "from fastapi import " + ", ".join(names)
    return text[:m.start()] + newline + text[m.end():]

def detect_auth_function(text: str) -> str:
    if "def require_client_auth(" in text:
        return "require_client_auth"
    m = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*authorization\b[\s\S]{0,220}?Header", text)
    if m:
        return m.group(1)
    fail("AUTH_FUNCTION_NOT_FOUND", 3)

def patch_route_line(text: str, method: str, path: str, auth_func: str):
    dep = f'Depends({auth_func})'
    pattern_exact = re.compile(
        rf'^@app\.{method}\("{re.escape(path)}"\)\s*$',
        flags=re.M
    )
    pattern_dep = re.compile(
        rf'^@app\.{method}\("{re.escape(path)}",[^\n]*dependencies=\[[^\n]*{re.escape(dep)}[^\n]*\]\)\s*$',
        flags=re.M
    )
    if pattern_dep.search(text):
        return text, 1

    replacement = f'@app.{method}("{path}", dependencies=[{dep}])'
    new_text, count = pattern_exact.subn(replacement, text, count=1)
    if count == 1:
        return new_text, 1

    pattern_existing = re.compile(
        rf'^@app\.{method}\("{re.escape(path)}",(.*)\)\s*$',
        flags=re.M
    )
    m = pattern_existing.search(text)
    if not m:
        return text, 0

    tail = m.group(1)
    if "dependencies=" in tail:
        def repl(mm):
            body = mm.group(1).strip()
            if dep in body:
                return mm.group(0)
            if body:
                return f"dependencies=[{body}, {dep}]"
            return f"dependencies=[{dep}]"
        new_tail = re.sub(r"dependencies\s*=\s*\[([^\]]*)\]", repl, tail, count=1)
        new_line = f'@app.{method}("{path}",{new_tail})'
    else:
        new_line = f'@app.{method}("{path}",{tail}, dependencies=[{dep}])'

    return text[:m.start()] + new_line + text[m.end():], 1

def restart_8010() -> None:
    p = run(["/usr/sbin/lsof", "-ti", "tcp:8010", "-sTCP:LISTEN"])
    for raw in p.stdout.splitlines():
        raw = raw.strip()
        if raw.isdigit():
            try:
                os.kill(int(raw), signal.SIGTERM)
            except ProcessLookupError:
                pass

    time.sleep(1)

    log_fp = open(str(LOG), "w", encoding="utf-8")
    subprocess.Popen(
        ["/usr/bin/python3", "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8010"],
        cwd=str(ROOT),
        stdout=log_fp,
        stderr=subprocess.STDOUT,
    )

def req(method: str, path: str, token=None, payload=None):
    headers = {}
    data = None
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"status": resp.status, "body": body[:1200]}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"status": exc.code, "body": body[:1200]}
    except Exception as exc:
        return {"status": None, "body": repr(exc)}

def collect_tokens(obj):
    found = set()
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                lk = str(k).lower()
                if isinstance(v, str):
                    s = v.strip()
                    if s and (
                        any(w in lk for w in ["token", "bearer", "secret", "auth", "access", "api_key", "apikey"])
                        or re.fullmatch(r"[A-Za-z0-9._~+/=-]{16,}", s)
                    ):
                        found.add(s)
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, str):
            s = cur.strip()
            if s and re.fullmatch(r"[A-Za-z0-9._~+/=-]{16,}", s):
                found.add(s)
    return sorted(found)

def main():
    if not APP.is_file():
        fail("APP_NOT_FOUND=" + str(APP), 1)

    good_backup = find_latest_good_backup()

    SESSION_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(APP), str(SESSION_BACKUP_DIR / "app_before_repair.py.bak"))
    shutil.copy2(str(good_backup), str(APP))

    text = APP.read_text(encoding="utf-8")
    auth_func = detect_auth_function(text)
    text = ensure_depends_import(text)

    patch_counts = {}
    for method, path in TARGETS:
        text, count = patch_route_line(text, method, path, auth_func)
        patch_counts[f"{method}:{path}"] = count

    missing = [k for k, v in patch_counts.items() if v == 0]
    if missing:
        fail("ROUTE_PATCH_FAILED=" + ",".join(missing), 4)

    APP.write_text(text, encoding="utf-8")

    compile_run = run(["/usr/bin/python3", "-m", "py_compile", str(APP)])
    if compile_run.returncode != 0:
        print(compile_run.stdout, end="")
        print(compile_run.stderr, end="", file=sys.stderr)
        fail("PY_COMPILE_FAILED", 5)

    restart_8010()

    for _ in range(40):
        ready = req("GET", "/health")
        if ready["status"] == 200:
            break
        time.sleep(0.5)

    if not REG.is_file():
        fail("REGISTRY_NOT_FOUND=" + str(REG), 6)

    registry = json.loads(REG.read_text(encoding="utf-8"))
    tokens = collect_tokens(registry)
    if not tokens:
        fail("TOKEN_NOT_FOUND_IN_REGISTRY", 7)

    token = tokens[0]

    no_health = req("GET", "/v1/ep/health")
    bad_health = req("GET", "/v1/ep/health", token="INVALID_BOUNDARY_TEST_TOKEN")
    ok_health = req("GET", "/v1/ep/health", token=token)

    no_providers = req("GET", "/v1/ep/providers")
    bad_providers = req("GET", "/v1/ep/providers", token="INVALID_BOUNDARY_TEST_TOKEN")
    ok_providers = req("GET", "/v1/ep/providers", token=token)

    no_respond = req(
        "POST",
        "/v1/ep/respond",
        payload={"input": {"text": "External auth boundary verification."}},
    )
    bad_respond = req(
        "POST",
        "/v1/ep/respond",
        token="INVALID_BOUNDARY_TEST_TOKEN",
        payload={"input": {"text": "External auth boundary verification."}},
    )
    ok_respond = req(
        "POST",
        "/v1/ep/respond",
        token=token,
        payload={"input": {"text": "External auth boundary verification."}},
    )

    passed = (
        no_health["status"] in [401, 403]
        and bad_health["status"] in [401, 403]
        and ok_health["status"] == 200
        and no_providers["status"] in [401, 403]
        and bad_providers["status"] in [401, 403]
        and ok_providers["status"] == 200
        and no_respond["status"] in [401, 403]
        and bad_respond["status"] in [401, 403]
        and ok_respond["status"] not in [401, 403, None]
    )

    report = {
        "result": "PASS" if passed else "FAIL",
        "auth_function": auth_func,
        "restored_from": str(good_backup),
        "app": str(APP),
        "session_backup": str(SESSION_BACKUP_DIR / "app_before_repair.py.bak"),
        "runtime_log": str(LOG),
        "token_masked": token[:4] + "..." + token[-4:],
        "patch_counts": patch_counts,
        "tests": {
            "no_token_health": no_health,
            "invalid_token_health": bad_health,
            "valid_token_health": ok_health,
            "no_token_providers": no_providers,
            "invalid_token_providers": bad_providers,
            "valid_token_providers": ok_providers,
            "no_token_respond": no_respond,
            "invalid_token_respond": bad_respond,
            "valid_token_respond": ok_respond,
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if passed:
        old = ROLLBACK.read_text(encoding="utf-8", errors="ignore") if ROLLBACK.is_file() else ""
        lines = []
        lines.append("")
        lines.append("## External Auth Stable Baseline")
        lines.append("")
        lines.append("- Updated: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        lines.append("- Base: " + BASE)
        lines.append("- Result: PASS")
        lines.append("- Auth function: " + auth_func)
        lines.append("- Restored from: " + str(good_backup))
        lines.append("- No token health status: " + str(no_health["status"]))
        lines.append("- Invalid token health status: " + str(bad_health["status"]))
        lines.append("- Valid token health status: " + str(ok_health["status"]))
        lines.append("- No token providers status: " + str(no_providers["status"]))
        lines.append("- Invalid token providers status: " + str(bad_providers["status"]))
        lines.append("- Valid token providers status: " + str(ok_providers["status"]))
        lines.append("- No token respond status: " + str(no_respond["status"]))
        lines.append("- Invalid token respond status: " + str(bad_respond["status"]))
        lines.append("- Valid token respond status: " + str(ok_respond["status"]))
        lines.append("- App file: " + str(APP))
        lines.append("- Session backup: " + str(SESSION_BACKUP_DIR / "app_before_repair.py.bak"))
        lines.append("- Runtime log: " + str(LOG))
        lines.append("- Report: " + str(REPORT))
        ROLLBACK.write_text(old.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

    print("RESULT=" + report["result"])
    print("AUTH_FUNCTION=" + auth_func)
    print("RESTORED_FROM=" + str(good_backup))
    print("APP=" + str(APP))
    print("SESSION_BACKUP=" + str(SESSION_BACKUP_DIR / "app_before_repair.py.bak"))
    print("RUNTIME_LOG=" + str(LOG))
    print("NO_TOKEN_HEALTH_STATUS=" + str(no_health["status"]))
    print("INVALID_TOKEN_HEALTH_STATUS=" + str(bad_health["status"]))
    print("VALID_TOKEN_HEALTH_STATUS=" + str(ok_health["status"]))
    print("NO_TOKEN_PROVIDERS_STATUS=" + str(no_providers["status"]))
    print("INVALID_TOKEN_PROVIDERS_STATUS=" + str(bad_providers["status"]))
    print("VALID_TOKEN_PROVIDERS_STATUS=" + str(ok_providers["status"]))
    print("NO_TOKEN_RESPOND_STATUS=" + str(no_respond["status"]))
    print("INVALID_TOKEN_RESPOND_STATUS=" + str(bad_respond["status"]))
    print("VALID_TOKEN_RESPOND_STATUS=" + str(ok_respond["status"]))
    print("REPORT=" + str(REPORT))
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
