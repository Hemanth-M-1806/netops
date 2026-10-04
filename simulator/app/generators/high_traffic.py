"""High RX / high TX traffic generator.

Pushes an interface toward (but not past) saturation while keeping the link
healthy — useful for demonstrating "busy but fine" links next to anomalies.
"""

from __future__ import annotations

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState
from app.generators.base import GeneratorContext, TrafficGenerator, clamp, jitter


class HighTrafficGenerator(TrafficGenerator):
    """Elevated utilisation on both directions with modest drops."""

    name = "high_traffic"
    description = "High RX/TX utilisation below saturation."

    def __init__(
        self,
        target_utilization: float = 0.80,
        volatility: float = 0.08,
        direction: str = "both",  # both | rx | tx
        drop_rate: float = 1e-4,
    ) -> None:
        super().__init__(
            target_utilization=target_utilization,
            volatility=volatility, direction=direction, drop_rate=drop_rate,
        )
        self.target_utilization = target_utilization
        self.volatility = volatility
        self.direction = direction
        self.drop_rate = drop_rate

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng
        target = self.target_utilization

        rx_util = clamp(jitter(rng, target, self.volatility), 0.1, 0.97)
        tx_util = clamp(jitter(rng, target * 0.9, self.volatility), 0.1, 0.97)
        if self.direction == "rx":
            tx_util = state.baseline_utilization
        elif self.direction == "tx":
            rx_util = state.baseline_utilization

        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, tx_util)
        drops = int(rx_bytes * self.drop_rate * rng.uniform(0.5, 1.5))

        state.health = clamp(state.health - 0.02, 0.5, 1.0)

        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes,
                packet_drops=drops, errors=0,
            ),
            interface_status="UP",
        )
