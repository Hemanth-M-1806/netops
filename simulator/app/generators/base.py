"""Generator base class and shared helpers.

A *generator* is a small, self-contained strategy that turns an
``InterfaceState`` into one interval of telemetry. Because each behaviour lives
in its own module, a bug in (say) the packet-drop logic never affects the
failure logic — you can unit test and fix it in isolation.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState

if TYPE_CHECKING:  # pragma: no cover
    from app.config import Settings


def clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))


def max_bytes_per_interval(capacity_bps: int, interval_seconds: float) -> int:
    """Bytes that would flow over the interval at 100% utilisation."""
    return int(capacity_bps * interval_seconds / 8)


def jitter(rng: random.Random, base: float, spread: float) -> float:
    """Return ``base`` perturbed by up to +/- ``spread`` (fractional)."""
    return base * (1.0 + rng.uniform(-spread, spread))


@dataclass(slots=True)
class GeneratorContext:
    """Everything a generator needs that is *not* interface state."""

    rng: random.Random
    now: datetime
    interval_seconds: float
    config: "Settings"


class TrafficGenerator(ABC):
    """Base class for all traffic generators."""

    name: str = "base"
    description: str = ""

    def __init__(self, **params: float) -> None:
        # Store arbitrary tuning parameters so scenarios can customise behaviour.
        self.params = params

    @abstractmethod
    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        """Produce one interval of telemetry for ``state``."""
        raise NotImplementedError

    # ---- shared helpers ---------------------------------------------------
    def _bytes_for_utilization(
        self, state: InterfaceState, ctx: GeneratorContext, utilization: float
    ) -> int:
        capacity = max_bytes_per_interval(state.capacity_bps, ctx.interval_seconds)
        return int(clamp(utilization, 0.0, 1.0) * capacity)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{type(self).__name__} name={self.name!r} params={self.params!r}>"

    def reset(self) -> None:
        """Clear any per-run state. Overridden by stateful generators.

        The engine calls this once at the start of every scenario run so a
        stateful generator (e.g. device failure) starts from a known baseline.
        """
        return None
