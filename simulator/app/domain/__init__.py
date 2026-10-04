"""Domain layer: enums and dataclasses."""

from app.domain.enums import (
    DeviceStatus,
    DeviceType,
    InterfaceStatus,
    InterfaceType,
    Severity,
)
from app.domain.models import (
    DeviceSpec,
    GeneratorResult,
    InterfaceSample,
    InterfaceSpec,
    InterfaceState,
    MetricPayload,
)

__all__ = [
    "DeviceStatus",
    "DeviceType",
    "InterfaceStatus",
    "InterfaceType",
    "Severity",
    "DeviceSpec",
    "InterfaceSpec",
    "InterfaceState",
    "InterfaceSample",
    "GeneratorResult",
    "MetricPayload",
]
