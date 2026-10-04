"""Topology: blueprint definition and resolution to real interface ids."""

from app.topology.blueprint import default_topology
from app.topology.resolver import DeviceDirectory, TopologyResolver

__all__ = ["default_topology", "TopologyResolver", "DeviceDirectory"]
