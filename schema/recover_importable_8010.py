#!/usr/bin/env python3
from pathlib import Path
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
import secrets

ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
APP = ROOT / "app.py"
REG = ROOT / "client_registry.json"
BACKUP_ROOT = Path("/Users/wesleyshu/ep_backups")
LOG = Path("/private/tmp/ep_api_8010_importable_recover.log")
STAMP = time.strftime("%Y%m%d_%H%M%S")
REPORT = ROOT / f"recover_importable_8010_report_{STAMP}.json"

KEYWORDS = [
    "8010",
    "request_fix",
    "auth_gate",
    "fix_8010",
    "route_auth",
    "signature_registry",
    "runtime_registry",
    "force_fix",
]

def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)

def http_code(url, token=None, payload=None):
    headers = {}
    data = None
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, headers=headers, data=data, method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return str(resp.status), body[:1200]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return str(exc.code), body[:1200]
    except Exception as exc:
        return "000", repr(exc)

def py_compile_ok(path: Path):
    r = run(["/usr/bin/python3", "-m", "py_compile", str(path)])
    return r.returncode == 0, (r.stdout + r.stderr)

def importable(candidate: Path):
    shutil.copy2(str(candidate), str(APP))
    env = dict(os.environ)
    env["EP_CLIENT_REGISTRY_PATH"] = str(REG)
    r = run(
        [
            "/usr/bin/python3",
            "-c",
            "import importlib; m=importlib.import_module('app'); assert hasattr(m,'app'); print(type(getattr(m,'app')).__name__)"
        ],
        cwd=str(ROOT),
        env=env,
    )
    return r.returncode == 0, (r.stdout + r.stderr)

def find_best_backup():
    candidates = []
    for p in BACKUP_ROOT.rglob("app.py.bak"):
        s = str(p)
        if any(k in s for k in KEYWORDS):
            try:
                candidates.append((p.stat().st_mtime, p))
            except FileNotFoundError:
                pass
    candidates.sort(reverse=True)
    tried = []
    for _, p in candidates:
        ok_compile, compile_msg = py_compile_ok(p)
        tried.append({"path": str(p), "compile_ok": ok_compile, "compile_msg": compile_msg[-400:]})
        if not ok_compile:
            continue
        ok_import, import_msg = importable(p)
        tried[-1]["import_ok"] = ok_import
        tried[-1]["import_msg"] = import_msg[-400:]
        if ok_import:
            return p, tried
    return None, tried

