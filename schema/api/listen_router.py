from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from core.listening_engine import build_listening_profile

router = APIRouter()


@router.post("/v1/ep/listen")
async def ep_listen(
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    raw_text = str(payload.get("text", ""))
    client_fp = str(payload.get("client_fp", "external_ep_client"))
    source = str(payload.get("source", "ep_api"))

    profile = build_listening_profile(
        raw_text=raw_text,
        client_fp=client_fp,
        authorized=True,
        source=source,
    )
    return {"listening_profile": profile}
