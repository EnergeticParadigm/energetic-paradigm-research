#!/bin/bash
set -euo pipefail

APP_ROOT="/Users/wesleyshu/ep_system/ep_api_system"
PY="$APP_ROOT/.venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "ERROR: missing virtualenv python at $PY"
  exit 1
fi

if [ -f "$APP_ROOT/app.py" ]; then
  exec "$PY" -m uvicorn app:app \
    --app-dir "$APP_ROOT" \
    --reload-dir "$APP_ROOT" \
    --host 127.0.0.1 \
    --port 8010 \
    --reload
elif [ -f "$APP_ROOT/main.py" ]; then
  exec "$PY" -m uvicorn main:app \
    --app-dir "$APP_ROOT" \
    --reload-dir "$APP_ROOT" \
    --host 127.0.0.1 \
    --port 8010 \
    --reload
else
  echo "ERROR: no app.py or main.py found under $APP_ROOT"
  exit 1
fi
