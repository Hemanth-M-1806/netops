"""Clock abstraction.

Injecting the clock makes the simulation deterministic in tests: a
``FrozenClock`` advances only when ``sleep`` is called, so a 100-tick run
completes instantly and every timestamp is predictable.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Protocol


class Clock(Protocol):
    """Minimal clock interface used by the engine."""

    def now(self) -> datetime:  # pragma: no cover - protocol
        ...

    async def sleep(self, seconds: float) -> None:  # pragma: no cover - protocol
        ...


class SystemClock:
    """Real wall-clock implementation using asyncio."""

    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class FrozenClock:
    """Deterministic clock for tests: time only moves via ``sleep``."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2024, 1, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._now

    async def sleep(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
