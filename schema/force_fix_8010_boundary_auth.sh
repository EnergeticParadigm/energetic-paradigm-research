#!/bin/bash
set -euo pipefail

APP="/Users/wesleyshu/ep_system/ep_api_system/app.py"
REG="/Users/wesleyshu/ep_system/ep_api_system/client_registry.json"
ROLLBACK="/Users/wesleyshu/ep_system/ep_api_system/work_memory/rollback.md"
STAMP="$(/bin/date +%Y%m%d_%H%M%S)"
BACKUP_DIR="/Users/wesleyshu/ep_backups/ep_8010_force_fix_${STAMP}"
LOG="/private/tmp/ep_api_8010_force_fix.log"
REPORT="/Users/wesleyshu/ep_system/ep_api_system/ep_8010_force_fix_report_${STAMP}.json"

/bin/mkdir -p "${BACKUP_DIR}"
/bin/cp "${APP}" "${BACKUP_DIR}/app.py.bak"
/bin/cp "${REG}" "${BACKUP_DIR}/client_registry.json.bak" 2>/dev/null || true

/usr/bin/python3 - <<'PY'
from pathlib import Path
import json
import re
import secrets

APP = Path("/Users/wesleyshu/ep_system/ep_api_system/app.py")
REG = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")

text = APP.read_text(encoding="utf-8")

text, n1 = re.subn(
    r'^CLIENT_REGISTRY_PATH\s*=.*$',
    'CLIENT_REGISTRY_PATH = "/Users/wesleyshu/ep_system/ep_api_system/client_registry.json"',
    text,
    flags=re.M,
)
if n1 != 1:
    raise SystemExit("CLIENT_REGISTRY_PATH_PATCH_FAILED")

pattern_loader = re.compile(
    r'def load_client_registry\(\) -> dict:\n(?:(?:    ).*\n)+',
    flags=0,
)
replacement_loader = '''def load_client_registry() -> dict:
    p = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")
    try:
        if not p.exists():
            return {"tokens": {}}
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("tokens", {})
            return data
        return {"tokens": {}}
    except Exception:
        return {"tokens": {}}
'''
text, n2 = pattern_loader.subn(replacement_loader, text, count=1)
if n2 != 1:
    raise SystemExit("LOAD_CLIENT_REGISTRY_PATCH_FAILED")

pattern_auth = re.compile(
    r'def ep_boundary_require_bearer\(authorization: str = Header\(None\)\):\n(?:(?:    ).*\n)+',
    flags=0,
)
replacement_auth = '''def ep_boundary_require_bearer(authorization: str = Header(None)):
    if not authorization or not str(authorization).startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = str(authorization).split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty Bearer token")

    p = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")
    try:
        registry = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        registry = {}

    allowed = set()

    explicit = registry.get("external_boundary_bearer_token")
    if isinstance(explicit, str) and explicit.strip():
        allowed.add(explicit.strip())

    token_map = registry.get("tokens", {})
    if isinstance(token_map, dict):
        for key in token_map.keys():
            if isinstance(key, str) and key.strip():
                allowed.add(key.strip())

    allowed.update(_ep_boundary_collect_tokens(registry))

    if not allowed:
        raise HTTPException(status_code=503, detail="No registered boundary token")
    if token not in allowed:
        raise HTTPException(status_code=403, detail="Invalid Bearer token")
    return True
'''
text, n3 = pattern_auth.subn(replacement_auth, text, count=1)
if n3 != 1:
    raise SystemExit("BOUNDARY_AUTH_PATCH_FAILED")

APP.write_text(text, encoding="utf-8")

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

data.setdefault("tokens", {})
data["tokens"].setdefault(token, {
    "client_id": "default_client",
    "active": True,
    "scopes": ["respond", "analyze"],
})
REG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(token, end="")
PY

/usr/bin/python3 -m py_compile "${APP}"

TOKEN="$(
/usr/bin/python3 -c 'import json; from pathlib import Path; d=json.loads(Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json").read_text(encoding="utf-8")); print(d["external_boundary_bearer_token"], end="")'
)"

/usr/bin/pkill -f "uvicorn app:app --host 127.0.0.1 --port 8010" >/dev/null 2>&1 || true
/usr/bin/nohup /usr/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8010 >"${LOG}" 2>&1 &
/bin/sleep 3

READY="$(
/usr/bin/curl -sS -o /tmp/ep_ready_${STAMP}.out -w "%{http_code}" http://127.0.0.1:8010/health || true
)"

