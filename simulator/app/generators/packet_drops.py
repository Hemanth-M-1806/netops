"""Packet-drop generator (congestion).

Models a link that is being driven into congestion: utilisation climbs and
packet drops grow *faster* than traffic, which is the classic signature an
anomaly detector should flag.
"""

from __future__ import annotations

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState
from app.generators.base import GeneratorContext, TrafficGenerator, clamp, jitter


class PacketDropGenerator(TrafficGenerator):
    """Rising congestion with escalating packet drops."""

    name = "packet_drops"
    description = "Congestion: traffic near capacity with escalating drops."

    def __init__(
        self,
        congestion_utilization: float = 0.88,
        ramp: float = 0.10,
        base_drop_rate: float = 2e-4,
        volatility: float = 0.10,
    ) -> None:
        super().__init__(
            congestion_utilization=congestion_utilization, ramp=ramp,
            base_drop_rate=base_drop_rate, volatility=volatility,
        )
        self.congestion_utilization = congestion_utilization
        self.ramp = ramp
        self.base_drop_rate = base_drop_rate
        self.volatility = volatility

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng

        # Degrade health a little every tick -> severity escalates over time.
        state.health = clamp(state.health - self.ramp, 0.15, 1.0)
        severity = 1.0 - state.health  # 0..~0.85

        rx_util = clamp(
            self.congestion_utilization * (0.6 + 0.4 * severity)
            + jitter(rng, 0.0, self.volatility),
            0.1, 0.99,
        )
        tx_util = clamp(rx_util * 0.9, 0.1, 0.99)

        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, tx_util)

        # Drops grow super-linearly with congestion severity.
        drop_rate = self.base_drop_rate * (1.0 + 25.0 * severity)
        drops = int(rx_bytes * drop_rate * rng.uniform(0.8, 1.2))

        status = "DOWN" if state.is_down else "UP"
        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes,
                packet_drops=drops, errors=int(drops * 0.02),
            ),
            interface_status=status,
        )
