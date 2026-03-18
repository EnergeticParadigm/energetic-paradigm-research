#!/usr/bin/env python3
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
APP = ROOT / "app.py"
REG = ROOT / "client_registry.json"
OUT = ROOT / ("discover_8010_bearer_report_" + time.strftime("%Y%m%d_%H%M%S") + ".json")
BASE = "http://127.0.0.1:8010"

def mask(s):
    if not s:
        return ""
    if len(s) <= 8:
        return s[:2] + "..." + s[-2:]
    return s[:4] + "..." + s[-4:]

def req(method, path, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(BASE + path, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"status": resp.status, "body": body[:800]}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"status": exc.code, "body": body[:800]}
    except Exception as exc:
        return {"status": None, "body": repr(exc)}

def collect_strings(obj, prefix="root"):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.extend(collect_strings(v, prefix + "." + str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(collect_strings(v, prefix + "[" + str(i) + "]"))
    elif isinstance(obj, str):
        s = obj.strip()
        if s:
            found.append({"path": prefix, "value": s})
    return found

def auth_snippet(text):
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        low = line.lower()
        if "authorization" in low or "bearer" in low or "load_client_registry" in low or "require_client_auth" in low:
            start = max(0, i - 6)
            end = min(len(lines), i + 18)
            block = []
            for j in range(start, end):
                block.append(f"{j+1}: {lines[j]}")
            hits.append("\n".join(block))
    uniq = []
    seen = set()
    for h in hits:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq[:6]

if not APP.is_file():
    raise SystemExit("APP_NOT_FOUND=" + str(APP))
if not REG.is_file():
    raise SystemExit("REGISTRY_NOT_FOUND=" + str(REG))

app_text = APP.read_text(encoding="utf-8", errors="ignore")
registry = json.loads(REG.read_text(encoding="utf-8"))

all_strings = collect_strings(registry)
dedup = []
seen = set()
for item in all_strings:
    v = item["value"]
    if v not in seen:
        seen.add(v)
        dedup.append(item)

baseline_no = req("GET", "/v1/ep/health")
baseline_bad = req("GET", "/v1/ep/health", token="INVALID_BOUNDARY_TEST_TOKEN")

tested = []
working = None

for item in dedup:
    token = item["value"]
    result = req("GET", "/v1/ep/health", token=token)
    tested.append({
        "path": item["path"],
        "masked": mask(token),
        "length": len(token),
        "status": result["status"],
        "body": result["body"],
    })
    if result["status"] == 200:
        working = {
            "path": item["path"],
            "masked": mask(token),
            "length": len(token),
            "health_status": result["status"],
            "health_body": result["body"],
        }
        respond = None
        try:
            payload = json.dumps({"input": {"text": "External auth boundary verification."}}).encode("utf-8")
            headers = {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            }
            r = urllib.request.Request(BASE + "/v1/ep/respond", data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(r, timeout=20) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                respond = {"status": resp.status, "body": body[:800]}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            respond = {"status": exc.code, "body": body[:800]}
        except Exception as exc:
            respond = {"status": None, "body": repr(exc)}
        working["respond_status"] = respond["status"]
        working["respond_body"] = respond["body"]
        break

report = {
    "base": BASE,
    "app": str(APP),
    "registry": str(REG),
    "baseline_no_token": baseline_no,
    "baseline_invalid_token": baseline_bad,
    "auth_snippets": auth_snippet(app_text),
    "registry_string_count": len(dedup),
    "working_token": working,
    "tested_candidates_first_80": tested[:80],
}

OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("APP=" + str(APP))
print("REGISTRY=" + str(REG))
print("NO_TOKEN_STATUS=" + str(baseline_no["status"]))
print("INVALID_TOKEN_STATUS=" + str(baseline_bad["status"]))
print("REGISTRY_STRING_COUNT=" + str(len(dedup)))
if working:
    print("WORKING_TOKEN_PATH=" + working["path"])
    print("WORKING_TOKEN_MASKED=" + working["masked"])
    print("WORKING_HEALTH_STATUS=" + str(working["health_status"]))
    print("WORKING_RESPOND_STATUS=" + str(working["respond_status"]))
else:
    print("WORKING_TOKEN_PATH=")
    print("WORKING_TOKEN_MASKED=")
    print("WORKING_HEALTH_STATUS=")
    print("WORKING_RESPOND_STATUS=")
print("REPORT=" + str(OUT))
