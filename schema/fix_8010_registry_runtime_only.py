#!/usr/bin/env python3
from pathlib import Path
import json
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

APP = Path("/Users/wesleyshu/ep_system/ep_api_system/app.py")
REG = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")
ROLLBACK = Path("/Users/wesleyshu/ep_system/ep_api_system/work_memory/rollback.md")
STAMP = time.strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = Path("/Users/wesleyshu/ep_backups") / f"ep_8010_registry_runtime_only_{STAMP}"
LOG = Path("/private/tmp/ep_api_8010_registry_runtime_only.log")
REPORT = Path("/Users/wesleyshu/ep_system/ep_api_system") / f"ep_8010_registry_runtime_only_report_{STAMP}.json"
BASE = "http://127.0.0.1:8010"

def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)

def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)

def http_request(method: str, path: str, token=None, payload=None):
    headers = {}
    data = None
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"status": resp.status, "body": body[:1200]}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"status": exc.code, "body": body[:1200]}
    except Exception as exc:
        return {"status": None, "body": repr(exc)}

def ensure_import(lines, prefix: str, name: str):
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            items = [x.strip() for x in line[len(prefix):].split(",") if x.strip()]
            if name not in items:
                items.append(name)
                lines[i] = prefix + ", ".join(items)
            return lines
    lines.insert(0, prefix + name)
    return lines

def ensure_plain_import(lines, module_name: str):
    target = f"import {module_name}"
    for line in lines:
        if line.strip() == target or line.startswith(f"from {module_name} import "):
            return lines
    lines.insert(0, target)
    return lines

def replace_block(lines, signature: str, new_block):
    for i, line in enumerate(lines):
        if line.startswith(signature):
            j = i + 1
            while j < len(lines):
                s = lines[j]
                if s.startswith("def ") or s.startswith("class ") or s.startswith("@app.") or s.startswith("@router.") or s.startswith("if __name__ =="):
                    break
                j += 1
            return lines[:i] + new_block + lines[j:], True
    return lines, False

if not APP.is_file():
    fail("APP_NOT_FOUND=" + str(APP), 1)
if not REG.is_file():
    fail("REG_NOT_FOUND=" + str(REG), 2)

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy2(str(APP), str(BACKUP_DIR / "app.py.bak"))
shutil.copy2(str(REG), str(BACKUP_DIR / "client_registry.json.bak"))

registry = json.loads(REG.read_text(encoding="utf-8"))
if not isinstance(registry, dict):
    registry = {}

token = registry.get("external_boundary_bearer_token")
if not isinstance(token, str) or len(token.strip()) < 16:
    fail("EXTERNAL_BOUNDARY_BEARER_TOKEN_MISSING", 3)
token = token.strip()

tokens = registry.get("tokens")
if not isinstance(tokens, dict):
    tokens = {}
registry["tokens"] = tokens
tokens.setdefault(token, {
    "client_id": "default_client",
    "active": True,
    "scopes": ["respond", "analyze"],
})
REG.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = APP.read_text(encoding="utf-8").splitlines()

lines = ensure_import(lines, "from fastapi import ", "Header")
lines = ensure_import(lines, "from fastapi import ", "HTTPException")
lines = ensure_plain_import(lines, "json")
lines = ensure_plain_import(lines, "re")
lines = ensure_import(lines, "from pathlib import ", "Path")

for i, line in enumerate(lines):
    if line.startswith("CLIENT_REGISTRY_PATH"):
        lines[i] = 'CLIENT_REGISTRY_PATH = "/Users/wesleyshu/ep_system/ep_api_system/client_registry.json"'
        break

loader_block = [
'def load_client_registry() -> dict:',
'    p = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")',
'    try:',
'        if not p.exists():',
'            return {"tokens": {}}',
'        data = json.loads(p.read_text(encoding="utf-8"))',
'        if isinstance(data, dict):',
'            data.setdefault("tokens", {})',
'            return data',
'        return {"tokens": {}}',
'    except Exception:',
'        return {"tokens": {}}',
'',
]

auth_block = [
'def ep_boundary_require_bearer(authorization: str = Header(None)):',
'    if not authorization or not str(authorization).startswith("Bearer "):',
'        raise HTTPException(status_code=401, detail="Missing Bearer token")',
'    token = str(authorization).split(" ", 1)[1].strip()',
'    if not token:',
'        raise HTTPException(status_code=401, detail="Empty Bearer token")',
'',
'    p = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")',
'    try:',
'        registry = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}',
'    except Exception:',
'        registry = {}',
'',
'    if not isinstance(registry, dict):',
'        registry = {}',
'',
'    allowed = set()',
'',
'    explicit = registry.get("external_boundary_bearer_token")',
'    if isinstance(explicit, str) and explicit.strip():',
'        allowed.add(explicit.strip())',
'',
'    token_map = registry.get("tokens", {})',
'    if isinstance(token_map, dict):',
'        for key, meta in token_map.items():',
'            if isinstance(key, str) and key.strip():',
'                if not isinstance(meta, dict) or meta.get("active", True):',
'                    allowed.add(key.strip())',
'',
'    if "_ep_boundary_collect_tokens" in globals():',
'        try:',
'            allowed.update(_ep_boundary_collect_tokens(registry))',
'        except Exception:',
'            pass',
'',
'    if not allowed:',
'        raise HTTPException(status_code=503, detail="No registered boundary token")',
'    if token not in allowed:',
'        raise HTTPException(status_code=403, detail="Invalid Bearer token")',
'    return True',
'',
]

