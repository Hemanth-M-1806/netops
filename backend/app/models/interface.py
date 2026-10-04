"""Interface Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


InterfaceType = Literal["ethernet", "loopback", "vlan", "tunnel", "other"]
InterfaceStatus = Literal["UP", "DOWN", "ADMIN_DOWN", "ERROR", "UNKNOWN"]


class InterfaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    name: str
    interface_id: int | None = None
    interface_name: str | None = None
    interface_type: InterfaceType
    status: InterfaceStatus
    speed_bps: int | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    # present when joined with devices table
    hostname: str | None = None

    def model_post_init(self, __context) -> None:
        if self.interface_id is None:
            self.interface_id = self.id
        if self.interface_name is None:
            self.interface_name = self.name


class InterfaceListOut(BaseModel):
    items: list[InterfaceOut]


class InterfaceStatusUpdate(BaseModel):
    """Single interface status report."""
    interface_id: int
    status: InterfaceStatus


class InterfaceStatusUpdateIn(BaseModel):
    """Bulk interface status report from the collector/simulator."""
    updates: list[InterfaceStatusUpdate] = Field(default_factory=list, max_length=500)
