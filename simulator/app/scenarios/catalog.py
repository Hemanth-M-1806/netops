"""Built-in scenarios."""

from __future__ import annotations

from app.generators import (
    DeviceFailureGenerator,
    ErrorGenerator,
    HighTrafficGenerator,
    InterfaceFailureGenerator,
    NormalGenerator,
    PacketDropGenerator,
    SpikeGenerator,
)
from app.scenarios.base import Scenario, ScenarioRule, on


def _normal() -> Scenario:
    return Scenario(
        name="normal",
        description="All interfaces at steady-state baseline.",
        default_generator=NormalGenerator(),
    )


def _high_traffic() -> Scenario:
    return Scenario(
        name="high_traffic",
        description="All interfaces pushed to high (but healthy) utilisation.",
        default_generator=HighTrafficGenerator(),
    )


def _packet_drops() -> Scenario:
    return Scenario(
        name="packet_drops",
        description="All interfaces congested with rising packet drops.",
        default_generator=PacketDropGenerator(),
    )


def _errors() -> Scenario:
    return Scenario(
        name="errors",
        description="All interfaces showing rising error counters.",
        default_generator=ErrorGenerator(),
    )


def _spikes() -> Scenario:
    return Scenario(
        name="spikes",
        description="Sudden traffic bursts on top of a normal baseline.",
        default_generator=SpikeGenerator(),
    )


def _interface_failure() -> Scenario:
    return Scenario(
        name="interface_failure",
        description="Interfaces flap DOWN intermittently.",
        default_generator=InterfaceFailureGenerator(),
    )


def _device_failure() -> Scenario:
    return Scenario(
        name="device_failure",
        description="Whole devices go OUT intermittently.",
        default_generator=DeviceFailureGenerator(),
    )


def _mixed() -> Scenario:
    """The default demo: healthy network with a few interesting faults.

    This produces a dashboard where most links look fine and a handful of
    anomalies stand out — exactly what an observability demo should show.
    """
    normal = NormalGenerator()
    return Scenario(
        name="mixed",
        description="Mostly healthy network with a few targeted faults.",
        default_generator=normal,
        rules=[
            ScenarioRule(
                generator=PacketDropGenerator(),
                match=on("R1", "Gi0/1"),
                label="R1 Gi0/1 congestion",
            ),
            ScenarioRule(
                generator=ErrorGenerator(),
                match=on("CORE-SW1", "Gi1/0/2"),
                label="CORE-SW1 Gi1/0/2 errors",
            ),
            ScenarioRule(
                generator=SpikeGenerator(),
                match=on("R2", "Gi0/0"),
                label="R2 Gi0/0 spikes",
            ),
            ScenarioRule(
                generator=HighTrafficGenerator(),
                match=on("FW1"),
                label="FW1 high throughput",
            ),
            ScenarioRule(
                generator=InterfaceFailureGenerator(),
                match=on("AP1", "eth0"),
                label="AP1 eth0 flapping",
            ),
        ],
    )


# Registry of scenario name -> factory. Add new scenarios here.
SCENARIO_FACTORIES = {
    "normal": _normal,
    "high_traffic": _high_traffic,
    "packet_drops": _packet_drops,
    "errors": _errors,
    "spikes": _spikes,
    "interface_failure": _interface_failure,
    "device_failure": _device_failure,
    "mixed": _mixed,
}