def ensure_registry():
    data = {}
    if REG.exists():
        try:
            data = json.loads(REG.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    token = data.get("external_boundary_bearer_token")
    if not isinstance(token, str) or len(token.strip()) < 16:
        token = secrets.token_urlsafe(24)
        data["external_boundary_bearer_token"] = token
    else:
        token = token.strip()
    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        tokens = {}
    data["tokens"] = tokens
    tokens.setdefault(token, {
        "client_id": "default_client",
        "active": True,
        "scopes": ["respond", "analyze"],
    })
    REG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return token

def stop_8010():
    p = run(["/usr/sbin/lsof", "-ti", "tcp:8010", "-sTCP:LISTEN"])
    for raw in p.stdout.splitlines():
        raw = raw.strip()
        if raw.isdigit():
            try:
                os.kill(int(raw), signal.SIGTERM)
            except ProcessLookupError:
                pass
    time.sleep(1)

def start_8010():
    env = dict(os.environ)
    env["EP_CLIENT_REGISTRY_PATH"] = str(REG)
    with open(LOG, "w", encoding="utf-8") as log_fp:
        subprocess.Popen(
            ["/usr/bin/python3", "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8010"],
            cwd=str(ROOT),
            env=env,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

def tail_log():
    if not LOG.exists():
        return ""
    try:
        return LOG.read_text(encoding="utf-8", errors="ignore")[-4000:]
    except Exception:
        return ""

def main():
    if not ROOT.is_dir():
        print("ROOT_NOT_FOUND=" + str(ROOT), file=sys.stderr)
        sys.exit(1)

    chosen, tried = find_best_backup()
    if chosen is None:
        print("NO_IMPORTABLE_APP_BACKUP_FOUND", file=sys.stderr)
        print(json.dumps(tried, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)

    sibling_reg = chosen.parent / "client_registry.json.bak"
    if sibling_reg.is_file():
        shutil.copy2(str(sibling_reg), str(REG))

    token = ensure_registry()

    stop_8010()
    start_8010()

    ready = "000"
    for _ in range(40):
        ready, _ = http_code("http://127.0.0.1:8010/health")
        if ready == "200":
            break
        time.sleep(0.5)

    no_health, no_health_body = http_code("http://127.0.0.1:8010/v1/ep/health")
    bad_health, bad_health_body = http_code("http://127.0.0.1:8010/v1/ep/health", token="INVALID_BOUNDARY_TEST_TOKEN")
    ok_health, ok_health_body = http_code("http://127.0.0.1:8010/v1/ep/health", token=token)

    no_providers, no_providers_body = http_code("http://127.0.0.1:8010/v1/ep/providers")
    bad_providers, bad_providers_body = http_code("http://127.0.0.1:8010/v1/ep/providers", token="INVALID_BOUNDARY_TEST_TOKEN")
    ok_providers, ok_providers_body = http_code("http://127.0.0.1:8010/v1/ep/providers", token=token)

    payload = {"input": {"text": "boundary verification"}}
    no_respond, no_respond_body = http_code("http://127.0.0.1:8010/v1/ep/respond", payload=payload)
    bad_respond, bad_respond_body = http_code("http://127.0.0.1:8010/v1/ep/respond", token="INVALID_BOUNDARY_TEST_TOKEN", payload=payload)
    ok_respond, ok_respond_body = http_code("http://127.0.0.1:8010/v1/ep/respond", token=token, payload=payload)

    result = "FAIL"
    if (
        ready == "200"
        and no_health == "401"
        and bad_health == "403"
        and ok_health == "200"
        and no_providers == "401"
        and bad_providers == "403"
        and ok_providers == "200"
        and no_respond == "401"
        and bad_respond == "403"
        and ok_respond not in {"000", "401", "403", "503"}
    ):
        result = "PASS"

    report = {
        "result": result,
        "good_app_backup": str(chosen),
        "app": str(APP),
        "registry": str(REG),
        "runtime_log": str(LOG),
        "token_key": "external_boundary_bearer_token",
        "token_masked": token[:4] + "..." + token[-4:],
        "tried_backups": tried,
        "tests": {
            "ready": {"status": ready},
            "no_token_health": {"status": no_health, "body": no_health_body},
            "invalid_token_health": {"status": bad_health, "body": bad_health_body},
            "valid_token_health": {"status": ok_health, "body": ok_health_body},
            "no_token_providers": {"status": no_providers, "body": no_providers_body},
            "invalid_token_providers": {"status": bad_providers, "body": bad_providers_body},
            "valid_token_providers": {"status": ok_providers, "body": ok_providers_body},
            "no_token_respond": {"status": no_respond, "body": no_respond_body},
            "invalid_token_respond": {"status": bad_respond, "body": bad_respond_body},
            "valid_token_respond": {"status": ok_respond, "body": ok_respond_body},
        },
        "log_tail": tail_log(),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("RESULT=" + result)
    print("GOOD_APP_BACKUP=" + str(chosen))
    print("APP=" + str(APP))
    print("REGISTRY=" + str(REG))
    print("REGISTRY_KEY=external_boundary_bearer_token")
    print("TOKEN_MASKED=" + token[:4] + "..." + token[-4:])
    print("RUNTIME_LOG=" + str(LOG))
    print("READY_STATUS=" + ready)
    print("NO_TOKEN_HEALTH_STATUS=" + no_health)
    print("INVALID_TOKEN_HEALTH_STATUS=" + bad_health)
    print("VALID_TOKEN_HEALTH_STATUS=" + ok_health)
    print("NO_TOKEN_PROVIDERS_STATUS=" + no_providers)
    print("INVALID_TOKEN_PROVIDERS_STATUS=" + bad_providers)
    print("VALID_TOKEN_PROVIDERS_STATUS=" + ok_providers)
    print("NO_TOKEN_RESPOND_STATUS=" + no_respond)
    print("INVALID_TOKEN_RESPOND_STATUS=" + bad_respond)
    print("VALID_TOKEN_RESPOND_STATUS=" + ok_respond)
    print("REPORT=" + str(REPORT))

if __name__ == "__main__":
    main()
