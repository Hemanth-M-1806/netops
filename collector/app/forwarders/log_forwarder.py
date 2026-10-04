"""Log forwarder — dry-run destination.  Logs samples instead of posting them.

Use this when:
  * The backend is not running.
  * You want to validate the collection pipeline end-to-end without writes.
  * `COLLECTOR_FORWARDER=log` or `COLLECTOR_DRY_RUN=true` is set.
"""

from __future__ import annotations

import logging

from app.forwarders.base import BaseForwarder
from app.models import SampleRecord

logger = logging.getLogger(__name__)


class LogForwarder(BaseForwarder):
    """Discards samples after logging them.  Never touches the network."""

    name = "log"

    async def send(self, samples: list[SampleRecord]) -> dict:
        logger.info(
            "forwarder.log.received",
            extra={"stage": "forwarder", "batch_size": len(samples), "forwarder": self.name},
        )
        for s in samples:
            logger.debug(
                "forwarder.log.sample",
                extra={"stage": "forwarder", "interface_id": s.interface_id},
            )
        return {"accepted": len(samples), "dry_run": True}
