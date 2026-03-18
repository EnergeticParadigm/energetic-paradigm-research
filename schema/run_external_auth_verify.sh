#!/bin/bash
set -euo pipefail

ROOT="/Users/wesleyshu/ep_system/ep_api_system"
WORK="/Users/wesleyshu/ep_system/ep_api_system/work_memory"
REG="/Users/wesleyshu/ep_system/ep_api_system/client_registry.json"
STATUS="/Users/wesleyshu/ep_system/ep_api_system/work_memory/current_status.md"
NEXT="/Users/wesleyshu/ep_system/ep_api_system/work_memory/next_step.md"
ROLLBACK="/Users/wesleyshu/ep_system/ep_api_system/work_memory/rollback.md"
REPO="/Users/wesleyshu/ep-public-reports"
VERIFY_SCRIPT="/Users/wesleyshu/ep_system/ep_api_system/verify_public_schema_release.sh"

STAMP="$(/bin/date +%Y%m%d_%H%M%S)"
BACKUP_DIR="/Users/wesleyshu/ep_backups/external_auth_verify_${STAMP}"
REPORT="/Users/wesleyshu/ep_system/ep_api_system/work_memory/external_auth_smoke_${STAMP}.md"

BASE_URL="http://127.0.0.1:8010"
ROUTES=("/v1/ep/health" "/v1/ep/providers")

/bin/mkdir -p "${BACKUP_DIR}"

for f in "${STATUS}" "${NEXT}" "${ROLLBACK}" "${REG}"; do
  if [ -f "${f}" ]; then
    /bin/cp "${f}" "${BACKUP_DIR}/$(/usr/bin/basename "${f}").bak"
  fi
done

if [ ! -f "${REG}" ]; then
  /bin/echo "MISSING_REGISTRY=${REG}" >&2
  exit 1
fi

TOKEN="$("/usr/bin/python3" -c 'import json, sys
from pathlib import Path
keys = {"token","bearer","bearer_token","api_key","access_token","client_token","secret","client_secret"}
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
cand = []
stack = [data]
while stack:
    obj = stack.pop()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                stack.append(v)
            elif isinstance(v, str) and v.strip():
                lk = str(k).lower()
                if lk in keys or "token" in lk or "bearer" in lk or "api_key" in lk:
                    cand.append(v.strip())
    elif isinstance(obj, list):
        stack.extend(obj)
seen = []
for v in cand:
    if v not in seen and len(v) >= 8:
        seen.append(v)
sys.stdout.write(seen[0] if seen else "")' "${REG}")"

if [ -n "${VALID_BEARER_TOKEN:-}" ]; then
  TOKEN="${VALID_BEARER_TOKEN}"
fi

if [ -z "${TOKEN}" ]; then
  /bin/echo "TOKEN_NOT_FOUND" >&2
  exit 1
fi

curl_code() {
  local mode="$1"
  local route="$2"
  local outfile="$3"
  if [ "${mode}" = "none" ]; then
    /usr/bin/curl -sS -o "${outfile}" -w "%{http_code}" "${BASE_URL}${route}" || true
  elif [ "${mode}" = "invalid" ]; then
    /usr/bin/curl -sS -o "${outfile}" -w "%{http_code}" -H "Authorization: Bearer INVALID_TOKEN_${STAMP}" "${BASE_URL}${route}" || true
  else
    /usr/bin/curl -sS -o "${outfile}" -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}${route}" || true
  fi
}

choose_route() {
  local route
  local code
  for route in "${ROUTES[@]}"; do
    code="$(curl_code valid "${route}" "${BACKUP_DIR}/valid_probe_$(/usr/bin/basename "${route}").txt")"
    case "${code}" in
      2??)
        /bin/echo "${route}"
        return 0
        ;;
    esac
  done
  return 1
}

ROUTE="$(choose_route || true)"
if [ -z "${ROUTE}" ]; then
  /bin/echo "NO_WORKING_PROTECTED_ROUTE_ON_8010" >&2
  exit 1
fi

NO_CODE="$(curl_code none "${ROUTE}" "${BACKUP_DIR}/no_bearer_body.txt")"
BAD_CODE="$(curl_code invalid "${ROUTE}" "${BACKUP_DIR}/invalid_bearer_body.txt")"
OK_CODE="$(curl_code valid "${ROUTE}" "${BACKUP_DIR}/valid_bearer_body.txt")"

case "${NO_CODE}" in
  401|403) : ;;
  *)
    /bin/echo "UNAUTHORIZED_REJECTION_FAILED=${NO_CODE}" >&2
    exit 1
    ;;
esac

case "${BAD_CODE}" in
  401|403) : ;;
  *)
    /bin/echo "INVALID_TOKEN_REJECTION_FAILED=${BAD_CODE}" >&2
    exit 1
    ;;
esac

case "${OK_CODE}" in
  2??) : ;;
  *)
    /bin/echo "VALID_TOKEN_SUCCESS_FAILED=${OK_CODE}" >&2
    exit 1
    ;;
esac

/bin/cat > "${VERIFY_SCRIPT}" <<'SH'
#!/bin/bash
set -euo pipefail

REPO="/Users/wesleyshu/ep-public-reports"
FILES=(
  "schema/README.md"
  "schema/openapi.yaml"
  "schema/contract_alignment_report.json"
  "schema/schema_test_result.json"
  "schema/schema_test_result_en.json"
  "schema/schema_test_result_en_after_patch.json"
)

FORBIDDEN_REGEX='127\.0\.0\.1:8010|ep/trigger1|/EP/trigger1|ep/terrence920|terrence920'
REQUIRED_README_REGEX='Authorization: Bearer <token>|AUTHORIZED_TRIGGER'
REQUIRED_OPENAPI_REGEX='Authorization: Bearer <token>|AUTHORIZED_TRIGGER|BearerAuth'

