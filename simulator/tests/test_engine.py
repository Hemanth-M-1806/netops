"""Tests for the simulation engine using a frozen clock and fake sink."""

from __future__ import annotations

from app.config import Settings
from app.engine.clock import FrozenClock
from app.engine.simulator import Simulator
from app.generators.normal import NormalGenerator
from tests.helpers import FakeSink, make_state


def _build(sink: FakeSink, clock: FrozenClock, interfaces, generator) -> Simulator:
    settings = Settings(_env_file=None, interval_seconds=5.0)
    return Simulator(
        settings=settings,
        interfaces=interfaces,
        sink=sink,
        generator_for=lambda state: generator,
        reset_generators=lambda: None,
        clock=clock,
    )


async def test_tick_emits_one_payload_per_interface() -> None:
    sink = FakeSink()
    sim = _build(
        sink,
        FrozenClock(),
        [make_state(interface_id=1), make_state(interface_id=2)],
        NormalGenerator(),
    )
    summary = await sim.tick()
    assert summary["samples"] == 2
    assert {p.interface_id for p in sink.all_payloads} == {1, 2}


async def test_run_respects_tick_count() -> None:
    sink = FakeSink()
    sim = _build(sink, FrozenClock(), [make_state()], NormalGenerator())
    summary = await sim.run(ticks=3)
    assert summary["ticks"] == 3
    assert summary["totals"]["samples"] == 3
    assert sink.batches  # sink was actually used


async def test_run_respects_duration_with_frozen_clock() -> None:
    sink = FakeSink()
    sim = _build(sink, FrozenClock(), [make_state()], NormalGenerator())
    # interval=5s, so 15s of simulated time == 3 ticks.
    summary = await sim.run(duration_seconds=15)
    assert summary["ticks"] == 3


async def test_engine_counts_generator_failures_without_crashing() -> None:
    class BoomGenerator(NormalGenerator):
        name = "boom"

        def sample(self, state, ctx):  # type: ignore[override]
            raise RuntimeError("boom")

    sink = FakeSink()
    sim = _build(sink, FrozenClock(), [make_state()], BoomGenerator())
    summary = await sim.tick()
    assert summary["samples"] == 0
    assert sim.totals["failures"] == 1
