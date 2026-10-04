"""Device endpoints."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends, Query

from app.core.errors import NotFoundError
from app.db import acquire, fetch_many, fetch_one
from app.db import queries as Q
from app.models import DeviceListOut, DeviceOut, InterfaceListOut, InterfaceOut
from app.routers.deps import get_db_pool

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DeviceListOut)
async def list_devices(
    status: str | None = Query(default=None, description="Filter by status (UP, DOWN, etc.)"),
    device_type: str | None = Query(default=None, description="Filter by device type"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> DeviceListOut:
    """List devices with optional filtering and pagination."""
    async with acquire(pool) as conn:
        count_row = await fetch_one(
            conn,
            Q.DEVICES_COUNT,
            (status, status, device_type, device_type),
        )
        total = count_row["total"] if count_row else 0

        rows = await fetch_many(
            conn,
            Q.DEVICES_LIST_FILTERED,
            (status, status, device_type, device_type, limit, offset),
        )

    return DeviceListOut(total=total, items=[DeviceOut(**r) for r in rows])


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: int,
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> DeviceOut:
    """Retrieve details of a single device."""
    async with acquire(pool) as conn:
        row = await fetch_one(conn, Q.DEVICE_BY_ID, (device_id,))
    if not row:
        raise NotFoundError(f"Device {device_id} not found")
    return DeviceOut(**row)


@router.get("/{device_id}/interfaces", response_model=InterfaceListOut)
async def get_device_interfaces(
    device_id: int,
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> InterfaceListOut:
    """List all interfaces associated with a specific device."""
    async with acquire(pool) as conn:
        dev = await fetch_one(conn, Q.DEVICE_BY_ID, (device_id,))
        if not dev:
            raise NotFoundError(f"Device {device_id} not found")
        rows = await fetch_many(conn, Q.INTERFACES_FOR_DEVICE, (device_id,))

    return InterfaceListOut(items=[InterfaceOut(**r) for r in rows])
