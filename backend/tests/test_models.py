"""Tests for Pydantic models and validation."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models import IngestRequest, SampleIn, DeviceOut, InterfaceOut, AlertOut


def test_sample_in_validation():
    valid = SampleIn(
        interface_id=1,
        rx_bytes=1000,
        tx_bytes=2000,
        packet_drops=0,
        errors=0,
        measured_at="2026-10-04T12:00:00Z",
    )
    assert valid.interface_id == 1
    assert valid.measured_at.tzinfo is not None

    with pytest.raises(ValidationError):
        SampleIn(
            interface_id=0,  # must be gt 0
            rx_bytes=1000,
            tx_bytes=2000,
            packet_drops=0,
            errors=0,
            measured_at="2026-10-04T12:00:00Z",
        )


def test_ingest_request_envelope():
    req = IngestRequest(
        source="collector",
        samples=[
            SampleIn(
                interface_id=10,
                rx_bytes=500,
                tx_bytes=500,
                packet_drops=0,
                errors=0,
                measured_at=datetime.now(timezone.utc),
            )
        ],
    )
    assert req.source == "collector"
    assert len(req.samples) == 1
