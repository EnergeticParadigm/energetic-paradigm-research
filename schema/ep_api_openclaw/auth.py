
import datetime as dt
import hashlib
import hmac
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, Request, status

from ep_api_openclaw.canonical import body_sha256_hex, build_signature_payload
from ep_api_openclaw.nonce_store import NonceStore
from ep_api_openclaw.settings import get_settings

_settings = get_settings()
_nonce_store = NonceStore(_settings.nonce_db_path, _settings.nonce_ttl_seconds)


def _parse_timestamp(value: str) -> dt.datetime:
    try:
        if value.endswith("Z"):
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid timestamp format") from exc


def _validate_time_window(timestamp: str) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    parsed_timestamp = _parse_timestamp(timestamp)
    delta_seconds = abs((now - parsed_timestamp).total_seconds())
    if delta_seconds > get_settings().allowed_clock_skew_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Timestamp outside allowed window")


def _validate_bearer(authorization: Optional[str]) -> None:
    expected_token = get_settings().bearer_token.strip()
    if not expected_token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    provided_token = authorization.split(" ", 1)[1].strip()
    if not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")


def _sign(secret: str, method: str, path: str, timestamp: str, nonce: str, body: Any) -> str:
    body_hash = body_sha256_hex(body)
    payload = build_signature_payload(method, path, timestamp, nonce, body_hash)
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


async def verify_openclaw_request(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    client_id: Optional[str] = Header(default=None, alias="X-EP-Client-ID"),
    timestamp: Optional[str] = Header(default=None, alias="X-EP-Timestamp"),
    nonce: Optional[str] = Header(default=None, alias="X-EP-Nonce"),
    signature: Optional[str] = Header(default=None, alias="X-EP-Signature"),
) -> Dict[str, Any]:
    settings = get_settings()

    if not client_id or not timestamp or not nonce or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication headers")

    if client_id != settings.hmac_client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client id")

    _validate_bearer(authorization)
    _validate_time_window(timestamp)

    try:
        body = await request.json()
    except Exception:
        body = {}

    expected_signature = _sign(settings.hmac_secret, request.method, request.url.path, timestamp, nonce, body)
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    if not _nonce_store.consume(nonce):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Replay detected")

    return {
        "client_id": client_id,
        "timestamp": timestamp,
        "nonce": nonce,
        "path": request.url.path,
    }
