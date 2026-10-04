"""Spike generator.

Mostly normal traffic punctuated by sudden, short-lived bursts — the pattern
that produces dramatic, easily-visible spikes on the dashboard chart.
"""

from __future__ import annotations

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState
from app.generators.base import GeneratorContext, TrafficGenerator, clamp, jitter


class SpikeGenerator(TrafficGenerator):
    """Normal baseline with occasional sudden bursts."""

    name = "spikes"
    description = "Sudden traffic spikes on top of a normal baseline."

    def __init__(
        self,
        spike_probability: float = 0.15,
        min_magnitude: float = 0.25,
        max_magnitude: float = 0.60,
        volatility: float = 0.12,
    ) -> None:
        super().__init__(
            spike_probability=spike_probability, min_magnitude=min_magnitude,
            max_magnitude=max_magnitude, volatility=volatility,
        )
        self.spike_probability = spike_probability
        self.min_magnitude = min_magnitude
        self.max_magnitude = max_magnitude
        self.volatility = volatility

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng
        spiking = rng.random() < self.spike_probability

        if spiking:
            magnitude = rng.uniform(self.min_magnitude, self.max_magnitude)
            rx_util = clamp(state.baseline_utilization + magnitude, 0.05, 0.99)
            rx_util = clamp(jitter(rng, rx_util, 0.05), 0.05, 0.99)
            drops = int(
                self._bytes_for_utilization(state, ctx, rx_util) * 3e-4 * (magnitude * 4)
            )
            state.health = clamp(state.health - 0.08, 0.3, 1.0)
        else:
            rx_util = clamp(
                jitter(rng, state.baseline_utilization, self.volatility), 0.01, 0.95
            )
            drops = int(self._bytes_for_utilization(state, ctx, rx_util) * 1e-5)
            state.health = clamp(state.health + 0.03, 0.0, 1.0)

        tx_util = clamp(rx_util * 0.85, 0.01, 0.99)
        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, tx_util)

        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes,
                packet_drops=drops, errors=0,
            ),
            interface_status="UP",
        )
