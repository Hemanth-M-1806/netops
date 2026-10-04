from __future__ import annotations
from datetime import datetime, timezone
from app.config import Settings
from app.forwarders.base import BaseForwarder
from app.models import SampleRecord


def make_sample(interface_id: int = 1) -> SampleRecord:
    return SampleRecord(
        interface_id=interface_id,
        rx_bytes=1_000_000,
        tx_bytes=500_000,
        packet_drops=0,
        errors=0,
        measured_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )


def make_settings(**overrides) -> Settings:
    base = dict(
        host="127.0.0.1",
        port=8100,
        sources="push",
        forwarder="log",
        forward_url="http://localhost:8000/api/v1/telemetry/ingest",
        timeout_seconds=5.0,
        max_retries=1,
        retry_backoff_seconds=0.1,
        batch_size=200,
        api_key="",
        log_level="WARNING",
        dry_run=False,
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)


class FakeForwarder(BaseForwarder):
    name = "fake"

    def __init__(self) -> None:
        self.sent: list[list[SampleRecord]] = []

    async def send(self, samples: list[SampleRecord]) -> dict:
        self.sent.append(list(samples))
        return {"accepted": len(samples)}
