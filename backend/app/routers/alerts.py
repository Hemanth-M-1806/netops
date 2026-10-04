"""Alerts endpoints."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends, Query

from app.core.errors import NotFoundError
from app.db import acquire, execute, fetch_many, fetch_one
from app.db import queries as Q
from app.models import AlertListOut, AlertOut, AlertResolveOut
from app.routers.deps import get_db_pool

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListOut)
async def list_alerts(
    resolved: bool | None = Query(default=None, description="Filter by resolved status"),
    severity: str | None = Query(default=None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    device_id: int | None = Query(default=None, description="Filter by device ID"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> AlertListOut:
    """List network alerts with optional filtering and pagination."""
    resolved_val = int(resolved) if resolved is not None else None
    params = (
        resolved_val,
        resolved_val,
        severity,
        severity,
        device_id,
        device_id,
    )

    async with acquire(pool) as conn:
        count_row = await fetch_one(conn, Q.ALERTS_COUNT, params)
        total = count_row["total"] if count_row else 0

        rows = await fetch_many(
            conn,
            Q.ALERTS_LIST,
            (*params, limit, offset),
        )

    # Convert tinyint(1) resolved to boolean
    items = []
    for r in rows:
        r["resolved"] = bool(r["resolved"])
        items.append(AlertOut(**r))

    return AlertListOut(total=total, items=items)


@router.patch("/{alert_id}/resolve", response_model=AlertResolveOut)
async def resolve_alert(
    alert_id: int,
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> AlertResolveOut:
    """Mark an active alert as resolved."""
    async with acquire(pool) as conn:
        existing = await fetch_one(conn, Q.ALERT_BY_ID, (alert_id,))
        if not existing:
            raise NotFoundError(f"Alert {alert_id} not found")

        await execute(conn, Q.ALERT_RESOLVE, (alert_id,))

    return AlertResolveOut(id=alert_id, resolved=True)
