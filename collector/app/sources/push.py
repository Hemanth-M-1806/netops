"""Push source — accepts telemetry via HTTP POST.

This is the source used when the **simulator** is running.  In production you
would disable this source and enable a polling source (SNMP / gNMI) instead.

The push source does not create any background tasks.  It marks itself as
active so the `/health` endpoint can report it, and exposes the route
`POST /ingest` through the main FastAPI app (registered in `routes/ingest`).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.sources.base import BaseSource

if TYPE_CHECKING:
    from app.service import CollectorService

logger = logging.getLogger(__name__)


class PushSource(BaseSource):
    """Telemetry pushed by an external agent (simulator, sidecar, etc.)."""

    name = "push"

    async def start(self, service: "CollectorService") -> None:
        # Nothing to set up — the HTTP route is registered separately by the
        # FastAPI router.  We just log our presence.
        logger.info("source.push.ready", extra={"stage": "source"})

    async def stop(self) -> None:
        logger.info("source.push.stopped", extra={"stage": "source"})
