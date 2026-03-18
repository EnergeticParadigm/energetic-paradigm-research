
import hashlib
import json
from typing import Any


def canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def body_sha256_hex(data: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def build_signature_payload(method: str, path: str, timestamp: str, nonce: str, body_sha256: str) -> bytes:
    payload = "\n".join([
        method.upper().strip(),
        path.strip(),
        timestamp.strip(),
        nonce.strip(),
        body_sha256.strip(),
    ])
    return payload.encode("utf-8")
