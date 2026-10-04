"""Failure generators: interface flap and whole-device outage.

These are *stateful*: an interface/device that goes down stays down until the
recover probability fires. State is reset at the start of each scenario run via
``reset()``.
"""

from __future__ import annotations

from app.domain.models import GeneratorResult, InterfaceSample, InterfaceState
from app.generators.base import GeneratorContext, TrafficGenerator, clamp, jitter


class InterfaceFailureGenerator(TrafficGenerator):
    """An interface repeatedly flaps DOWN and (sometimes) recovers."""

    name = "interface_failure"
    description = "Interface flaps: goes DOWN, traffic stops, may recover."

    def __init__(
        self,
        down_probability: float = 0.20,
        recover_probability: float = 0.15,
    ) -> None:
        super().__init__(
            down_probability=down_probability, recover_probability=recover_probability
        )
        self.down_probability = down_probability
        self.recover_probability = recover_probability

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng

        if state.is_down:
            if rng.random() < self.recover_probability:
                state.status = "UP"
                state.health = 0.6
            else:
                return self._dead(state, "DOWN")

        if rng.random() < self.down_probability:
            state.status = "DOWN"
            state.health = 0.0
            return self._dead(state, "DOWN")

        # Healthy interval.
        rx_util = clamp(
            jitter(rng, state.baseline_utilization, 0.2), 0.01, 0.9
        )
        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, rx_util * 0.85)
        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes, packet_drops=0, errors=0
            ),
            interface_status="UP",
        )

    def _dead(self, state: InterfaceState, status: str) -> GeneratorResult:
        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=0, tx_bytes=0, packet_drops=0, errors=0
            ),
            interface_status=status,
        )


class DeviceFailureGenerator(TrafficGenerator):
    """A whole device goes DOWN — *all* its interfaces go silent together.

    Device-level down state is shared across the device's interfaces, so the
    outage is consistent (all interfaces report DOWN at the same time).
    """

    name = "device_failure"
    description = "Whole device outage: all interfaces down simultaneously."

    def __init__(
        self,
        down_probability: float = 0.08,
        recover_probability: float = 0.10,
    ) -> None:
        super().__init__(
            down_probability=down_probability, recover_probability=recover_probability
        )
        self.down_probability = down_probability
        self.recover_probability = recover_probability
        self._down_devices: set[str] = set()

    def reset(self) -> None:
        self._down_devices.clear()

    def sample(self, state: InterfaceState, ctx: GeneratorContext) -> GeneratorResult:
        rng = ctx.rng
        hostname = state.device_hostname

        if hostname in self._down_devices:
            if rng.random() < self.recover_probability:
                self._down_devices.discard(hostname)
            else:
                return self._down(state, "DOWN")

        if rng.random() < self.down_probability:
            self._down_devices.add(hostname)
            return self._down(state, "DOWN")

        rx_util = clamp(jitter(rng, state.baseline_utilization, 0.2), 0.01, 0.9)
        rx_bytes = self._bytes_for_utilization(state, ctx, rx_util)
        tx_bytes = self._bytes_for_utilization(state, ctx, rx_util * 0.85)
        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=rx_bytes, tx_bytes=tx_bytes, packet_drops=0, errors=0
            ),
            interface_status="UP",
            device_status="UP",
        )

    def _down(self, state: InterfaceState, status: str) -> GeneratorResult:
        return GeneratorResult(
            sample=InterfaceSample(
                rx_bytes=0, tx_bytes=0, packet_drops=0, errors=0
            ),
            interface_status=status,
            device_status="DOWN",
        )
