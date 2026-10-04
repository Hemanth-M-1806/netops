"""Interface endpoints."""
from __future__ import annotations

from datetime import datetime
import aiomysql
from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.db import acquire, fetch_many, fetch_one
from app.db import queries as Q
from app.models import InterfaceOut, MetricListOut, MetricOut, RiskScoreOut
from app.routers.deps import get_db_pool
from app.scoring import score_interface

router = APIRouter(prefix="/interfaces", tags=["interfaces"])


@router.get("/{interface_id}", response_model=InterfaceOut)
async def get_interface(
    interface_id: int,
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> InterfaceOut:
    """Retrieve details of a single interface."""
    async with acquire(pool) as conn:
        row = await fetch_one(conn, Q.INTERFACE_BY_ID, (interface_id,))
    if not row:
        raise NotFoundError(f"Interface {interface_id} not found")
    return InterfaceOut(**row)


@router.get("/{interface_id}/metrics", response_model=MetricListOut)
async def get_interface_metrics(
    interface_id: int,
    from_time: datetime | None = Query(default=None, description="Start of time window (ISO 8601)"),
    to_time: datetime | None = Query(default=None, description="End of time window (ISO 8601)"),
    limit: int = Query(default=100, ge=1, le=1000),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> MetricListOut:
    """Retrieve time-series telemetry metrics for an interface."""
    async with acquire(pool) as conn:
        iface = await fetch_one(conn, Q.INTERFACE_BY_ID, (interface_id,))
        if not iface:
            raise NotFoundError(f"Interface {interface_id} not found")

        if from_time is not None and to_time is not None:
            rows = await fetch_many(
                conn,
                Q.METRICS_RANGE,
                (interface_id, from_time, to_time, limit),
            )
        else:
            rows = await fetch_many(
                conn,
                Q.METRICS_LATEST,
                (interface_id, limit),
            )

    return MetricListOut(interface_id=interface_id, items=[MetricOut(**r) for r in rows])


@router.get("/{interface_id}/score", response_model=RiskScoreOut)
async def get_interface_score(
    interface_id: int,
    pool: aiomysql.Pool = Depends(get_db_pool),
    settings: Settings = Depends(get_settings),
) -> RiskScoreOut:
    """Calculate and return the dynamic risk score and baseline statistics for an interface."""
    async with acquire(pool) as conn:
        iface = await fetch_one(conn, Q.INTERFACE_BY_ID, (interface_id,))
        if not iface:
            raise NotFoundError(f"Interface {interface_id} not found")

        speed_bps: int | None = iface.get("speed_bps")
        window = await fetch_many(
            conn,
            Q.METRICS_LATEST,
            (interface_id, settings.scoring_window),
        )

    score = score_interface(interface_id, window, speed_bps, settings)
    return RiskScoreOut(**score.as_dict)