lines, ok1 = replace_block(lines, "def load_client_registry() -> dict:", loader_block)
if not ok1:
    fail("LOAD_CLIENT_REGISTRY_NOT_FOUND", 4)

lines, ok2 = replace_block(lines, "def ep_boundary_require_bearer(authorization: str = Header(None)):", auth_block)
if not ok2:
    fail("EP_BOUNDARY_REQUIRE_BEARER_NOT_FOUND", 5)

APP.write_text("\n".join(lines) + "\n", encoding="utf-8")

compiled = run(["/usr/bin/python3", "-m", "py_compile", str(APP)])
if compiled.returncode != 0:
    print(compiled.stdout, end="")
    print(compiled.stderr, end="", file=sys.stderr)
    fail("PY_COMPILE_FAILED", 6)

p = run(["/usr/sbin/lsof", "-ti", "tcp:8010", "-sTCP:LISTEN"])
for raw in p.stdout.splitlines():
    raw = raw.strip()
    if raw.isdigit():
        try:
            signal.pthread_kill
        except Exception:
            pass
        try:
            import os
            os.kill(int(raw), signal.SIGTERM)
        except ProcessLookupError:
            pass

time.sleep(1)

env = dict(__import__("os").environ)
env["EP_CLIENT_REGISTRY_PATH"] = str(REG)

with open(LOG, "w", encoding="utf-8") as log_fp:
    subprocess.Popen(
        ["/usr/bin/python3", "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8010"],
        cwd="/Users/wesleyshu/ep_system/ep_api_system",
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

ready = {"status": None}
for _ in range(40):
    ready = http_request("GET", "/health")
    if ready["status"] == 200:
        break
    time.sleep(0.5)

no_health = http_request("GET", "/v1/ep/health")
bad_health = http_request("GET", "/v1/ep/health", token="INVALID_BOUNDARY_TEST_TOKEN")
ok_health = http_request("GET", "/v1/ep/health", token=token)

no_providers = http_request("GET", "/v1/ep/providers")
bad_providers = http_request("GET", "/v1/ep/providers", token="INVALID_BOUNDARY_TEST_TOKEN")
ok_providers = http_request("GET", "/v1/ep/providers", token=token)

payload = {"input": {"text": "boundary verification"}}
no_respond = http_request("POST", "/v1/ep/respond", payload=payload)
bad_respond = http_request("POST", "/v1/ep/respond", token="INVALID_BOUNDARY_TEST_TOKEN", payload=payload)
ok_respond = http_request("POST", "/v1/ep/respond", token=token, payload=payload)

result = "FAIL"
if (
    ready["status"] == 200
    and no_health["status"] == 401
    and bad_health["status"] == 403
    and ok_health["status"] == 200
    and no_providers["status"] == 401
    and bad_providers["status"] == 403
    and ok_providers["status"] == 200
    and no_respond["status"] == 401
    and bad_respond["status"] == 403
    and ok_respond["status"] not in [None, 401, 403, 503]
):
    result = "PASS"

log_tail = ""
try:
    log_tail = LOG.read_text(encoding="utf-8", errors="ignore")[-4000:]
except Exception:
    pass

report = {
    "result": result,
    "app": str(APP),
    "app_backup": str(BACKUP_DIR / "app.py.bak"),
    "registry": str(REG),
    "registry_backup": str(BACKUP_DIR / "client_registry.json.bak"),
    "runtime_log": str(LOG),
    "token_key": "external_boundary_bearer_token",
    "token_masked": token[:4] + "..." + token[-4:],
    "tests": {
        "ready": ready,
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
    "log_tail": log_tail,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if result == "PASS":
    old = ROLLBACK.read_text(encoding="utf-8", errors="ignore") if ROLLBACK.is_file() else ""
    lines = []
    lines.append("")
    lines.append("## External Auth Stable Baseline")
    lines.append("")
    lines.append("- Updated: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("- Base: http://127.0.0.1:8010")
    lines.append("- Result: PASS")
    lines.append("- Registry key: external_boundary_bearer_token")
    lines.append("- App file: " + str(APP))
    lines.append("- App backup: " + str(BACKUP_DIR / "app.py.bak"))
    lines.append("- Registry file: " + str(REG))
    lines.append("- Registry backup: " + str(BACKUP_DIR / "client_registry.json.bak"))
    lines.append("- Runtime log: " + str(LOG))
    lines.append("- No token health status: " + str(no_health["status"]))
    lines.append("- Invalid token health status: " + str(bad_health["status"]))
    lines.append("- Valid token health status: " + str(ok_health["status"]))
    lines.append("- No token providers status: " + str(no_providers["status"]))
    lines.append("- Invalid token providers status: " + str(bad_providers["status"]))
    lines.append("- Valid token providers status: " + str(ok_providers["status"]))
    lines.append("- No token respond status: " + str(no_respond["status"]))
    lines.append("- Invalid token respond status: " + str(bad_respond["status"]))
    lines.append("- Valid token respond status: " + str(ok_respond["status"]))
    lines.append("- Report: " + str(REPORT))
    ROLLBACK.write_text(old.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

print("RESULT=" + result)
print("APP=" + str(APP))
print("APP_BACKUP=" + str(BACKUP_DIR / "app.py.bak"))
print("REGISTRY=" + str(REG))
print("REGISTRY_BACKUP=" + str(BACKUP_DIR / "client_registry.json.bak"))
print("REGISTRY_KEY=external_boundary_bearer_token")
print("TOKEN_MASKED=" + token[:4] + "..." + token[-4:])
print("RUNTIME_LOG=" + str(LOG))
print("READY_STATUS=" + str(ready["status"]))
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
