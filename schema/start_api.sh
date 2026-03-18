#!/bin/bash
set -euo pipefail

BASE_DIR="/Users/wesleyshu/ep_system/ep_api_system"
VENV_DIR="/Users/wesleyshu/ep_system/ep_api_system/.venv"
APP_FILE="/Users/wesleyshu/ep_system/ep_api_system/app.py"
LOG_FILE="/Users/wesleyshu/ep_system/ep_api_system/server.log"
PID_FILE="/Users/wesleyshu/ep_system/ep_api_system/server.pid"
PORT="8010"

if [ ! -x "/Users/wesleyshu/ep_system/ep_api_system/.venv/bin/python" ]; then
  /usr/bin/python3 -m venv "/Users/wesleyshu/ep_system/ep_api_system/.venv"
  "/Users/wesleyshu/ep_system/ep_api_system/.venv/bin/pip" install --upgrade pip
  "/Users/wesleyshu/ep_system/ep_api_system/.venv/bin/pip" install -r "/Users/wesleyshu/ep_system/ep_api_system/requirements.txt"
fi

if [ -f "${PID_FILE}" ]; then
  OLD_PID="$(cat "${PID_FILE}" || true)"
  if [ -n "${OLD_PID}" ] && ps -p "${OLD_PID}" > /dev/null 2>&1; then
    kill "${OLD_PID}" || true
    sleep 1
  fi
fi

RUNNING_PID="$(lsof -ti tcp:${PORT} || true)"
if [ -n "${RUNNING_PID}" ]; then
  kill ${RUNNING_PID} || true
  sleep 1
fi

nohup "/Users/wesleyshu/ep_system/ep_api_system/.venv/bin/python" -m uvicorn app:app \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --app-dir "/Users/wesleyshu/ep_system/ep_api_system" \
  > "${LOG_FILE}" 2>&1 &

echo $! > "${PID_FILE}"
sleep 2
/usr/bin/curl -s "http://127.0.0.1:${PORT}/v1/ep/health"
echo
