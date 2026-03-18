from pathlib import Path
import re
import shutil
import subprocess
import time
import json

ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
APP = ROOT / "app.py"
WM = ROOT / "work_memory"
LOG = WM / "uvicorn_8010_restart.log"
TS = time.strftime("%Y%m%d_%H%M%S")
BACKUP = Path(str(APP) + f".respond_routing_backup_{TS}")

if not APP.exists():
    raise SystemExit(f"APP_NOT_FOUND={APP}")

shutil.copy2(APP, BACKUP)
text = APP.read_text(encoding="utf-8")

import_line = "from core.listening_engine import build_listening_profile\n"
if import_line not in text:
    m = re.search(r"^(from fastapi import .*|import fastapi.*)$", text, flags=re.MULTILINE)
    if m:
        text = text[:m.end()+1] + import_line + text[m.end()+1:]
    else:
        text = import_line + text

marker1 = '@app.post("/v1/ep/respond")'
marker2 = "@app.post('/v1/ep/respond')"
start = text.find(marker1)
if start == -1:
    start = text.find(marker2)
if start == -1:
    raise SystemExit("RESPOND_HANDLER_NOT_FOUND")

func_start = text.find("\n", start) + 1
next_deco = text.find("\n@app.", func_start)
if next_deco == -1:
    next_deco = len(text)

block = text[func_start:next_deco]

if "listening_profile = build_listening_profile(" not in block:
    lines = block.splitlines()
    if not lines:
        raise SystemExit("EMPTY_RESPOND_BLOCK")

    def_line = lines[0]
    body_lines = lines[1:]

    injection = [
        "    raw_text = \"\"",
        "    if isinstance(payload, dict):",
        "        raw_text = str(payload.get(\"text\", \"\"))",
        "",
        "    listening_profile = build_listening_profile(",
        "        raw_text=raw_text,",
        "        client_fp=\"external_ep_api_client\",",
        "        authorized=True,",
        "        source=\"ep_api_respond\",",
        "    )",
        "",
        "    route_mode = listening_profile.get(\"routing\", {}).get(\"mode\", \"direct_answer\")",
        "",
        "    if route_mode == \"clarify_or_narrow\":",
        "        return {",
        "            \"ok\": True,",
        "            \"routing_mode\": route_mode,",
        "            \"listening_profile\": listening_profile,",
        "            \"response\": {",
        "                \"type\": \"clarification\",",
        "                \"text\": \"Request recognized, but it is still too broad or ambiguous. Narrow the task before execution.\"",
        "            }",
        "        }",
        "",
        "    if route_mode == \"admin_tooling\":",
        "        return {",
        "            \"ok\": True,",
        "            \"routing_mode\": route_mode,",
        "            \"listening_profile\": listening_profile,",
        "            \"response\": {",
        "                \"type\": \"admin_tooling\",",
        "                \"text\": \"Request routed to admin_tooling. Live tool execution path is the next integration step.\"",
        "            }",
        "        }",
        "",
        "    if route_mode == \"writing_mode\":",
        "        return {",
        "            \"ok\": True,",
        "            \"routing_mode\": route_mode,",
        "            \"listening_profile\": listening_profile,",
        "            \"response\": {",
        "                \"type\": \"writing_mode\",",
        "                \"text\": \"Request routed to writing_mode. Writing pipeline binding is the next integration step.\"",
        "            }",
        "        }",
        "",
        "    if route_mode == \"structured_answer\":",
        "        return {",
        "            \"ok\": True,",
        "            \"routing_mode\": route_mode,",
        "            \"listening_profile\": listening_profile,",
        "            \"response\": {",
        "                \"type\": \"structured_answer\",",
        "                \"text\": raw_text",
        "            }",
        "        }",
        "",
    ]

    new_block = def_line + "\n" + "\n".join(injection) + "\n" + "\n".join(body_lines)
    text = text[:func_start] + new_block + text[next_deco:]

APP.write_text(text, encoding="utf-8")
print(f"RESPOND_PATCHED={APP}")
print(f"RESPOND_BACKUP={BACKUP}")

subprocess.run(
    ["/usr/bin/pkill", "-f", "uvicorn app:app --host 127.0.0.1 --port 8010 --app-dir /Users/wesleyshu/ep_system/ep_api_system"],
    check=False
)

with LOG.open("wb") as f:
    subprocess.Popen(
        ["/usr/bin/python3", "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8010", "--app-dir", "/Users/wesleyshu/ep_system/ep_api_system"],
        stdout=f,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT),
    )

time.sleep(5)

registry = json.loads((ROOT / "client_registry.json").read_text(encoding="utf-8"))
token = registry["external_boundary_bearer_token"]

tests = [
    ("EP ROUTE", {"text": "ep/trigger1 what is ep"}),
    ("LEGAL ROUTE", {"text": "Can this contract clause be enforced under Taiwan law?"}),
    ("AMBIGUOUS SYSTEM ROUTE", {"text": "something about system"}),
]

for label, payload in tests:
    print(f"=== TEST: {label} ===")
    result = subprocess.run(
        [
            "/usr/bin/curl", "-sS", "-X", "POST", "http://127.0.0.1:8010/v1/ep/respond",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "--data", json.dumps(payload),
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())

print(f"LOG={LOG}")
