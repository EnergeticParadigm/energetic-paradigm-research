#!/bin/bash
set -euo pipefail

cd /

export PYTHONPATH="/Users/wesleyshu/ep_system/ep_api_system/.deps_ep_api_openclaw:/Users/wesleyshu/ep_system/ep_api_system:/Users/wesleyshu/ep_system"
export EP_OPENCLAW_APP_NAME="EP OpenClaw Bridge"
export EP_OPENCLAW_API_PREFIX="/v1"
export EP_OPENCLAW_HMAC_CLIENT_ID="openclaw-prod"
export EP_OPENCLAW_HMAC_SECRET="CHANGE_ME"
export EP_OPENCLAW_ALLOWED_CLOCK_SKEW_SECONDS="300"
export EP_OPENCLAW_NONCE_TTL_SECONDS="600"
export EP_OPENCLAW_NONCE_DB_PATH="/Users/wesleyshu/ep_system/ep_api_system/ep_api_openclaw/nonces.sqlite3"
export EP_ENGINE_QUERY_HANDLER="ep_api_openclaw.real_ep_wrapper:real_query_handler"
export EP_ENGINE_COMPARE_HANDLER="ep_api_openclaw.example_engine_handlers:example_compare_handler"
export EP_REAL_AUTHORIZATION="${EP_REAL_AUTHORIZATION:-}"

exec "/usr/local/bin/python3" -m uvicorn   --app-dir "/Users/wesleyshu/ep_system/ep_api_system"   ep_api_openclaw.main:app   --host 0.0.0.0   --port 8011
