"""CollectorService — the central stateful object.

It owns the active sources and forwarder.  Sources call `receive()` to hand
batches of validated samples in; the service forwards them immediately.

Lifecycle
---------
`start()`   → call once when the FastAPI app starts (lifespan).
`receive()` → called by every source (push route, SNMP poller, …).
`stop()`    → call once on shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import time

from app.core.errors import ForwardError
from app.forwarders.base import BaseForwarder
from app.models import IngestRequest, SampleRecord
from app.sources.base import BaseSource

logger = logging.getLogger(__name__)


class CollectorService:
    """Wires sources to the forwarder and keeps running counters."""

    def __init__(
        self,
        sources: list[BaseSource],
        forwarder: BaseForwarder,
    ) -> None:
        self._sources = sources
        self._forwarder = forwarder
        self._started_at: float = 0.0

        # Counters (reset on each start).
        self.received: int = 0
        self.accepted: int = 0
        self.failures: int = 0

    # -------------------------------------------------------------------------
    async def start(self) -> None:
        self._started_at = time.monotonic()
        for source in self._sources:
            await source.start(self)
        logger.info(
            "service.started",
            extra={
                "stage": "service",
                "sources": [s.name for s in self._sources],
                "forwarder": self._forwarder.name,
            },
        )

    async def stop(self) -> None:
        for source in self._sources:
            await source.stop()
        await self._forwarder.close()
        logger.info("service.stopped", extra={"stage": "service"})

    # -------------------------------------------------------------------------
    async def receive(self, request: IngestRequest) -> dict:
        """Accept an `IngestRequest` from any source and forward it.

        Returns the forwarder result dict (`{"accepted": N, ...}`).
        """
        samples: list[SampleRecord] = request.samples
        self.received += len(samples)

        if not samples:
            return {"accepted": 0}

        logger.info(
            "service.receive",
            extra={
                "stage": "service",
                "source": request.source,
                "batch_size": len(samples),
            },
        )

        try:
            result = await self._forwarder.send(samples)
            self.accepted += result.get("accepted", 0)
            return result
        except ForwardError as exc:
            self.failures += 1
            logger.error(
                "service.forward_error",
                extra={"stage": "service", "error": str(exc)},
            )
            raise

    # -------------------------------------------------------------------------
    @property
    def uptime_seconds(self) -> float:
        if self._started_at == 0.0:
            return 0.0
        return time.monotonic() - self._started_at

    @property
    def source_names(self) -> list[str]:
        return [s.name for s in self._sources]
