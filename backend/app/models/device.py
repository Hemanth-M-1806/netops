"""Device Pydantic schemas (API I/O only — no ORM)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


DeviceType = Literal["router", "switch", "firewall", "loadbalancer", "access_point", "other"]
DeviceStatus = Literal["UP", "DOWN", "WARNING", "CRITICAL", "MAINTENANCE", "UNKNOWN"]


class DeviceBase(BaseModel):
    hostname: str
    ip_address: str
    device_type: DeviceType = "other"
    status: DeviceStatus = "UNKNOWN"
    location: str | None = None
    description: str | None = None


class DeviceOut(DeviceBase):
    """Full device row as returned by the API."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int | None = None
    created_at: datetime
    updated_at: datetime

    def model_post_init(self, __context) -> None:
        if self.device_id is None:
            self.device_id = self.id


class DeviceListOut(BaseModel):
    """Paginated device list envelope."""
    total: int
    items: list[DeviceOut]


class DeviceStatusUpdate(BaseModel):
    """Single device status report (hostname-keyed, as known by producers)."""
    hostname: str
    status: DeviceStatus


class DeviceStatusUpdateIn(BaseModel):
    """Bulk device status report from the collector/simulator."""
    updates: list[DeviceStatusUpdate] = Field(default_factory=list, max_length=500)


class StatusUpdateOut(BaseModel):
    """Generic envelope for bulk status updates."""
    updated: int
