"""Tests for the API sink with a fake telemetry client.

Covers the ``TelemetryClient`` protocol added when telemetry was re-pointed at
the collection layer.
"""

from __future__ import annotations

from app.domain.models import MetricPayload
from app.sinks.api_sink import ApiSink
from tests.helpers import FIXED_NOW


class FakeTelemetryClient:
    def __init__(self) -> None:
        self.batches: list[list[MetricPayload]] = []
        self.closed = False

    async def ingest(self, payloads: list[MetricPayload]) -> dict:
        self.batches.append(list(payloads))
        return {"accepted": len(payloads)}

    async def close(self) -> None:
        self.closed = True


def _payload(interface_id: int) -> MetricPayload:
    return MetricPayload(
        interface_id=interface_id,
        rx_bytes=1,
        tx_bytes=1,
        packet_drops=0,
        errors=0,
        measured_at=FIXED_NOW,
    )


async def test_api_sink_chunks_and_sums_accepted() -> None:
    client = FakeTelemetryClient()
    sink = ApiSink(client, batch_size=2)
    result = await sink.send([_payload(i) for i in range(5)])
    assert result == {"accepted": 5, "batches": 3}
    assert [len(batch) for batch in client.batches] == [2, 2, 1]


async def test_api_sink_empty_batch() -> None:
    sink = ApiSink(FakeTelemetryClient())
    assert await sink.send([]) == {"accepted": 0, "batches": 0}


async def test_api_sink_close_delegates() -> None:
    client = FakeTelemetryClient()
    await ApiSink(client).close()
    assert client.closed is True
