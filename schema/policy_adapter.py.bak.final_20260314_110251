from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_FILE = Path("/Users/wesleyshu/ep_system/ep_api_system/config/routing_policy_v1.json").resolve()

_CONFIG_CACHE: Dict[str, Any] = {
    "mtime_ns": None,
    "data": None,
}


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _normalize_provider_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    if isinstance(value, tuple):
        return [str(v) for v in value if v is not None and str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}

    mtime_ns = CONFIG_FILE.stat().st_mtime_ns
    if _CONFIG_CACHE["mtime_ns"] == mtime_ns and isinstance(_CONFIG_CACHE["data"], dict):
        return _CONFIG_CACHE["data"]

    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    _CONFIG_CACHE["mtime_ns"] = mtime_ns
    _CONFIG_CACHE["data"] = data
    return data


def _make_context(req: Any) -> Dict[str, Any]:
    input_obj = _get_attr(req, "input", None)
    ep_obj = _get_attr(req, "ep", None)
    output_obj = _get_attr(req, "output", None)
    routing_obj = _get_attr(req, "routing", None)

    text = str(_get_attr(input_obj, "text", "") or "")
    return {
        "input_text": text.lower(),
        "ep_mode": _get_attr(ep_obj, "mode", None),
        "ep_depth": _get_attr(ep_obj, "depth", None),
        "ep_domain": _get_attr(ep_obj, "domain", None),
        "output_format": _get_attr(ep_obj, "format", None),
        "response_type": _get_attr(output_obj, "response_type", None),
        "requested_provider": _get_attr(routing_obj, "preferred_provider", None),
    }


def _match_condition(ctx: Dict[str, Any], node: Any) -> bool:
    if not isinstance(node, dict):
        return False

    if "all" in node:
        return all(_match_condition(ctx, child) for child in node["all"])

    if "any" in node:
        return any(_match_condition(ctx, child) for child in node["any"])

    if "input_contains_any" in node:
        phrases = [str(p).lower() for p in node["input_contains_any"]]
        return any(phrase in ctx["input_text"] for phrase in phrases)

    if "input_contains_all" in node:
        phrases = [str(p).lower() for p in node["input_contains_all"]]
        return all(phrase in ctx["input_text"] for phrase in phrases)

    if "ep_mode_in" in node:
        return ctx["ep_mode"] in node["ep_mode_in"]

    if "ep_depth_in" in node:
        return ctx["ep_depth"] in node["ep_depth_in"]

    if "ep_domain_in" in node:
        return ctx["ep_domain"] in node["ep_domain_in"]

    if "output_format_in" in node:
        return ctx["output_format"] in node["output_format_in"]

    if "response_type_in" in node:
        return ctx["response_type"] in node["response_type_in"]

    if "requested_provider_in" in node:
        return ctx["requested_provider"] in node["requested_provider_in"]

    return False


def _baseline_from_request(req: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    routing_obj = _get_attr(req, "routing", None)
    defaults = config.get("defaults", {}) if isinstance(config, dict) else {}

    request_allowed = _normalize_provider_list(_get_attr(routing_obj, "allowed_providers", None))
    default_allowed = _normalize_provider_list(defaults.get("allowed_providers", None))

    preferred_provider = _get_attr(routing_obj, "preferred_provider", None)
    if preferred_provider is None:
        preferred_provider = defaults.get("preferred_provider", "openai")

    allowed_providers = request_allowed or default_allowed or ["openai", "local"]

    fallback_provider = _get_attr(routing_obj, "fallback_provider", None)
    if fallback_provider is None:
        fallback_provider = defaults.get("fallback_provider", None)

    allow_fallback = _get_attr(routing_obj, "allow_fallback", None)
    if allow_fallback is None:
        allow_fallback = defaults.get("allow_fallback", True)

    return {
        "preferred_provider": preferred_provider,
        "allowed_providers": allowed_providers,
        "fallback_provider": fallback_provider,
        "allow_fallback": bool(allow_fallback),
    }


def apply_routing_policy(req: Any) -> Dict[str, Any]:
    config = _load_config()
    baseline = _baseline_from_request(req, config)

    if not config.get("policy_enabled", False):
        return {
            "policy_enabled": False,
            "matched_rule_id": None,
            "reason": None,
            **baseline,
        }

    ctx = _make_context(req)
    rules = config.get("pre_routing_rules", [])
    rules = sorted(rules, key=lambda rule: int(rule.get("priority", 0)), reverse=True)

    for rule in rules:
        when = rule.get("when", {})
        if _match_condition(ctx, when):
            select = rule.get("select", {})
            return {
                "policy_enabled": True,
                "matched_rule_id": rule.get("id"),
                "reason": rule.get("reason"),
                "preferred_provider": select.get("preferred_provider", baseline["preferred_provider"]),
                "allowed_providers": _normalize_provider_list(select.get("allowed_providers", baseline["allowed_providers"])) or baseline["allowed_providers"],
                "fallback_provider": select.get("fallback_provider", baseline["fallback_provider"]),
                "allow_fallback": bool(select.get("allow_fallback", baseline["allow_fallback"])),
            }

    return {
        "policy_enabled": True,
        "matched_rule_id": None,
        "reason": None,
        **baseline,
    }
