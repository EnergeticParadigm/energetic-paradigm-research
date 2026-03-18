#!/bin/bash
set -euo pipefail

ROOT="/Users/wesleyshu/ep_system"
OUT="/Users/wesleyshu/ep_system/ep_api_system/diagnose_8010_auth_gate_$(/bin/date +%Y%m%d_%H%M%S).log"

{
  echo "=== 8010 AUTH GATE DIAGNOSE ==="
  echo "TIME=$(/bin/date '+%Y-%m-%d %H:%M:%S')"
  echo "ROOT=${ROOT}"
  echo

  echo "=== PORT 8010 PROCESS ==="
  /usr/sbin/lsof -nP -iTCP:8010 -sTCP:LISTEN || true
  echo

  echo "=== FILES MENTIONING 8010 ==="
  /usr/bin/grep -RIn --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='__pycache__' '8010' "${ROOT}" || true
  echo

  echo "=== FILES MENTIONING Authorization / Bearer / client_registry ==="
  /usr/bin/grep -RIn --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='__pycache__' -E 'Authorization|Bearer|client_registry|registry|auth token|auth_token|verify.*token|token.*verify|require_auth|check_auth|authenticate' "${ROOT}" || true
  echo

  echo "=== FILES MENTIONING /v1/ep/health OR /v1/ep/respond ==="
  /usr/bin/grep -RIn --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='__pycache__' -E '/v1/ep/health|/v1/ep/respond|health|respond' "${ROOT}" || true
  echo

  echo "=== FASTAPI / FLASK ROUTE DECLARATIONS ==="
  /usr/bin/grep -RIn --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='__pycache__' -E '@app\.(get|post|api_route)|APIRouter|FastAPI\(|Flask\(|Blueprint\(' "${ROOT}" || true
  echo

  echo "=== CANDIDATE SERVER FILES ==="
  /usr/bin/find "${ROOT}" -type f \( -name '*.py' -o -name '*.sh' -o -name '*.service' -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) | /usr/bin/grep -E 'ep_api|8010|server|app|main|launch|start|run' || true
  echo

  echo "=== CURRENT REGISTRY FILE ==="
  /bin/cat /Users/wesleyshu/ep_system/ep_api_system/client_registry.json 2>/dev/null || true
  echo
} | /usr/bin/tee "${OUT}"

echo "REPORT=${OUT}"
