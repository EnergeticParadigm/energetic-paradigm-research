import inspect
import os
import traceback
from typing import Any, Dict

from ep_gateway.app import run_ep

DEBUG_LOG = "/Users/wesleyshu/ep_system/ep_api_system/ep_api_openclaw/logs/real_ep_wrapper_debug.log"


def _extract_answer(result: Any) -> str:
    if result is None:
        return ""

    if isinstance(result, dict):
        for key in ("answer", "response", "text", "result", "output", "content", "message"):
            value = result.get(key)
            if value is not None:
                return str(value)
        return str(result)

    return str(result)


def _extract_authorization(metadata: Any) -> str:
    if isinstance(metadata, dict):
        for key in ("authorization", "access_key", "token", "auth"):
            value = metadata.get(key)
            if value:
                return str(value)

    env_value = os.getenv("EP_REAL_AUTHORIZATION", "")
    if env_value:
        return env_value

    return ""


def _append_debug(text: str) -> None:
    os.makedirs(os.path.dirname(DEBUG_LOG), exist_ok=True)
    with open(DEBUG_LOG, "a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


async def real_query_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = str(payload.get("question", ""))
    mode = str(payload.get("mode", "ep"))
    metadata = payload.get("metadata") or {}
    authorization = _extract_authorization(metadata)

    try:
        result = run_ep(query, authorization)
        if inspect.isawaitable(result):
            result = await result

        return {
            "answer": _extract_answer(result),
            "mode": mode,
            "metadata": {
                "handler": "ep_api_openclaw.real_ep_wrapper:real_query_handler",
                "source_callable": "ep_gateway.app:run_ep",
                "authorization_supplied": bool(authorization),
                "real_ok": True,
            },
        }
    except Exception as exc:
        _append_debug("=== REAL_EP_EXCEPTION ===")
        _append_debug(f"query={query}")
        _append_debug(f"authorization_supplied={bool(authorization)}")
        _append_debug("traceback:")
        _append_debug(traceback.format_exc())

        return {
            "answer": f"REAL_EP_ERROR: {exc.__class__.__name__}: {exc}",
            "mode": mode,
            "metadata": {
                "handler": "ep_api_openclaw.real_ep_wrapper:real_query_handler",
                "source_callable": "ep_gateway.app:run_ep",
                "authorization_supplied": bool(authorization),
                "real_ok": False,
                "debug_log": DEBUG_LOG,
            },
        }
