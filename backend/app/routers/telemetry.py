"""Telemetry ingest endpoints."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, BackgroundTasks, Depends

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.db import acquire, executemany
from app.db import queries as Q
from app.models import IngestRequest, IngestResponse
from app.routers.deps import get_db_pool
from app.scoring import run_detection

logger = get_logger(__name__)
router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_telemetry(
    payload: IngestRequest,
    pool: aiomysql.Pool = Depends(get_db_pool),
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    """
    Ingest a batch of metrics from the collection layer (simulator or real network).
    Inserts raw samples into the database and triggers the dynamic anomaly detector.
    """
    if not payload.samples:
        return IngestResponse(accepted=0, rejected=0)

    rows_to_insert = [
        (
            s.interface_id,
            s.rx_bytes,
            s.tx_bytes,
            s.packet_drops,
            s.errors,
            s.measured_at,
        )
        for s in payload.samples
    ]

    async with acquire(pool) as conn:
        inserted = await executemany(conn, Q.METRICS_INSERT, rows_to_insert)

    unique_interfaces = list({s.interface_id for s in payload.samples})

    # Trigger ML dynamic scoring & alert generation
    try:
        await run_detection(pool, unique_interfaces, settings)
    except Exception as exc:
        logger.error(
            "telemetry.detection.failed",
            extra={"error": str(exc), "interfaces": unique_interfaces},
        )

    logger.info(
        "telemetry.ingested",
        extra={
            "source": payload.source,
            "samples_count": len(payload.samples),
            "inserted": inserted,
            "interfaces": len(unique_interfaces),
        },
    )

    return IngestResponse(accepted=len(payload.samples), rejected=0)