NO_HEALTH="$(
/usr/bin/curl -sS -o /tmp/ep_no_health_${STAMP}.out -w "%{http_code}" http://127.0.0.1:8010/v1/ep/health || true
)"
BAD_HEALTH="$(
/usr/bin/curl -sS -o /tmp/ep_bad_health_${STAMP}.out -w "%{http_code}" -H "Authorization: Bearer INVALID_BOUNDARY_TEST_TOKEN" http://127.0.0.1:8010/v1/ep/health || true
)"
OK_HEALTH="$(
/usr/bin/curl -sS -o /tmp/ep_ok_health_${STAMP}.out -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" http://127.0.0.1:8010/v1/ep/health || true
)"

NO_PROVIDERS="$(
/usr/bin/curl -sS -o /tmp/ep_no_providers_${STAMP}.out -w "%{http_code}" http://127.0.0.1:8010/v1/ep/providers || true
)"
BAD_PROVIDERS="$(
/usr/bin/curl -sS -o /tmp/ep_bad_providers_${STAMP}.out -w "%{http_code}" -H "Authorization: Bearer INVALID_BOUNDARY_TEST_TOKEN" http://127.0.0.1:8010/v1/ep/providers || true
)"
OK_PROVIDERS="$(
/usr/bin/curl -sS -o /tmp/ep_ok_providers_${STAMP}.out -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" http://127.0.0.1:8010/v1/ep/providers || true
)"

NO_RESPOND="$(
/usr/bin/curl -sS -o /tmp/ep_no_respond_${STAMP}.out -w "%{http_code}" -H "Content-Type: application/json" -d '{"input":{"text":"boundary verification"}}' http://127.0.0.1:8010/v1/ep/respond || true
)"
BAD_RESPOND="$(
/usr/bin/curl -sS -o /tmp/ep_bad_respond_${STAMP}.out -w "%{http_code}" -H "Authorization: Bearer INVALID_BOUNDARY_TEST_TOKEN" -H "Content-Type: application/json" -d '{"input":{"text":"boundary verification"}}' http://127.0.0.1:8010/v1/ep/respond || true
)"
OK_RESPOND="$(
/usr/bin/curl -sS -o /tmp/ep_ok_respond_${STAMP}.out -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"input":{"text":"boundary verification"}}' http://127.0.0.1:8010/v1/ep/respond || true
)"

RESULT="FAIL"
if [ "${READY}" = "200" ] && \
   [ "${NO_HEALTH}" = "401" ] && \
   [ "${BAD_HEALTH}" = "403" ] && \
   [ "${OK_HEALTH}" = "200" ] && \
   [ "${NO_PROVIDERS}" = "401" ] && \
   [ "${BAD_PROVIDERS}" = "403" ] && \
   [ "${OK_PROVIDERS}" = "200" ] && \
   [ "${NO_RESPOND}" = "401" ] && \
   [ "${BAD_RESPOND}" = "403" ] && \
   [ "${OK_RESPOND}" != "401" ] && [ "${OK_RESPOND}" != "403" ] && [ "${OK_RESPOND}" != "503" ] && [ "${OK_RESPOND}" != "000" ]; then
  RESULT="PASS"
fi

APP="${APP}" REG="${REG}" ROLLBACK="${ROLLBACK}" BACKUP_DIR="${BACKUP_DIR}" LOG="${LOG}" REPORT="${REPORT}" TOKEN="${TOKEN}" \
READY="${READY}" NO_HEALTH="${NO_HEALTH}" BAD_HEALTH="${BAD_HEALTH}" OK_HEALTH="${OK_HEALTH}" \
NO_PROVIDERS="${NO_PROVIDERS}" BAD_PROVIDERS="${BAD_PROVIDERS}" OK_PROVIDERS="${OK_PROVIDERS}" \
NO_RESPOND="${NO_RESPOND}" BAD_RESPOND="${BAD_RESPOND}" OK_RESPOND="${OK_RESPOND}" RESULT="${RESULT}" \
/usr/bin/python3 - <<'PY'
import json
import os
from pathlib import Path

