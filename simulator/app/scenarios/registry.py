"""Scenario registry helpers."""

from __future__ import annotations

from app.core.errors import ScenarioError
from app.scenarios.base import Scenario
from app.scenarios.catalog import SCENARIO_FACTORIES


def build_scenario(name: str) -> Scenario:
    """Instantiate a scenario by name."""
    try:
        factory = SCENARIO_FACTORIES[name]
    except KeyError as exc:
        available = ", ".join(sorted(SCENARIO_FACTORIES))
        raise ScenarioError(f"Unknown scenario '{name}'. Available: {available}") from exc
    return factory()


def list_scenarios() -> list[str]:
    """Return the sorted list of scenario names."""
    return sorted(SCENARIO_FACTORIES)
