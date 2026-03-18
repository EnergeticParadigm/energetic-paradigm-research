#!/bin/bash
set -euo pipefail

APP="/Users/wesleyshu/ep_system/ep_api_system/app.py"
REG="/Users/wesleyshu/ep_system/ep_api_system/client_registry.json"
BACKUP_ROOT="/Users/wesleyshu/ep_backups"
ROLLBACK="/Users/wesleyshu/ep_system/ep_api_system/work_memory/rollback.md"
LOG="/private/tmp/ep_api_8010_recover_with_registry_env.log"
STAMP="$(/bin/date +%Y%m%d_%H%M%S)"
REPORT="/Users/wesleyshu/ep_system/ep_api_system/recover_8010_with_registry_env_report_${STAMP}.json"

GOOD_APP="$(
/usr/bin/python3 - <<'PY'
from pathlib import Path
import subprocess

BACKUP_ROOT = Path("/Users/wesleyshu/ep_backups")

def py_ok(path: Path) -> bool:
    r = subprocess.run(
        ["/usr/bin/python3", "-m", "py_compile", str(path)],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0

candidates = []
for p in BACKUP_ROOT.rglob("app.py.bak"):
    s = str(p)
    if any(k in s for k in ["8010", "request_fix", "auth_gate", "fix_8010", "route_auth", "signature_registry", "runtime_registry"]):
        try:
            if py_ok(p):
                candidates.append((p.stat().st_mtime, p))
        except FileNotFoundError:
            pass

candidates.sort(reverse=True)
print(str(candidates[0][1]) if candidates else "", end="")
PY
)"

[ -n "${GOOD_APP}" ] || { /bin/echo "NO_COMPILEABLE_APP_BACKUP_FOUND"; exit 1; }

/bin/cp "${GOOD_APP}" "${APP}"

/usr/bin/python3 - <<'PY'
from pathlib import Path
import json
import secrets

reg = Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json")
data = {}
if reg.exists():
    try:
        data = json.loads(reg.read_text(encoding="utf-8"))
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

reg.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(token, end="")
PY
TOKEN="$(
/usr/bin/python3 - <<'PY'
from pathlib import Path
import json
d = json.loads(Path("/Users/wesleyshu/ep_system/ep_api_system/client_registry.json").read_text(encoding="utf-8"))
print(d["external_boundary_bearer_token"], end="")
PY
)"

/usr/bin/python3 -m py_compile "${APP}"

/usr/bin/pkill -f "uvicorn app:app --host 127.0.0.1 --port 8010" >/dev/null 2>&1 || true
EP_CLIENT_REGISTRY_PATH="${REG}" PYTHONUNBUFFERED=1 /usr/bin/nohup /usr/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8010 >"${LOG}" 2>&1 &
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

APP="${APP}" REG="${REG}" ROLLBACK="${ROLLBACK}" BACKUP_ROOT="${BACKUP_ROOT}" GOOD_APP="${GOOD_APP}" LOG="${LOG}" REPORT="${REPORT}" TOKEN="${TOKEN}" \
READY="${READY}" NO_HEALTH="${NO_HEALTH}" BAD_HEALTH="${BAD_HEALTH}" OK_HEALTH="${OK_HEALTH}" \
NO_PROVIDERS="${NO_PROVIDERS}" BAD_PROVIDERS="${BAD_PROVIDERS}" OK_PROVIDERS="${OK_PROVIDERS}" \
NO_RESPOND="${NO_RESPOND}" BAD_RESPOND="${BAD_RESPOND}" OK_RESPOND="${OK_RESPOND}" RESULT="${RESULT}" \
/usr/bin/python3 - <<'PY'
import json
import os
from pathlib import Path

report = {
    "result": os.environ["RESULT"],
    "good_app_backup": os.environ["GOOD_APP"],
    "app": os.environ["APP"],
    "registry": os.environ["REG"],
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
    lines.append("- Restored app backup: " + os.environ["GOOD_APP"])
    lines.append("- Registry file: " + os.environ["REG"])
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
/bin/echo "GOOD_APP_BACKUP=${GOOD_APP}"
/bin/echo "APP=${APP}"
/bin/echo "REGISTRY=${REG}"
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
/usr/bin/tail -n 80 "${LOG}"