report = {
    "result": os.environ["RESULT"],
    "app": os.environ["APP"],
    "app_backup": os.environ["BACKUP_DIR"] + "/app.py.bak",
    "registry": os.environ["REG"],
    "registry_backup": os.environ["BACKUP_DIR"] + "/client_registry.json.bak",
    "runtime_log": os.environ["LOG"],
    "token_key": "external_boundary_bearer_token",
    "token_masked": os.environ["TOKEN"][:4] + "..." + os.environ["TOKEN"][-4:],
    "tests": {
        "ready": {"status": os.environ["READY"]},
        "no_token_health": {"status": os.environ["NO_HEALTH"]},
        "invalid_token_health": {"status": os.environ["BAD_HEALTH"]},
        "valid_token_health": {"status": os.environ["OK_HEALTH"]},
        "no_token_providers": {"status": os.environ["NO_PROVIDERS"]},
        "invalid_token_providers": {"status": os.environ["BAD_PROVIDERS"]},
        "valid_token_providers": {"status": os.environ["OK_PROVIDERS"]},
        "no_token_respond": {"status": os.environ["NO_RESPOND"]},
        "invalid_token_respond": {"status": os.environ["BAD_RESPOND"]},
        "valid_token_respond": {"status": os.environ["OK_RESPOND"]},
    },
}
Path(os.environ["REPORT"]).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if os.environ["RESULT"] == "PASS":
    rb = Path(os.environ["ROLLBACK"])
    old = rb.read_text(encoding="utf-8", errors="ignore") if rb.is_file() else ""
    lines = []
    lines.append("")
    lines.append("## External Auth Stable Baseline")
    lines.append("")
    lines.append("- Updated: " + os.popen('/bin/date "+%Y-%m-%d %H:%M:%S"').read().strip())
    lines.append("- Base: http://127.0.0.1:8010")
    lines.append("- Result: PASS")
    lines.append("- Registry key: external_boundary_bearer_token")
    lines.append("- App file: " + os.environ["APP"])
    lines.append("- App backup: " + os.environ["BACKUP_DIR"] + "/app.py.bak")
    lines.append("- Registry file: " + os.environ["REG"])
    lines.append("- Registry backup: " + os.environ["BACKUP_DIR"] + "/client_registry.json.bak")
    lines.append("- Runtime log: " + os.environ["LOG"])
    lines.append("- No token health status: " + os.environ["NO_HEALTH"])
    lines.append("- Invalid token health status: " + os.environ["BAD_HEALTH"])
    lines.append("- Valid token health status: " + os.environ["OK_HEALTH"])
    lines.append("- No token providers status: " + os.environ["NO_PROVIDERS"])
    lines.append("- Invalid token providers status: " + os.environ["BAD_PROVIDERS"])
    lines.append("- Valid token providers status: " + os.environ["OK_PROVIDERS"])
    lines.append("- No token respond status: " + os.environ["NO_RESPOND"])
    lines.append("- Invalid token respond status: " + os.environ["BAD_RESPOND"])
    lines.append("- Valid token respond status: " + os.environ["OK_RESPOND"])
    lines.append("- Report: " + os.environ["REPORT"])
    rb.write_text(old.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
PY

/bin/echo "RESULT=${RESULT}"
/bin/echo "APP=${APP}"
/bin/echo "APP_BACKUP=${BACKUP_DIR}/app.py.bak"
/bin/echo "REGISTRY=${REG}"
/bin/echo "REGISTRY_BACKUP=${BACKUP_DIR}/client_registry.json.bak"
/bin/echo "REGISTRY_KEY=external_boundary_bearer_token"
/bin/echo "TOKEN_MASKED=${TOKEN:0:4}...${TOKEN: -4}"
/bin/echo "RUNTIME_LOG=${LOG}"
/bin/echo "READY_STATUS=${READY}"
/bin/echo "NO_TOKEN_HEALTH_STATUS=${NO_HEALTH}"
/bin/echo "INVALID_TOKEN_HEALTH_STATUS=${BAD_HEALTH}"
/bin/echo "VALID_TOKEN_HEALTH_STATUS=${OK_HEALTH}"
/bin/echo "NO_TOKEN_PROVIDERS_STATUS=${NO_PROVIDERS}"
/bin/echo "INVALID_TOKEN_PROVIDERS_STATUS=${BAD_PROVIDERS}"
/bin/echo "VALID_TOKEN_PROVIDERS_STATUS=${OK_PROVIDERS}"
/bin/echo "NO_TOKEN_RESPOND_STATUS=${NO_RESPOND}"
/bin/echo "INVALID_TOKEN_RESPOND_STATUS=${BAD_RESPOND}"
/bin/echo "VALID_TOKEN_RESPOND_STATUS=${OK_RESPOND}"
/bin/echo "REPORT=${REPORT}"
