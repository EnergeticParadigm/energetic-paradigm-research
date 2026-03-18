
import importlib
import inspect
from typing import Any, Callable, Dict

import httpx

from ep_api_openclaw.settings import get_settings


def import_string(path: str) -> Callable[..., Any]:
    if not path or ":" not in path:
        raise ValueError(f"Invalid import path: {path!r}")
    module_name, attr_name = path.split(":", 1)
    module = importlib.import_module(module_name)
    handler = getattr(module, attr_name)
    if not callable(handler):
        raise TypeError(f"Imported object is not callable: {path!r}")
    return handler


async def _call_maybe_async(handler: Callable[..., Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    result = handler(payload)
    if inspect.isawaitable(result):
        result = await result
    if not isinstance(result, dict):
        raise TypeError(f"Handler must return dict, got {type(result).__name__}")
    return result


async def run_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    if settings.ep_engine_query_handler:
        handler = import_string(settings.ep_engine_query_handler)
        return await _call_maybe_async(handler, payload)
    if settings.ep_engine_base_url:
        async with httpx.AsyncClient(timeout=settings.ep_engine_timeout_seconds) as client:
            response = await client.post(settings.ep_engine_base_url.rstrip("/") + "/query", json=payload)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise TypeError("HTTP query backend must return JSON object")
            return data
    raise RuntimeError("No EP query backend configured")


async def run_compare(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    if settings.ep_engine_compare_handler:
        handler = import_string(settings.ep_engine_compare_handler)
        return await _call_maybe_async(handler, payload)
    if settings.ep_engine_base_url:
        async with httpx.AsyncClient(timeout=settings.ep_engine_timeout_seconds) as client:
            response = await client.post(settings.ep_engine_base_url.rstrip("/") + "/compare", json=payload)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise TypeError("HTTP compare backend must return JSON object")
            return data
    raise RuntimeError("No EP compare backend configured")
