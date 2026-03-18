#!/bin/bash
set -euo pipefail
/usr/bin/pkill -f "/Users/wesleyshu/ep_system/ep_api_system/ep_verified_ui_3000/server.py" || true
nohup /usr/bin/python3 /Users/wesleyshu/ep_system/ep_api_system/ep_verified_ui_3000/server.py > /private/tmp/ep_verified_ui_3000.log 2>&1 &
echo $! > /private/tmp/ep_verified_ui_3000.pid
echo "UI_URL=http://127.0.0.1:3000/"
