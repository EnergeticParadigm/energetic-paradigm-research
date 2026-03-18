#!/bin/bash
set -euo pipefail

ROOT="/Users/wesleyshu/ep_system/ep_api_system"
CTX="/Users/wesleyshu/ep_system/ep_api_system/runtime_arch_context.txt"
REQ="/Users/wesleyshu/ep_system/ep_api_system/runtime_arch_request.json"

{
  echo "PROJECT_ROOT=$ROOT"
  echo
  echo "=== FILE TREE depth 3 ==="
  /usr/bin/find "$ROOT" -maxdepth 3 \
    -not -path "$ROOT/.venv*" \
    -not -path "$ROOT/.git*" \
    -not -path "$ROOT/__pycache__*" \
    -not -name "*.pyc" \
    | /usr/bin/sort
  echo

  for f in \
    "$ROOT/app.py" \
    "$ROOT/main.py" \
    "$ROOT/requirements.txt" \
    "$ROOT/launch_ep_api.sh" \
    "$ROOT/start_api.sh" \
    "$ROOT/sample_request.json" \
    "$ROOT/sample_request_en.json"
  do
    if [ -f "$f" ]; then
      echo "=== FILE: $f ==="
      /usr/bin/sed -n '1,260p' "$f"
      echo
    fi
  done

  for d in \
    "$ROOT/schemas" \
    "$ROOT/routing" \
    "$ROOT/adapters" \
    "$ROOT/services" \
    "$ROOT/security" \
    "$ROOT/prompts"
  do
    if [ -d "$d" ]; then
      echo "=== DIRECTORY SNAPSHOT: $d ==="
      /usr/bin/find "$d" -maxdepth 2 -type f \
        -not -name "*.pyc" \
        | /usr/bin/sort \
        | while read -r file; do
            echo "--- BEGIN $file ---"
            /usr/bin/sed -n '1,260p' "$file"
            echo "--- END $file ---"
            echo
          done
    fi
  done

  echo "=== OPENAPI JSON ==="
  /usr/bin/curl -s http://127.0.0.1:8010/openapi.json || true
  echo
} > "$CTX"

REQ_JSON=$(/usr/bin/python3 - <<'PY'
import json
from pathlib import Path

ctx = Path("/Users/wesleyshu/ep_system/ep_api_system/runtime_arch_context.txt").read_text(encoding="utf-8", errors="ignore")

prompt = (
    "Use the local EP API project context below and do not ask for more information. "
    "Explain exactly what this API currently does, identify each major layer, identify the real request path, "
    "the normalization path, the EP instruction-building path, the routing path, the provider adapter path, "
    "the response normalization path, and whether a provider-independent core already exists in implementation. "
    "Then draw one plain-text structure diagram based only on the visible code. "
    "Answer in English only. "
    "Be concrete and implementation-facing, not generic.\\n\\n"
    + ctx
)

payload = {
    "request_id": "req_runtime_arch_deep_0001",
    "client": {
        "client_id": "ep_partner_app_demo",
        "client_type": "partner_app",
        "session_id": "sess_runtime_arch_deep_123"
    },
    "user": {
        "user_id": "user_001",
        "locale": "en",
        "timezone": "Asia/Riyadh"
    },
    "input": {
        "text": prompt,
        "attachments": []
    },
    "ep": {
        "mode": "deep",
        "depth": "long",
        "domain": "general",
        "format": "structured",
        "safety_level": "standard"
    },
    "routing": {
        "preferred_provider": "auto",
        "allowed_providers": ["openai", "local"],
        "fallback_provider": "local",
        "allow_fallback": True
    },
    "output": {
        "response_type": "final_answer",
        "max_tokens": 2200,
        "temperature": 0.1,
        "include_citations": False,
        "include_trace": True,
        "language": "en"
    },
    "metadata": {
        "source": "terminal",
        "tags": ["ep", "api-test", "architecture", "deep"]
    }
}

print(json.dumps(payload, ensure_ascii=False))
PY
)

printf "%s" "$REQ_JSON" > "$REQ"

/usr/bin/curl -s -X POST http://127.0.0.1:8010/v1/ep/respond \
  -H "Content-Type: application/json" \
  --data @"$REQ" \
| /usr/bin/python3 -c 'import sys, json; d=json.load(sys.stdin); print("status =", d.get("status")); print(); print(d["result"]["content"])'
