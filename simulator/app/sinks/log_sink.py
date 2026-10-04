"""Log sink: dry-run destination used for debugging without a backend."""

from __future__ import annotations

from app.core.logging import get_logger
from app.domain.models import MetricPayload

logger = get_logger(__name__)


class LogSink:
    """Log every generated sample instead of sending it anywhere.

    This is the key debugging affordance: run a single generator, see exactly
    what it produces, with no backend required.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        self._verbose = verbose

    async def send(self, payloads: list[MetricPayload]) -> dict:
        for payload in payloads:
            if self._verbose:
                logger.info(
                    "telemetry.sample",
                    extra={
                        "stage": "dry-run",
                        "interface": payload.interface_id,
                    },
                )
        logger.info(
            "sink.log.received",
            extra={"stage": "dry-run"},
        )
        return {"accepted": len(payloads), "dry_run": True}

    async def close(self) -> None:  # symmetry with ApiSink
        return None
