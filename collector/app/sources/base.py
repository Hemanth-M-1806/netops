"""Abstract base class for all telemetry sources.

A source produces `IngestRequest` objects.  The two abstract methods are:

* `start(service)` — called once when the collector service starts.
  Polling sources (SNMP, gNMI) launch their background tasks here.
  Push sources (HTTP) register their routes here and return immediately.

* `stop()` — called on shutdown; cancel tasks, close sockets.

The `name` class-attribute is used in logs and `GET /health`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.service import CollectorService


class BaseSource(ABC):
    """All sources subclass this and override `start` / `stop`."""

    name: str = "base"

    @abstractmethod
    async def start(self, service: "CollectorService") -> None:
        """Initialise the source.  Called once at service startup."""

    @abstractmethod
    async def stop(self) -> None:
        """Tear down the source.  Called on service shutdown."""

    def __repr__(self) -> str:
        return f"<Source:{self.name}>"
