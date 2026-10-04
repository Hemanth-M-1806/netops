"""Tests for the topology resolver."""

from __future__ import annotations

import pytest

from app.core.errors import TopologyError
from app.topology.blueprint import default_topology
from app.topology.resolver import TopologyResolver
from tests.helpers import FakeDirectory


def _r1_only():
    return [device for device in default_topology() if device.hostname == "R1"]


async def test_resolve_maps_real_interface_ids() -> None:
    devices = [{"device_id": 10, "hostname": "R1"}]
    interfaces = {
        10: [
            {"interface_id": 501, "interface_name": "Gi0/0"},
            {"interface_id": 502, "interface_name": "Gi0/1"},
        ]
    }
    resolver = TopologyResolver(FakeDirectory(devices, interfaces), allow_synthetic=False)
    states = await resolver.resolve(_r1_only())
    by_name = {state.name: state for state in states}

    assert by_name["Gi0/0"].interface_id == 501
    assert by_name["Gi0/1"].interface_id == 502
    assert by_name["Gi0/0"].device_id == 10


async def test_resolve_falls_back_to_synthetic_ids() -> None:
    resolver = TopologyResolver(None, allow_synthetic=True)
    states = await resolver.resolve(_r1_only())
    assert len(states) == len(_r1_only()[0].interfaces)
    assert all(state.interface_id >= 1 for state in states)
    assert all(state.device_id is None for state in states)


async def test_resolve_empty_blueprint_raises() -> None:
    resolver = TopologyResolver(None, allow_synthetic=True)
    with pytest.raises(TopologyError):
        await resolver.resolve([])
