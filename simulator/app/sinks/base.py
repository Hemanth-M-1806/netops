"""Sink abstraction."""

from __future__ import annotations

from typing import Protocol

from app.domain.models import MetricPayload


class Sink(Protocol):
    """Destination for generated telemetry.

    Implementations must be safe to call once per tick with a batch of payloads.
    """

    async def send(self, payloads: list[MetricPayload]) -> dict:  # pragma: no cover
        """Deliver a batch and return an arbitrary result dict."""
        ...
