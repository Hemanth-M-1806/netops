"""Health check endpoint."""
from __future__ import annotations

import aiomysql
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.db import acquire, fetch_one
from app.routers.deps import get_db_pool

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(pool: aiomysql.Pool = Depends(get_db_pool)) -> JSONResponse:
    """Service and database health check."""
    db_ok = False
    try:
        async with acquire(pool) as conn:
            row = await fetch_one(conn, "SELECT 1 AS alive")
            db_ok = row is not None and row.get("alive") == 1
    except Exception as exc:
        logger.warning("health_check.db_failed", extra={"error": str(exc)})

    if db_ok:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "connected",
                "version": "0.1.0",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "degraded",
            "database": "unreachable",
            "version": "0.1.0",
        },
    )
