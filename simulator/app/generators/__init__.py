"""Generator registry.

Adding a new behaviour is a two-step job: create ``app/generators/<name>.py``
exposing a ``TrafficGenerator`` subclass, then register it here. Nothing else
in the simulator needs to change.
"""

from __future__ import annotations

from app.core.errors import ConfigurationError
from app.generators.base import GeneratorContext, TrafficGenerator
from app.generators.errors import ErrorGenerator
from app.generators.failures import DeviceFailureGenerator, InterfaceFailureGenerator
from app.generators.high_traffic import HighTrafficGenerator
from app.generators.normal import NormalGenerator
from app.generators.packet_drops import PacketDropGenerator
from app.generators.spikes import SpikeGenerator

GENERATOR_REGISTRY: dict[str, type[TrafficGenerator]] = {
    NormalGenerator.name: NormalGenerator,
    HighTrafficGenerator.name: HighTrafficGenerator,
    PacketDropGenerator.name: PacketDropGenerator,
    ErrorGenerator.name: ErrorGenerator,
    SpikeGenerator.name: SpikeGenerator,
    InterfaceFailureGenerator.name: InterfaceFailureGenerator,
    DeviceFailureGenerator.name: DeviceFailureGenerator,
}


def build_generator(name: str, **params: float) -> TrafficGenerator:
    """Instantiate a generator by name."""
    try:
        generator_cls = GENERATOR_REGISTRY[name]
    except KeyError as exc:
        available = ", ".join(sorted(GENERATOR_REGISTRY))
        raise ConfigurationError(
            f"Unknown generator '{name}'. Available: {available}"
        ) from exc
    return generator_cls(**params)


def get_generator_class(name: str) -> type[TrafficGenerator]:
    """Return the generator class for ``name`` (used by the CLI)."""
    try:
        return GENERATOR_REGISTRY[name]
    except KeyError as exc:
        available = ", ".join(sorted(GENERATOR_REGISTRY))
        raise ConfigurationError(
            f"Unknown generator '{name}'. Available: {available}"
        ) from exc


__all__ = [
    "GENERATOR_REGISTRY",
    "GeneratorContext",
    "TrafficGenerator",
    "build_generator",
    "get_generator_class",
    "NormalGenerator",
    "HighTrafficGenerator",
    "PacketDropGenerator",
    "ErrorGenerator",
    "SpikeGenerator",
    "InterfaceFailureGenerator",
    "DeviceFailureGenerator",
]
