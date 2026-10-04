"""Resolve blueprint interfaces to real ``interface_id`` values.

The simulator does not invent primary keys — it asks the backend for the
devices and interfaces that actually exist, then matches them by name.

Decoupling: the resolver depends only on the small ``DeviceDirectory`` protocol,
not on the concrete HTTP client, so it can be unit-tested with a fake.
"""

from __future__ import annotations

from typing import Protocol

from app.core.errors import TopologyError
from app.core.logging import get_logger
from app.domain.models import DeviceSpec, InterfaceState

logger = get_logger(__name__)


class DeviceDirectory(Protocol):
    """Minimal read interface the resolver needs."""

    async def list_devices(self) -> list[dict]:  # pragma: no cover - protocol
        ...

    async def list_interfaces(self, device_id: int) -> list[dict]:  # pragma: no cover
        ...


class TopologyResolver:
    """Turn a blueprint into concrete ``InterfaceState`` objects."""

    def __init__(
        self, directory: DeviceDirectory | None, *, allow_synthetic: bool = True
    ) -> None:
        self.directory = directory
        self.allow_synthetic = allow_synthetic

    async def resolve(self, blueprint: list[DeviceSpec]) -> list[InterfaceState]:
        """Resolve each blueprint interface to a usable ``InterfaceState``."""
        state: list[InterfaceState] = []
        synthetic_id = 1

        try:
            devices = await self.directory.list_devices() if self.directory else []
        except Exception as exc:  # pragma: no cover - network dependent
            if not self.allow_synthetic:
                raise TopologyError(f"could not list devices: {exc}") from exc
            logger.warning("topology.directory_unavailable", extra={"stage": "topology"})
            devices = []

        by_hostname = {d.get("hostname"): d for d in devices}

        for device in blueprint:
            backend_device = by_hostname.get(device.hostname)
            interfaces_by_name: dict[str, dict] = {}

            if backend_device is not None:
                try:
                    found = await self.directory.list_interfaces(backend_device["device_id"])
                    interfaces_by_name = {i.get("interface_name"): i for i in found}
                except Exception as exc:  # pragma: no cover - network dependent
                    logger.warning(
                        "topology.interface_list_failed",
                        extra={"stage": "topology", "device": device.hostname},
                    )
                    if not self.allow_synthetic:
                        raise TopologyError(str(exc)) from exc

            for spec in device.interfaces:
                backend_interface = interfaces_by_name.get(spec.name)
                if backend_interface is not None:
                    interface_id = int(backend_interface["interface_id"])
                elif self.allow_synthetic or backend_device is None:
                    interface_id = synthetic_id
                    synthetic_id += 1
                    logger.debug(
                        "topology.synthetic_interface",
                        extra={"device": device.hostname, "interface": spec.name},
                    )
                else:
                    # Backend exists but interface is missing and synthetic is off.
                    logger.warning(
                        "topology.interface_missing",
                        extra={"device": device.hostname, "interface": spec.name},
                    )
                    continue

                state.append(
                    InterfaceState(
                        interface_id=interface_id,
                        name=spec.name,
                        device_hostname=device.hostname,
                        device_id=backend_device["device_id"] if backend_device else None,
                        interface_type=spec.interface_type,
                        capacity_bps=spec.capacity_bps,
                        baseline_utilization=spec.baseline_utilization,
                        status=spec.status,
                    )
                )

        if not state:
            raise TopologyError("resolved topology is empty")

        logger.info(
            "topology.resolved",
            extra={"stage": "topology"},
        )
        return state
