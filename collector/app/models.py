"""Shared Pydantic models used across the collection layer.

`IngestRequest`  — what any source sends to the collector (POST /ingest).
`SampleRecord`   — validated, normalised form forwarded to the backend.
`IngestResponse` — the collector's own response envelope.
`HealthResponse` — GET /health payload.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class SampleRecord(BaseModel):
    """A single telemetry sample, normalised from any source format."""

    interface_id: int
    rx_bytes: int = Field(ge=0)
    tx_bytes: int = Field(ge=0)
    packet_drops: int = Field(ge=0)
    errors: int = Field(ge=0)
    measured_at: datetime

    @field_validator("measured_at", mode="before")
    @classmethod
    def _parse_dt(cls, v: object) -> datetime:
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        raise ValueError(f"Cannot parse measured_at: {v!r}")

    def as_backend_body(self) -> dict:
        """Serialise to the wire format the backend expects."""
        return {
            "interface_id": self.interface_id,
            "rx_bytes": self.rx_bytes,
            "tx_bytes": self.tx_bytes,
            "packet_drops": self.packet_drops,
            "errors": self.errors,
            "measured_at": self.measured_at.isoformat(),
        }


class IngestRequest(BaseModel):
    """Payload accepted by `POST /ingest`.

    `source` names where the data came from — "simulator", "snmp-poller",
    "gnmi-agent", etc.  The collector logs it but does not act on it.
    """

    source: str = "unknown"
    samples: list[SampleRecord] = Field(default_factory=list)


class IngestResponse(BaseModel):
    """Standard response envelope returned by `POST /ingest`."""

    success: bool = True
    data: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Payload for `GET /health`."""

    status: str = "ok"
    version: str
    sources: list[str]
    forwarder: str
    uptime_seconds: float
