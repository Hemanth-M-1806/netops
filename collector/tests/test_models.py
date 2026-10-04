from datetime import datetime, timezone
import pytest
from app.models import IngestRequest, SampleRecord


def test_sample_record_valid():
    s = SampleRecord(
        interface_id=1,
        rx_bytes=100,
        tx_bytes=200,
        packet_drops=0,
        errors=0,
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    body = s.as_backend_body()
    assert body["interface_id"] == 1
    assert body["rx_bytes"] == 100
    assert "measured_at" in body


def test_sample_record_parses_string_datetime():
    s = SampleRecord(
        interface_id=2,
        rx_bytes=0,
        tx_bytes=0,
        packet_drops=0,
        errors=0,
        measured_at="2026-06-15T12:00:00+00:00",
    )
    assert s.measured_at.tzinfo is not None


def test_ingest_request_defaults():
    req = IngestRequest()
    assert req.source == "unknown"
    assert req.samples == []


def test_ingest_request_with_samples():
    req = IngestRequest(
        source="simulator",
        samples=[
            {
                "interface_id": 5,
                "rx_bytes": 999,
                "tx_bytes": 888,
                "packet_drops": 1,
                "errors": 0,
                "measured_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    assert len(req.samples) == 1
    assert req.samples[0].interface_id == 5
