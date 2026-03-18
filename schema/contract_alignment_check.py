import json
import urllib.request
import urllib.error
from pathlib import Path

OUT = Path("/Users/wesleyshu/ep_system/ep_api_system/contract_alignment_report.json")

TESTS = [
    {
        "name": "respond_minimal_en",
        "url": "http://127.0.0.1:8010/v1/ep/respond",
        "payload": {
            "input": {
                "text": "Answer in English only. Keep the reply in English only."
            },
            "ep": {
                "mode": "auto",
                "depth": "auto",
                "domain": "general",
                "format": "structured",
                "safety_level": "standard"
            },
            "routing": {
                "preferred_provider": "openai",
                "allowed_providers": ["openai", "local"],
                "fallback_provider": "local",
                "allow_fallback": True
            },
            "output": {
                "response_type": "final_answer",
                "max_tokens": 800,
                "temperature": 0.2,
                "include_citations": False,
                "include_trace": False,
                "language": "en"
            },
            "metadata": {
                "source": "terminal",
                "tags": ["contract-check", "respond"]
            }
        }
    },
    {
        "name": "analyze_minimal_en",
        "url": "http://127.0.0.1:8010/v1/ep/analyze",
        "payload": {
            "input": {
                "text": "Answer in English only. Analyze this issue in English only."
            },
            "ep": {
                "mode": "auto",
                "depth": "auto",
                "domain": "general",
                "format": "structured",
                "safety_level": "standard"
            },
            "routing": {
                "preferred_provider": "openai",
                "allowed_providers": ["openai", "local"],
                "fallback_provider": "local",
                "allow_fallback": True
            },
            "output": {
                "response_type": "analysis",
                "max_tokens": 800,
                "temperature": 0.2,
                "include_citations": False,
                "include_trace": False,
                "language": "en"
            },
            "metadata": {
                "source": "terminal",
                "tags": ["contract-check", "analyze"]
            }
        }
    }
]

TOP = ["request_id", "status", "result", "ep", "provider", "usage", "timing", "warnings", "error"]
RESULT = ["response_type", "content", "language", "format"]
EP = ["mode_applied", "depth_applied", "domain_applied", "routing_path"]
PROVIDER = ["selected", "model", "fallback_used"]
USAGE = ["input_tokens", "output_tokens", "total_tokens", "estimated_cost"]
TIMING = ["started_at", "completed_at", "latency_ms"]

def missing(obj, required):
    if not isinstance(obj, dict):
        return [f"expected_object_got_{type(obj).__name__}"]
    return [k for k in required if k not in obj]

def has_non_ascii(text):
    return any(ord(ch) > 127 for ch in text)

report = {
    "alignment_passed": True,
    "tests": []
}

for test in TESTS:
    row = {
        "name": test["name"],
        "url": test["url"],
        "http_status": None,
        "passed": True,
        "problems": [],
        "response": None
    }
    try:
        req = urllib.request.Request(
            test["url"],
            data=json.dumps(test["payload"]).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode("utf-8")
            row["http_status"] = resp.status
            data = json.loads(body)
            row["response"] = data
    except urllib.error.HTTPError as exc:
        row["http_status"] = exc.code
        row["passed"] = False
        row["problems"].append(f"http_error_{exc.code}")
        try:
            row["response"] = json.loads(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            row["response"] = None
        report["alignment_passed"] = False
        report["tests"].append(row)
        continue
    except Exception as exc:
        row["passed"] = False
        row["problems"].append(f"request_failed_{exc}")
        report["alignment_passed"] = False
        report["tests"].append(row)
        continue

    if row["http_status"] != 200:
        row["passed"] = False
        row["problems"].append(f"expected_200_got_{row['http_status']}")

    top_missing = missing(data, TOP)
    if top_missing:
        row["passed"] = False
        row["problems"].append({"top_missing": top_missing})

    status = data.get("status")
    if status not in ("success", "error"):
        row["passed"] = False
        row["problems"].append(f"invalid_status_{status!r}")

    ep_missing = missing(data.get("ep"), EP)
    if ep_missing:
        row["passed"] = False
        row["problems"].append({"ep_missing": ep_missing})

    provider_missing = missing(data.get("provider"), PROVIDER)
    if provider_missing:
        row["passed"] = False
        row["problems"].append({"provider_missing": provider_missing})

    usage_missing = missing(data.get("usage"), USAGE)
    if usage_missing:
        row["passed"] = False
        row["problems"].append({"usage_missing": usage_missing})

    timing_missing = missing(data.get("timing"), TIMING)
    if timing_missing:
        row["passed"] = False
        row["problems"].append({"timing_missing": timing_missing})

    if not isinstance(data.get("warnings"), list):
        row["passed"] = False
        row["problems"].append("warnings_not_array")

    if status == "success":
        result_missing = missing(data.get("result"), RESULT)
        if result_missing:
            row["passed"] = False
            row["problems"].append({"result_missing": result_missing})

        result = data.get("result") or {}
        content = result.get("content", "")
        if (result.get("language") or "").lower() != "en":
            row["passed"] = False
            row["problems"].append(f"language_not_en_{result.get('language')!r}")
        if has_non_ascii(content):
            row["passed"] = False
            row["problems"].append("content_contains_non_ascii")
        if not isinstance(content, str) or not content.strip():
            row["passed"] = False
            row["problems"].append("empty_content")

    if not row["passed"]:
        report["alignment_passed"] = False

    report["tests"].append(row)

OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
