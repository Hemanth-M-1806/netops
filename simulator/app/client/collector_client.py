"""HTTP client for the collection layer.

The simulator pushes telemetry **here** (the collection layer entry point) rather
than talking to the database-facing backend directly. That keeps the simulator a
pure *source*: in production the collection layer is fed by real collectors
(SNMP / gNMI) and the simulator is simply removed — only ``collector_url``
changes.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.client.envelope import unwrap
from app.client.retry import call_with_retry
from app.config import Settings
from app.core.errors import IngestError
from app.core.logging import get_logger
from app.domain.models import MetricPayload

logger = get_logger(__name__)


class CollectorClient:
    """Async client that submits metric batches to the collection layer."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # A full URL, e.g. http://localhost:8100/ingest
        self._ingest_url = settings.collector_url
        self._client = httpx.AsyncClient(timeout=settings.timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "CollectorClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def ingest(self, payloads: list[MetricPayload]) -> dict:
        """POST a batch of samples to the collection layer."""
        if not payloads:
            return {"accepted": 0}

        body = {
            "source": "simulator",
            "samples": [p.as_ingest_body() for p in payloads],
        }

        async def _do() -> Any:
            response = await self._client.post(self._ingest_url, json=body)
            response.raise_for_status()
            return response.json()

        try:
            response = await call_with_retry(
                _do,
                attempts=self._settings.max_retries,
                backoff_seconds=self._settings.retry_backoff_seconds,
            )
        except httpx.HTTPStatusError as exc:
            snippet = exc.response.text[:200]
            raise IngestError(
                f"collector rejected: HTTP {exc.response.status_code} {snippet}",
                status_code=exc.response.status_code,
            ) from exc

        data = unwrap(response)
        return data if isinstance(data, dict) else {"raw": data}
