"""Scenario composition layer."""

from app.scenarios.base import Scenario, ScenarioRule, on
from app.scenarios.catalog import SCENARIO_FACTORIES
from app.scenarios.registry import build_scenario, list_scenarios

__all__ = [
    "Scenario",
    "ScenarioRule",
    "on",
    "SCENARIO_FACTORIES",
    "build_scenario",
    "list_scenarios",
]
