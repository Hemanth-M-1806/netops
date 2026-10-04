"""Abstract base class for all forwarders."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import SampleRecord


class BaseForwarder(ABC):
    """All forwarders subclass this and override `send` / `close`."""

    name: str = "base"

    @abstractmethod
    async def send(self, samples: list[SampleRecord]) -> dict:
        """Deliver *samples* to the destination.  Return a result dict."""

    async def close(self) -> None:
        """Release resources (HTTP client, sockets, etc.)."""

    def __repr__(self) -> str:
        return f"<Forwarder:{self.name}>"
