#!/bin/bash
set -euo pipefail
/usr/bin/pkill -f "/Users/wesleyshu/ep_system/ep_api_system/ep_verified_ui_3000/server.py" || true
/bin/rm -f /private/tmp/ep_verified_ui_3000.pid
echo "STOPPED=YES"
