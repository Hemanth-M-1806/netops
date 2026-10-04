"""Tests for domain models."""

from __future__ import annotations

from app.domain.models import InterfaceState, MetricPayload
from tests.helpers import FIXED_NOW, make_state


def test_metric_payload_body_shape() -> None:
    payload = MetricPayload(
        interface_id=7,
        rx_bytes=100,
        tx_bytes=200,
        packet_drops=3,
        errors=1,
        measured_at=FIXED_NOW,
    )
    body = payload.as_ingest_body()
    assert body["interface_id"] == 7
    assert body["rx_bytes"] == 100
    assert body["packet_drops"] == 3
    assert isinstance(body["measured_at"], str)
    assert body["measured_at"].startswith("2024-01-01T12:00:00")


def test_interface_state_is_down_for_down_and_admin_down() -> None:
    assert make_state(status="DOWN").is_down is True
    assert make_state(status="ADMIN_DOWN").is_down is True
    assert make_state(status="UP").is_down is False


def test_interface_state_defaults() -> None:
    state: InterfaceState = make_state()
    assert state.health == 1.0
    assert state.tick == 0
    assert state.rx_bytes == 0
