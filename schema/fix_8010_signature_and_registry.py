#!/usr/bin/env python3
from pathlib import Path
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
APP = ROOT / "app.py"
REG = ROOT / "client_registry.json"
ROLLBACK = ROOT / "work_memory" / "rollback.md"
STAMP = time.strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = Path("/Users/wesleyshu/ep_backups") / ("ep_8010_signature_registry_fix_" + STAMP)
LOG = Path("/private/tmp/ep_api_8010_signature_registry_fix.log")
REPORT = ROOT / ("ep_8010_signature_registry_fix_report_" + STAMP + ".json")
BASE = "http://127.0.0.1:8010"

def fail(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)

if not APP.is_file():
    fail("APP_NOT_FOUND=" + str(APP), 1)

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy2(str(APP), str(BACKUP_DIR / "app.py.bak"))
if REG.is_file():
    shutil.copy2(str(REG), str(BACKUP_DIR / "client_registry.json.bak"))

text = APP.read_text(encoding="utf-8")

m = re.search(r"^from fastapi import ([^\n]+)$", text, flags=re.M)
if not m:
    fail("FASTAPI_IMPORT_NOT_FOUND", 2)

names = [x.strip() for x in m.group(1).split(",") if x.strip()]
if "Header" not in names:
    names.append("Header")
new_import = "from fastapi import " + ", ".join(names)
text = text[:m.start()] + new_import + text[m.end():]

new_sig = "def require_client_auth(authorization: str = Header(None)):"
text, count = re.subn(r"def\s+require_client_auth\s*\([^\)]*\)\s*:", new_sig, text, count=1)
if count == 0:
    fail("REQUIRE_CLIENT_AUTH_NOT_FOUND", 3)

APP.write_text(text, encoding="utf-8")

compile_run = subprocess.run(
    ["/usr/bin/python3", "-m", "py_compile", str(APP)],
    capture_output=True,
    text=True
)
if compile_run.returncode != 0:
    print(compile_run.stdout, end="")
    print(compile_run.stderr, end="", file=sys.stderr)
    fail("PY_COMPILE_FAILED", 4)

if REG.is_file():
    registry = json.loads(REG.read_text(encoding="utf-8"))
else:
    registry = {}

token = registry.get("external_boundary_bearer_token")
if not isinstance(token, str) or len(token.strip()) < 16:
    token = secrets.token_urlsafe(24)
    registry["external_boundary_bearer_token"] = token
    REG.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
else:
    token = token.strip()

def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

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
    stderr=subprocess.STDOUT
)

def req(method, path, token_value=None, payload=None):
    headers = {}
    data = None
    if token_value is not None:
        headers["Authorization"] = "Bearer " + token_value
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

for _ in range(40):
    ready = req("GET", "/health")
    if ready["status"] == 200:
        break
    time.sleep(0.5)

no_health = req("GET", "/v1/ep/health")
bad_health = req("GET", "/v1/ep/health", token_value="INVALID_BOUNDARY_TEST_TOKEN")
ok_health = req("GET", "/v1/ep/health", token_value=token)

no_providers = req("GET", "/v1/ep/providers")
bad_providers = req("GET", "/v1/ep/providers", token_value="INVALID_BOUNDARY_TEST_TOKEN")
ok_providers = req("GET", "/v1/ep/providers", token_value=token)

no_respond = req("POST", "/v1/ep/respond", payload={"input": {"text": "External auth boundary verification."}})
bad_respond = req("POST", "/v1/ep/respond", token_value="INVALID_BOUNDARY_TEST_TOKEN", payload={"input": {"text": "External auth boundary verification."}})
ok_respond = req("POST", "/v1/ep/respond", token_value=token, payload={"input": {"text": "External auth boundary verification."}})

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
    "app": str(APP),
    "app_backup": str(BACKUP_DIR / "app.py.bak"),
    "registry": str(REG),
    "registry_backup": str(BACKUP_DIR / "client_registry.json.bak"),
    "runtime_log": str(LOG),
    "token_key": "external_boundary_bearer_token",
    "token_masked": token[:4] + "..." + token[-4:],
    "tests": {
        "no_token_health": no_health,
        "invalid_token_health": bad_health,
        "valid_token_health": ok_health,
        "no_token_providers": no_providers,
        "invalid_token_providers": bad_providers,
        "valid_token_providers": ok_providers,
        "no_token_respond": no_respond,
        "invalid_token_respond": bad_respond,
        "valid_token_respond": ok_respond
    }
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
    lines.append("- App backup: " + str(BACKUP_DIR / "app.py.bak"))
    lines.append("- Registry file: " + str(REG))
    lines.append("- Registry key: external_boundary_bearer_token")
    lines.append("- Runtime log: " + str(LOG))
    lines.append("- Report: " + str(REPORT))
    ROLLBACK.write_text(old.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

print("RESULT=" + report["result"])
print("APP=" + str(APP))
print("APP_BACKUP=" + str(BACKUP_DIR / "app.py.bak"))
print("REGISTRY=" + str(REG))
print("REGISTRY_KEY=external_boundary_bearer_token")
print("TOKEN_MASKED=" + report["token_masked"])
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
