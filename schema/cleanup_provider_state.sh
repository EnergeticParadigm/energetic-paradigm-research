#!/bin/bash
set -euo pipefail

ROOT="/Users/wesleyshu/ep_system/ep_api_system"

PIDS=$(/usr/sbin/lsof -ti tcp:8010 || true)
if [ -n "$PIDS" ]; then
  /bin/kill -9 $PIDS || true
  /bin/sleep 1
fi

/usr/bin/nohup "$ROOT/launch_ep_api.sh" >/tmp/ep_api_launch.log 2>&1 &
/bin/sleep 5

echo "===== TEST OUTPUT ====="
"$ROOT/test_ep_api.sh"

echo
echo "===== RECENT LAUNCH LOG ====="
/usr/bin/tail -n 80 /tmp/ep_api_launch.log
