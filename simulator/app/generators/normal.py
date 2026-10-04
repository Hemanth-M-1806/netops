"""Normal (steady-state) traffic generator."""

from __future__ import annotations

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState
from app.generators.base import GeneratorContext, TrafficGenerator, clamp, jitter


class NormalGenerator(TrafficGenerator):
    """Traffic that hovers around the interface baseline with light noise.

    Packet drops and errors stay near zero, which models a healthy link.
    """

    name = "normal"
    description = "Steady-state traffic around the interface baseline."

    def __init__(
        self,
        volatility: float = 0.15,
        tx_ratio: float = 0.85,
        drop_rate: float = 2e-5,
        error_rate: float = 5e-6,
    ) -> None:
        super().__init__(
            volatility=volatility, tx_ratio=tx_ratio,
            drop_rate=drop_rate, error_rate=error_rate,
        )
        self.volatility = volatility
        self.tx_ratio = tx_ratio
        self.drop_rate = drop_rate
        self.error_rate = error_rate

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng
        rx_util = clamp(
            jitter(rng, state.baseline_utilization, self.volatility), 0.005, 0.95
        )
        tx_util = clamp(rx_util * self.tx_ratio, 0.005, 0.95)

        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, tx_util)

        drops = int(rx_bytes * self.drop_rate * rng.uniform(0.0, 2.0))
        errors = int(rx_bytes * self.error_rate * rng.uniform(0.0, 2.0))

        # A healthy interface slowly recovers toward full health.
        state.health = clamp(state.health + 0.05, 0.0, 1.0)

        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes,
                packet_drops=drops, errors=errors,
            ),
            interface_status="UP",
        )
