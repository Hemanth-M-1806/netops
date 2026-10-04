"""Domain enums.

These mirror the controlled vocabularies enforced by the MySQL CHECK
constraints, so the simulator can never emit a value the database will reject.
"""

from __future__ import annotations

from enum import Enum


class DeviceType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    LOADBALANCER = "loadbalancer"
    ACCESS_POINT = "access_point"
    OTHER = "other"


class DeviceStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class InterfaceType(str, Enum):
    ETHERNET = "ethernet"
    LOOPBACK = "loopback"
    VLAN = "vlan"
    TUNNEL = "tunnel"


class InterfaceStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    ADMIN_DOWN = "ADMIN_DOWN"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
