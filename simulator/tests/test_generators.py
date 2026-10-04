"""Tests for every traffic generator.

Each generator is exercised in isolation with a seeded RNG and a fixed clock,
so failures point straight at the offending module.
"""

from __future__ import annotations

import pytest

from app.generators import GENERATOR_REGISTRY, build_generator
from app.generators.failures import DeviceFailureGenerator, InterfaceFailureGenerator
from app.generators.packet_drops import PacketDropGenerator
from tests.helpers import make_context, make_state

ALL_GENERATORS = sorted(GENERATOR_REGISTRY)


@pytest.mark.parametrize("name", ALL_GENERATORS)
def test_generator_produces_non_negative_values(name: str) -> None:
    generator = build_generator(name)
    state = make_state()
    ctx = make_context()
    for _ in range(50):
        sample = generator.sample(state, ctx).sample
        assert sample.rx_bytes >= 0
        assert sample.tx_bytes >= 0
        assert sample.packet_drops >= 0
        assert sample.errors >= 0


@pytest.mark.parametrize("name", ALL_GENERATORS)
def test_generator_never_exceeds_link_capacity(name: str) -> None:
    generator = build_generator(name)
    state = make_state(capacity_bps=1_000_000_000)
    ctx = make_context(interval_seconds=5.0)
    max_bytes = int(1_000_000_000 * 5 / 8)
    for _ in range(30):
        sample = generator.sample(state, ctx).sample
        assert sample.rx_bytes <= max_bytes
        assert sample.tx_bytes <= max_bytes


def test_packet_drops_escalate_over_time() -> None:
    generator = PacketDropGenerator(base_drop_rate=1e-4)
    state = make_state(baseline_utilization=0.5)
    ctx = make_context(seed=7)
    first = generator.sample(state, ctx).sample.packet_drops
    last = first
    for _ in range(25):
        last = generator.sample(state, ctx).sample.packet_drops
    assert last > first, "drops should grow as congestion severity increases"


def test_interface_failure_stops_traffic_when_down() -> None:
    generator = InterfaceFailureGenerator(down_probability=1.0, recover_probability=0.0)
    result = generator.sample(make_state(), make_context())
    assert result.interface_status == "DOWN"
    assert result.sample.rx_bytes == 0
    assert result.sample.tx_bytes == 0


def test_device_failure_marks_all_interfaces_down() -> None:
    generator = DeviceFailureGenerator(down_probability=1.0, recover_probability=0.0)
    ctx = make_context()
    first = generator.sample(make_state(interface_id=1, hostname="R1", name="Gi0/0"), ctx)
    second = generator.sample(make_state(interface_id=2, hostname="R1", name="Gi0/1"), ctx)
    assert first.device_status == "DOWN"
    assert second.device_status == "DOWN"
    assert first.sample.rx_bytes == 0
    assert second.sample.rx_bytes == 0


def test_device_failure_reset_clears_state() -> None:
    generator = DeviceFailureGenerator(down_probability=1.0, recover_probability=0.0)
    generator.sample(make_state(hostname="R1"), make_context())
    generator.reset()
    assert generator._down_devices == set()