/usr/bin/git -C "${REPO}" fetch origin >/dev/null 2>&1 || true

for f in "${FILES[@]}"; do
  if [ ! -f "${REPO}/${f}" ]; then
    /bin/echo "MISSING_LOCAL=${REPO}/${f}" >&2
    exit 1
  fi
done

for f in "${FILES[@]}"; do
  if /usr/bin/grep -nE "${FORBIDDEN_REGEX}" "${REPO}/${f}" >/dev/null 2>&1; then
    /bin/echo "FORBIDDEN_LOCAL=${f}" >&2
    /usr/bin/grep -nE "${FORBIDDEN_REGEX}" "${REPO}/${f}" >&2 || true
    exit 1
  fi
done

if ! /usr/bin/grep -nE "${REQUIRED_README_REGEX}" "${REPO}/schema/README.md" >/dev/null 2>&1; then
  /bin/echo "README_REQUIRED_TEXT_MISSING" >&2
  exit 1
fi

if ! /usr/bin/grep -nE "${REQUIRED_OPENAPI_REGEX}" "${REPO}/schema/openapi.yaml" >/dev/null 2>&1; then
  /bin/echo "OPENAPI_REQUIRED_TEXT_MISSING" >&2
  exit 1
fi

for f in "schema/README.md" "schema/openapi.yaml" "schema/contract_alignment_report.json"; do
  if /usr/bin/git -C "${REPO}" show "origin/main:${f}" | /usr/bin/grep -nE "${FORBIDDEN_REGEX}" >/dev/null 2>&1; then
    /bin/echo "FORBIDDEN_REMOTE=${f}" >&2
    /usr/bin/git -C "${REPO}" show "origin/main:${f}" | /usr/bin/grep -nE "${FORBIDDEN_REGEX}" >&2 || true
    exit 1
  fi
done

/bin/echo "VERIFY_PUBLIC_SCHEMA_RELEASE_OK=True"
SH

/bin/chmod +x "${VERIFY_SCRIPT}"
/bin/bash "${VERIFY_SCRIPT}" > "${BACKUP_DIR}/release_check.txt"

{
  /bin/echo "# External Auth Smoke"
  /bin/echo
  /bin/echo "Updated: ${STAMP}"
  /bin/echo
  /bin/echo "- Base URL: ${BASE_URL}"
  /bin/echo "- Route used: ${ROUTE}"
  /bin/echo "- No Bearer code: ${NO_CODE}"
  /bin/echo "- Invalid Bearer code: ${BAD_CODE}"
  /bin/echo "- Valid Bearer code: ${OK_CODE}"
  /bin/echo "- Release check script: ${VERIFY_SCRIPT}"
  /bin/echo "- Release check result: VERIFY_PUBLIC_SCHEMA_RELEASE_OK=True"
  /bin/echo "- Backup dir: ${BACKUP_DIR}"
} > "${REPORT}"

{
  /bin/echo
  /bin/echo "## External Auth Smoke ${STAMP}"
  /bin/echo "- Port 8010 boundary verified."
  /bin/echo "- Route used: ${ROUTE}"
  /bin/echo "- No Bearer rejected: ${NO_CODE}"
  /bin/echo "- Invalid Bearer rejected: ${BAD_CODE}"
  /bin/echo "- Valid Bearer succeeded: ${OK_CODE}"
  /bin/echo "- Release check script created: ${VERIFY_SCRIPT}"
  /bin/echo "- Release check passed after auth test."
} >> "${STATUS}"

{
  /bin/echo
  /bin/echo "## Stable Restore Point ${STAMP}"
  /bin/echo "- External auth on 8010 verified."
  /bin/echo "- Working protected route: ${ROUTE}"
  /bin/echo "- No Bearer rejection code: ${NO_CODE}"
  /bin/echo "- Invalid Bearer rejection code: ${BAD_CODE}"
  /bin/echo "- Valid Bearer success code: ${OK_CODE}"
  /bin/echo "- Public schema release check script: ${VERIFY_SCRIPT}"
  /bin/echo "- Backup dir: ${BACKUP_DIR}"
} >> "${ROLLBACK}"

{
  /bin/echo "# Next Step"
  /bin/echo
  /bin/echo "Updated: ${STAMP}"
  /bin/echo
  /bin/echo "## Immediate Next Step"
  /bin/echo "- External auth verification baseline is complete."
  /bin/echo "- Run ${VERIFY_SCRIPT} before any public schema release."
  /bin/echo "- Keep 8010 protected by Bearer auth."
  /bin/echo "- Preserve AUTHORIZED_TRIGGER-only public wording."
  /bin/echo
  /bin/echo "## Current Stable Result"
  /bin/echo "- No Bearer rejected with ${NO_CODE}."
  /bin/echo "- Invalid Bearer rejected with ${BAD_CODE}."
  /bin/echo "- Valid Bearer succeeded with ${OK_CODE}."
  /bin/echo "- Release check passed."
} > "${NEXT}"

/bin/echo "REPORT=${REPORT}"
/bin/echo "BACKUP_DIR=${BACKUP_DIR}"
/bin/echo "ROUTE=${ROUTE}"
/bin/echo "NO_BEARER_CODE=${NO_CODE}"
/bin/echo "INVALID_BEARER_CODE=${BAD_CODE}"
/bin/echo "VALID_BEARER_CODE=${OK_CODE}"
/bin/echo "VERIFY_SCRIPT=${VERIFY_SCRIPT}"
/bin/echo "RESULT=OK"
