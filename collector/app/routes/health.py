"""GET /health and GET /metrics routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app import __version__
from app.models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["observability"])


@router.get(
    "/",
    summary="Service index",
)
async def index(request: Request) -> dict:
    """Browsable root so opening the port shows service info, not a 404."""
    service = getattr(request.app.state, "service", None)
    settings = getattr(request.app.state, "settings", None)
    return {
        "service": "NetOps Collection Layer",
        "version": __version__,
        "status": "ok" if service is not None else "starting",
        "forwarder": settings.forwarder if settings else None,
        "links": {"docs": "/docs", "health": "/health", "metrics": "/metrics"},
        "endpoints": {"ingest": "POST /ingest"},
    }



@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness / readiness check",
)
async def health(request: Request) -> HealthResponse:
    service = request.app.state.service
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        version=__version__,
        sources=service.source_names,
        forwarder=settings.forwarder,
        uptime_seconds=round(service.uptime_seconds, 1),
    )


@router.get(
    "/metrics",
    summary="Running counters (received / accepted / failures)",
)
async def metrics(request: Request) -> dict:
    svc = request.app.state.service
    return {
        "success": True,
        "data": {
            "received": svc.received,
            "accepted": svc.accepted,
            "failures": svc.failures,
            "uptime_seconds": round(svc.uptime_seconds, 1),
        },
    }
