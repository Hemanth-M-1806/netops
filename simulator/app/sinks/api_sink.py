"""API sink: pushes telemetry to the collection layer."""

from __future__ import annotations

from typing import Protocol

from app.core.logging import get_logger
from app.domain.models import MetricPayload
from app.utils.chunking import chunked

logger = get_logger(__name__)


class TelemetryClient(Protocol):
    """Anything that can submit metric batches (e.g. ``CollectorClient``)."""

    async def ingest(self, payloads: list[MetricPayload]) -> dict:  # pragma: no cover
        ...

    async def close(self) -> None:  # pragma: no cover
        ...


class ApiSink:
    """Send telemetry batches to the collection layer's ingest endpoint."""

    def __init__(self, client: TelemetryClient, *, batch_size: int = 200) -> None:
        self._client = client
        self._batch_size = batch_size

    async def send(self, payloads: list[MetricPayload]) -> dict:
        if not payloads:
            return {"accepted": 0, "batches": 0}

        accepted = 0
        batches = 0
        for batch in chunked(payloads, self._batch_size):
            result = await self._client.ingest(batch)
            accepted += int(result.get("accepted", len(batch)))
            batches += 1

        logger.info("sink.api.sent", extra={"stage": "sink"})
        return {"accepted": accepted, "batches": batches}

    async def close(self) -> None:
        await self._client.close()

