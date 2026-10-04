"""Domain models for the simulator.

Two families of objects live here:

* **Blueprints** (`DeviceSpec`, `InterfaceSpec`) — the *intended* topology that
  the simulator wants to model.
* **Runtime objects** (`InterfaceState`, `InterfaceSample`, `GeneratorResult`,
  `MetricPayload`) — what actually gets produced tick by tick.

The simulator emits **per-interval deltas** (bytes/drops/errors accumulated
during one sampling interval), not cumulative SNMP counters. This keeps the
charts unambiguous for the DBMS demo; the backend may accumulate if desired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import InterfaceStatus


# --------------------------------------------------------------------------- #
# Blueprints (static definition of the topology we want to simulate)
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class InterfaceSpec:
    """Blueprint for a single interface."""

    name: str
    interface_type: str = "ethernet"
    capacity_bps: int = 1_000_000_000  # 1 Gbps default
    baseline_utilization: float = 0.25  # 0..1 fraction of capacity
    status: str = InterfaceStatus.UP.value


@dataclass(slots=True)
class DeviceSpec:
    """Blueprint for a single device and its interfaces."""

    hostname: str
    ip_address: str
    device_type: str
    interfaces: list[InterfaceSpec] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Runtime state (mutable, one per simulated interface)
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class InterfaceState:
    """Live state carried between ticks for one interface."""

    interface_id: int
    name: str
    device_hostname: str
    device_id: int | None = None
    interface_type: str = "ethernet"
    capacity_bps: int = 1_000_000_000
    baseline_utilization: float = 0.25
    status: str = InterfaceStatus.UP.value

    # Rolling per-interval values from the previous tick (used for correlation).
    rx_bytes: int = 0
    tx_bytes: int = 0
    packet_drops: int = 0
    errors: int = 0

    # Bookkeeping.
    tick: int = 0
    health: float = 1.0  # 1.0 healthy .. 0.0 failed

    @property
    def is_down(self) -> bool:
        return self.status in {
            InterfaceStatus.DOWN.value,
            InterfaceStatus.ADMIN_DOWN.value,
        }


# --------------------------------------------------------------------------- #
# Generated output
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class InterfaceSample:
    """Per-interval telemetry produced by a generator for one interface."""

    rx_bytes: int
    tx_bytes: int
    packet_drops: int
    errors: int


@dataclass(slots=True)
class GeneratorResult:
    """Everything a generator wants the engine to apply for one interface."""

    sample: InterfaceSample
    interface_status: str | None = None  # override interface status, if any
    device_status: str | None = None  # override device status, if any


@dataclass(slots=True)
class MetricPayload:
    """Wire format sent to ``POST /api/v1/telemetry/ingest``."""

    interface_id: int
    rx_bytes: int
    tx_bytes: int
    packet_drops: int
    errors: int
    measured_at: datetime

    def as_ingest_body(self) -> dict[str, object]:
        return {
            "interface_id": self.interface_id,
            "rx_bytes": self.rx_bytes,
            "tx_bytes": self.tx_bytes,
            "packet_drops": self.packet_drops,
            "errors": self.errors,
            "measured_at": self.measured_at.isoformat(),
        }
