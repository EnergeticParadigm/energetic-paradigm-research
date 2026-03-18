#!/usr/bin/env python3
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:8010"
ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system")
REGISTRY = ROOT / "client_registry.json"
ROLLBACK = ROOT / "work_memory" / "rollback.md"
REPORT = ROOT / ("external_auth_verify_report_" + time.strftime("%Y%m%d_%H%M%S") + ".json")

ENV_FILES = [
    ROOT / ".env",
    ROOT / ".env.local",
    ROOT / "auth.env",
    ROOT / "server.env",
    Path("/Users/wesleyshu/ep_system/.env"),
]

ENV_VARS = [
    "EP_BEARER_TOKEN",
    "BEARER_TOKEN",
    "AUTH_TOKEN",
    "API_TOKEN",
    "EP_TOKEN",
    "ACCESS_TOKEN",
]

def mask_token(token):
    if not token:
        return ""
    if len(token) <= 8:
        return token[:2] + "..." + token[-2:]
    return token[:4] + "..." + token[-4:]

def add_candidate(candidates, token, source):
    if not isinstance(token, str):
        return
    value = token.strip()
    if not value:
        return
    if len(value) < 8:
        return
    if value.startswith("{") or value.startswith("["):
        return
    candidates.append({"token": value, "source": source})

def walk_json(obj, prefix, candidates):
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            key_lower = key_text.lower()
            next_prefix = prefix + "." + key_text if prefix else key_text
            if isinstance(value, str) and any(word in key_lower for word in ["token", "bearer", "auth", "secret", "api_key", "apikey", "access"]):
                add_candidate(candidates, value, next_prefix)
            walk_json(value, next_prefix, candidates)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            walk_json(value, prefix + "[" + str(idx) + "]", candidates)
    elif isinstance(obj, str):
        if re.fullmatch(r"[A-Za-z0-9._~+/=-]{16,}", obj.strip()):
            add_candidate(candidates, obj, prefix)

def parse_env_file(path, candidates):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return
    for line in text.splitlines():
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", line)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2).strip().strip("\"")
        if any(word in key.lower() for word in ["token", "bearer", "auth", "secret", "api_key", "apikey", "access"]):
            add_candidate(candidates, value, str(path) + ":" + key)

def load_candidates():
    candidates = []
    for name in ENV_VARS:
        add_candidate(candidates, os.environ.get(name, ""), "env:" + name)
    for env_path in ENV_FILES:
        if env_path.is_file():
            parse_env_file(env_path, candidates)
    if REGISTRY.is_file():
        try:
            data = json.loads(REGISTRY.read_text(encoding="utf-8"))
            walk_json(data, "client_registry", candidates)
        except Exception as exc:
            print("REGISTRY_PARSE_WARNING=" + repr(exc))
    seen = set()
    unique = []
    for item in candidates:
        token = item["token"]
        if token in seen:
            continue
        seen.add(token)
        unique.append(item)
    return unique

def http_request(method, path, token=None, payload=None):
    url = BASE + path
    headers = {}
    body = None
    if token:
        headers["Authorization"] = "Bearer " + token
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            return {"status": resp.status, "body": data[:1200]}
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8", errors="replace")
        return {"status": exc.code, "body": data[:1200]}
    except Exception as exc:
        return {"status": None, "body": repr(exc)}

def find_working_token(candidates):
    for item in candidates:
        probe = http_request("GET", "/v1/ep/health", token=item["token"])
        if probe["status"] == 200:
            return item, probe
    return None, None

def append_rollback(report):
    try:
        existing = ""
        if ROLLBACK.is_file():
            existing = ROLLBACK.read_text(encoding="utf-8", errors="ignore")
        block = []
        block.append("")
        block.append("## External Auth Stable Baseline")
        block.append("")
        block.append("- Updated: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        block.append("- Base: " + BASE)
        block.append("- Result: " + report["result"])
        block.append("- No token health status: " + str(report["tests"]["no_token_health"]["status"]))
        block.append("- Invalid token health status: " + str(report["tests"]["invalid_token_health"]["status"]))
        block.append("- Valid token health status: " + str(report["tests"]["valid_token_health"]["status"]))
        block.append("- Valid token respond status: " + str(report["tests"]["valid_token_respond"]["status"]))
        block.append("- Working token source: " + report["working_token"]["source"])
        block.append("- Working token masked: " + report["working_token"]["masked"])
        block.append("- Report: " + str(REPORT))
        text = existing.rstrip() + "\n" + "\n".join(block) + "\n"
        ROLLBACK.write_text(text, encoding="utf-8")
        return True
    except Exception as exc:
        print("ROLLBACK_UPDATE_WARNING=" + repr(exc))
        return False

def main():
    candidates = load_candidates()

    report = {
        "base": BASE,
        "registry": str(REGISTRY),
        "candidate_count": len(candidates),
        "candidate_sources": [item["source"] for item in candidates],
        "tests": {}
    }

    report["tests"]["no_token_health"] = http_request("GET", "/v1/ep/health")
    report["tests"]["invalid_token_health"] = http_request("GET", "/v1/ep/health", token="invalid-token-for-boundary-test")

    working, working_probe = find_working_token(candidates)

    if working is None:
        report["result"] = "NO_WORKING_TOKEN_FOUND"
        report["working_token"] = None
        report["working_probe"] = working_probe
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("RESULT=NO_WORKING_TOKEN_FOUND")
        print("CANDIDATES=" + str(len(candidates)))
        for item in candidates[:20]:
            print("CANDIDATE_SOURCE=" + item["source"] + " TOKEN=" + mask_token(item["token"]))
        print("NO_TOKEN_STATUS=" + str(report["tests"]["no_token_health"]["status"]))
        print("INVALID_TOKEN_STATUS=" + str(report["tests"]["invalid_token_health"]["status"]))
        print("REPORT=" + str(REPORT))
        sys.exit(2)

    report["working_token"] = {
        "source": working["source"],
        "masked": mask_token(working["token"])
    }
    report["tests"]["valid_token_health"] = working_probe
    report["tests"]["valid_token_respond"] = http_request(
        "POST",
        "/v1/ep/respond",
        token=working["token"],
        payload={"input": {"text": "External auth boundary verification."}}
    )

    no_token_ok = report["tests"]["no_token_health"]["status"] in [401, 403]
    invalid_token_ok = report["tests"]["invalid_token_health"]["status"] in [401, 403]
    valid_health_ok = report["tests"]["valid_token_health"]["status"] == 200
    valid_respond_ok = report["tests"]["valid_token_respond"]["status"] not in [401, 403, None]

    report["result"] = "PASS" if all([no_token_ok, invalid_token_ok, valid_health_ok, valid_respond_ok]) else "FAIL"
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if report["result"] == "PASS":
        append_rollback(report)

    print("RESULT=" + report["result"])
    print("WORKING_TOKEN_SOURCE=" + report["working_token"]["source"])
    print("WORKING_TOKEN_MASKED=" + report["working_token"]["masked"])
    print("NO_TOKEN_STATUS=" + str(report["tests"]["no_token_health"]["status"]))
    print("INVALID_TOKEN_STATUS=" + str(report["tests"]["invalid_token_health"]["status"]))
    print("VALID_HEALTH_STATUS=" + str(report["tests"]["valid_token_health"]["status"]))
    print("VALID_RESPOND_STATUS=" + str(report["tests"]["valid_token_respond"]["status"]))
    print("REPORT=" + str(REPORT))
    sys.exit(0 if report["result"] == "PASS" else 1)

if __name__ == "__main__":
    main()
