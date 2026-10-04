"""POST /ingest — the push source HTTP endpoint.

The simulator (and any other push client) sends:

    POST http://localhost:8100/ingest
    Content-Type: application/json

    {
        "source": "simulator",
        "samples": [
            {
                "interface_id": 42,
                "rx_bytes": 12345678,
                "tx_bytes": 8765432,
                "packet_drops": 0,
                "errors": 0,
                "measured_at": "2026-10-04T07:30:00+00:00"
            },
            ...
        ]
    }

The route validates the body with Pydantic (`IngestRequest`), hands it to the
`CollectorService`, and returns:

    { "success": true, "data": { "accepted": N } }

Authentication
--------------
If `COLLECTOR_API_KEY` is set, the request must carry:
    X-Collector-Key: <key>
Leave the env var empty (the default) to disable auth for local dev.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.models import IngestRequest, IngestResponse
from app.service import CollectorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ingest"])


def _get_service(request: Request) -> CollectorService:
    return request.app.state.service


def _check_api_key(
    request: Request,
    x_collector_key: str | None = Header(default=None),
) -> None:
    """Optional shared-secret guard.  No-op when api_key is empty."""
    expected = request.app.state.settings.api_key
    if expected and x_collector_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Accept a batch of telemetry samples",
    description=(
        "Accepts samples from any push source (simulator, sidecar, etc.) "
        "and forwards them to the configured backend."
    ),
)
async def ingest(
    body: IngestRequest,
    _auth: None = Depends(_check_api_key),
    service: CollectorService = Depends(_get_service),
) -> IngestResponse:
    result = await service.receive(body)
    return IngestResponse(success=True, data=result)
