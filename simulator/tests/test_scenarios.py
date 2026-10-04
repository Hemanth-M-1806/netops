"""Tests for the scenario layer."""

from __future__ import annotations

import pytest

from app.core.errors import ScenarioError
from app.scenarios import build_scenario, list_scenarios
from app.scenarios.base import on
from tests.helpers import make_state


@pytest.mark.parametrize("name", list_scenarios())
def test_every_scenario_builds(name: str) -> None:
    scenario = build_scenario(name)
    assert scenario.name == name
    assert scenario.default_generator is not None
    assert scenario.description


def test_unknown_scenario_raises() -> None:
    with pytest.raises(ScenarioError):
        build_scenario("does_not_exist")


def test_mixed_scenario_routes_specific_interfaces() -> None:
    scenario = build_scenario("mixed")
    assert scenario.generator_for(make_state(hostname="R1", name="Gi0/1")).name == (
        "packet_drops"
    )
    assert scenario.generator_for(make_state(hostname="CORE-SW1", name="Gi1/0/2")).name == (
        "errors"
    )
    # Unlisted interface falls through to the default generator.
    assert scenario.generator_for(make_state(hostname="UNKNOWN", name="x")).name == (
        "normal"
    )


def test_on_matcher_by_interface_and_device() -> None:
    matcher = on("R1", "Gi0/0")
    assert matcher(make_state(hostname="R1", name="Gi0/0")) is True
    assert matcher(make_state(hostname="R1", name="Gi0/1")) is False
    assert on("R1")(make_state(hostname="R1", name="whatever")) is True
    assert on("R1")(make_state(hostname="R2", name="whatever")) is False


def test_scenario_reset_is_safe() -> None:
    scenario = build_scenario("device_failure")
    scenario.reset()  # must not raise
