"""Shared test helpers and fakes.

Fakes (``FakeSink``, ``FakeDirectory``) let each module be tested without any
network or database, which is exactly what makes debugging a single function
easy.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone

from app.config import Settings
from app.domain.models import InterfaceState, MetricPayload
from app.generators.base import GeneratorContext

FIXED_NOW = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_state(
    *,
    interface_id: int = 1,
    name: str = "Gi0/0",
    hostname: str = "R1",
    capacity_bps: int = 1_000_000_000,
    baseline_utilization: float = 0.3,
    status: str = "UP",
) -> InterfaceState:
    """Build a deterministic ``InterfaceState`` for tests."""
    return InterfaceState(
        interface_id=interface_id,
        name=name,
        device_hostname=hostname,
        capacity_bps=capacity_bps,
        baseline_utilization=baseline_utilization,
        status=status,
    )


def make_context(
    *, seed: int = 1234, interval_seconds: float = 5.0
) -> GeneratorContext:
    """Build a ``GeneratorContext`` with a seeded RNG and fixed clock."""
    return GeneratorContext(
        rng=random.Random(seed),
        now=FIXED_NOW,
        interval_seconds=interval_seconds,
        config=Settings(_env_file=None),
    )


class FakeSink:
    """Captures payloads instead of sending them."""

    def __init__(self) -> None:
        self.batches: list[list[MetricPayload]] = []
        self.closed = False

    async def send(self, payloads: list[MetricPayload]) -> dict:
        self.batches.append(list(payloads))
        return {"accepted": len(payloads)}

    async def close(self) -> None:
        self.closed = True

    @property
    def all_payloads(self) -> list[MetricPayload]:
        return [p for batch in self.batches for p in batch]


class FakeDirectory:
    """In-memory DeviceDirectory implementing the resolver protocol."""

    def __init__(
        self,
        devices: list[dict] | None = None,
        interfaces: dict[int, list[dict]] | None = None,
    ) -> None:
        self._devices = devices or []
        self._interfaces = interfaces or {}

    async def list_devices(self) -> list[dict]:
        return list(self._devices)

    async def list_interfaces(self, device_id: int) -> list[dict]:
        return list(self._interfaces.get(device_id, []))
