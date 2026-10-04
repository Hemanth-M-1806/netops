"""Scenario model.

A scenario is a *composition* of generators: a default generator plus optional
rules that route specific interfaces to specific generators. This is how we get
realistic mixed states (most links healthy, one dropping packets, one spiking).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.domain.models import InterfaceState
from app.generators.base import TrafficGenerator

InterfaceMatcher = Callable[[InterfaceState], bool]


def on(hostname: str, interface_name: str | None = None) -> InterfaceMatcher:
    """Build a matcher for a device hostname and (optionally) interface name."""

    def _match(state: InterfaceState) -> bool:
        if state.device_hostname != hostname:
            return False
        if interface_name is None:
            return True
        return state.name == interface_name

    return _match


@dataclass(slots=True)
class ScenarioRule:
    """Route matching interfaces to a specific generator."""

    generator: TrafficGenerator
    match: InterfaceMatcher | None = None
    label: str = ""


@dataclass(slots=True)
class Scenario:
    """A named composition of generators."""

    name: str
    description: str
    default_generator: TrafficGenerator
    rules: list[ScenarioRule] = field(default_factory=list)

    def generator_for(self, state: InterfaceState) -> TrafficGenerator:
        """Return the generator responsible for ``state`` in this scenario."""
        for rule in self.rules:
            if rule.match is None or rule.match(state):
                return rule.generator
        return self.default_generator

    def reset(self) -> None:
        """Reset every generator (called once before a run)."""
        self.default_generator.reset()
        for rule in self.rules:
            rule.generator.reset()
