
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ep_api_openclaw.auth import verify_openclaw_request
from ep_api_openclaw.ep_engine_adapter import run_compare, run_query
from ep_api_openclaw.models import CompareRequest, EPResult, QueryRequest

router = APIRouter()


def model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Unsupported model type: {type(model).__name__}")


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/ep/query")
async def ep_query(
    payload: QueryRequest,
    auth_context: Dict[str, Any] = Depends(verify_openclaw_request),
) -> Dict[str, Any]:
    try:
        result = await run_query(model_to_dict(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"EP query failed: {exc}") from exc

    response_model = EPResult(
        ok=True,
        answer=str(result.get("answer", "")),
        mode=str(result.get("mode", payload.mode)),
        session_id=payload.session_id,
        user_ref=payload.user_ref,
        metadata={
            **payload.metadata,
            "auth_client_id": auth_context["client_id"],
            **result.get("metadata", {}),
        },
    )
    return model_to_dict(response_model)


@router.post("/ep/compare")
async def ep_compare(
    payload: CompareRequest,
    auth_context: Dict[str, Any] = Depends(verify_openclaw_request),
) -> Dict[str, Any]:
    try:
        result = await run_compare(model_to_dict(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"EP compare failed: {exc}") from exc

    return {
        "ok": True,
        "question": str(result.get("question", payload.question)),
        "results": result.get("results", []),
        "output_format": str(result.get("output_format", payload.output_format)),
        "session_id": payload.session_id,
        "user_ref": payload.user_ref,
        "metadata": {
            **payload.metadata,
            "auth_client_id": auth_context["client_id"],
            **result.get("metadata", {}),
        },
    }
