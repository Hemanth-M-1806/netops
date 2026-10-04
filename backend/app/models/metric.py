"""Telemetry / metric Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SampleIn(BaseModel):
    """One sample received from the collection layer."""
    interface_id: int = Field(gt=0)
    rx_bytes: int = Field(ge=0)
    tx_bytes: int = Field(ge=0)
    packet_drops: int = Field(ge=0)
    errors: int = Field(ge=0)
    measured_at: datetime

    @field_validator("measured_at", mode="before")
    @classmethod
    def _parse_dt(cls, v: object) -> datetime:
        from datetime import timezone
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        if isinstance(v, str):
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        raise ValueError(f"Cannot parse measured_at: {v!r}")


class IngestRequest(BaseModel):
    """Payload from the collection layer POST /telemetry/ingest."""
    source: str = "unknown"
    samples: list[SampleIn] = Field(default_factory=list)


class IngestResponse(BaseModel):
    accepted: int
    rejected: int = 0


class MetricOut(BaseModel):
    """A single metric row as returned by the API."""
    id: int
    interface_id: int
    rx_bytes: int
    tx_bytes: int
    packet_drops: int
    errors: int
    measured_at: datetime
    ingested_at: datetime


class MetricListOut(BaseModel):
    interface_id: int
    items: list[MetricOut]
