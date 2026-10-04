"""Standard response-envelope helper.

Both the backend (FastAPI) and the collection layer reply with the envelope
``{ "success": bool, "data": ..., "meta": ..., "error": { ... } }``.
``unwrap`` turns that into the useful payload, or raises ``IngestError``.
"""

from __future__ import annotations

from typing import Any

from app.core.errors import IngestError


def unwrap(body: Any) -> Any:
    """Return the ``data`` of an envelope, raising on ``success: false``."""
    if isinstance(body, dict):
        if body.get("success") is False:
            error = body.get("error") or {}
            raise IngestError(str(error.get("message", "server returned an error")))
        if "data" in body:
            return body["data"]
    return body
