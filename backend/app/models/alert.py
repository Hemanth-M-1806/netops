"""Alert Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    interface_id: int
    severity: Severity
    alert_type: str
    message: str
    resolved: bool
    triggered_at: datetime
    resolved_at: datetime | None
    # joined fields
    interface_name: str | None = None
    hostname: str | None = None


class AlertListOut(BaseModel):
    total: int
    items: list[AlertOut]


class AlertResolveOut(BaseModel):
    id: int
    resolved: bool = True
