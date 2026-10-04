"""Error generator (interface error counters).

Models a degrading link (bad cable / SFP / duplex mismatch) where the interface
*error* counter climbs independently of raw traffic volume.
"""

from __future__ import annotations

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState
from app.generators.base import GeneratorContext, TrafficGenerator, clamp, jitter


class ErrorGenerator(TrafficGenerator):
    """Normal traffic volume but a growing error counter."""

    name = "errors"
    description = "Degrading link: escalating interface errors."

    def __init__(
        self,
        ramp: float = 0.12,
        base_error_rate: float = 1e-4,
        volatility: float = 0.15,
    ) -> None:
        super().__init__(
            ramp=ramp, base_error_rate=base_error_rate, volatility=volatility
        )
        self.ramp = ramp
        self.base_error_rate = base_error_rate
        self.volatility = volatility

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng
        state.health = clamp(state.health - self.ramp, 0.1, 1.0)
        severity = 1.0 - state.health

        rx_util = clamp(
            jitter(rng, state.baseline_utilization, self.volatility), 0.01, 0.95
        )
        tx_util = clamp(rx_util * 0.85, 0.01, 0.95)

        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, tx_util)

        error_rate = self.base_error_rate * (1.0 + 40.0 * severity)
        errors = int(rx_bytes * error_rate * rng.uniform(0.7, 1.3))
        drops = int(errors * 0.1)

        status = "ERROR" if severity > 0.5 else "UP"
        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes,
                packet_drops=drops, errors=errors,
            ),
            interface_status=status,
        )
