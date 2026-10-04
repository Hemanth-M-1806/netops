"""Default topology blueprint.

A small but realistic campus/edge network: two routers, two core switches, a
firewall and an access point. Capacities and baseline utilisations are chosen
so the dashboard looks plausible.
"""

from __future__ import annotations

from app.domain.enums import DeviceType, InterfaceStatus, InterfaceType
from app.domain.models import DeviceSpec, InterfaceSpec

GB = 1_000_000_000
TEN_GB = 10 * GB


def _eth(name: str, capacity_bps: int, baseline: float) -> InterfaceSpec:
    return InterfaceSpec(
        name=name,
        interface_type=InterfaceType.ETHERNET.value,
        capacity_bps=capacity_bps,
        baseline_utilization=baseline,
    )


def default_topology() -> list[DeviceSpec]:
    """Return the built-in demo topology."""
    return [
        DeviceSpec(
            hostname="R1",
            ip_address="10.0.0.1",
            device_type=DeviceType.ROUTER.value,
            interfaces=[
                _eth("Gi0/0", TEN_GB, 0.35),
                _eth("Gi0/1", TEN_GB, 0.28),
                _eth("Gi0/2", GB, 0.18),
                InterfaceSpec(
                    name="Lo0",
                    interface_type=InterfaceType.LOOPBACK.value,
                    capacity_bps=GB,
                    baseline_utilization=0.02,
                    status=InterfaceStatus.UP.value,
                ),
            ],
        ),
        DeviceSpec(
            hostname="R2",
            ip_address="10.0.0.2",
            device_type=DeviceType.ROUTER.value,
            interfaces=[
                _eth("Gi0/0", TEN_GB, 0.30),
                _eth("Gi0/1", TEN_GB, 0.22),
                InterfaceSpec(
                    name="Lo0",
                    interface_type=InterfaceType.LOOPBACK.value,
                    capacity_bps=GB,
                    baseline_utilization=0.02,
                ),
            ],
        ),
        DeviceSpec(
            hostname="CORE-SW1",
            ip_address="10.0.0.10",
            device_type=DeviceType.SWITCH.value,
            interfaces=[
                _eth("Gi1/0/1", TEN_GB, 0.40),
                _eth("Gi1/0/2", TEN_GB, 0.33),
                _eth("Gi1/0/3", GB, 0.15),
                _eth("Gi1/0/4", GB, 0.12),
                InterfaceSpec(
                    name="Vlan10",
                    interface_type=InterfaceType.VLAN.value,
                    capacity_bps=TEN_GB,
                    baseline_utilization=0.45,
                ),
            ],
        ),
        DeviceSpec(
            hostname="CORE-SW2",
            ip_address="10.0.0.11",
            device_type=DeviceType.SWITCH.value,
            interfaces=[
                _eth("Gi1/0/1", TEN_GB, 0.38),
                _eth("Gi1/0/2", TEN_GB, 0.31),
                InterfaceSpec(
                    name="Vlan10",
                    interface_type=InterfaceType.VLAN.value,
                    capacity_bps=TEN_GB,
                    baseline_utilization=0.42,
                ),
            ],
        ),
        DeviceSpec(
            hostname="FW1",
            ip_address="10.0.0.20",
            device_type=DeviceType.FIREWALL.value,
            interfaces=[
                _eth("eth0", TEN_GB, 0.50),
                _eth("eth1", TEN_GB, 0.47),
            ],
        ),
        DeviceSpec(
            hostname="AP1",
            ip_address="10.0.0.30",
            device_type=DeviceType.ACCESS_POINT.value,
            interfaces=[
                _eth("eth0", GB, 0.20),
                InterfaceSpec(
                    name="wlan0",
                    interface_type=InterfaceType.ETHERNET.value,
                    capacity_bps=GB,
                    baseline_utilization=0.25,
                ),
            ],
        ),
    ]
