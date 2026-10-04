"""FastAPI application factory for the Collection Layer.

`create_app()` is called by the entrypoint and by tests.  It wires together:
  * the `CollectorService` (sources + forwarder)
  * the HTTP routes (`/ingest`, `/health`, `/metrics`)
  * the startup / shutdown lifespan

Design: everything the routes need is stored on `app.state` so FastAPI's
dependency injection can pull it out via `request.app.state`.  This avoids
module-level global state.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import Settings, get_settings
from app.core.errors import CollectorError
from app.core.logging import configure_logging, get_logger
from app.forwarders import build_forwarder
from app.routes.health import router as health_router
from app.routes.ingest import router as ingest_router
from app.service import CollectorService
from app.sources import build_sources

logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings: Settings = app.state.settings
    configure_logging(settings.log_level)

    sources = build_sources(settings.active_sources)
    forwarder = build_forwarder(settings)

    service = CollectorService(sources=sources, forwarder=forwarder)
    app.state.service = service

    await service.start()
    logger.info(
        "app.ready",
        extra={
            "stage": "app",
            "version": __version__,
            "port": settings.port,
            "sources": settings.active_sources,
            "forwarder": settings.forwarder,
        },
    )

    try:
        yield
    finally:
        await service.stop()
        logger.info("app.shutdown", extra={"stage": "app"})


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    _settings = settings or get_settings()

    app = FastAPI(
        title="NetOps Collection Layer",
        description=(
            "Telemetry collection microservice.  Accepts metric pushes from the "
            "simulator (dev) or from real collectors (prod) and forwards them "
            "to the backend API."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    # Store settings on app.state before lifespan runs so routes can read them.
    app.state.settings = _settings

    # CORS — wide-open for dev; tighten in prod.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(ingest_router)
    app.include_router(health_router)

    # Global error handler so CollectorError becomes a clean JSON response.
    @app.exception_handler(CollectorError)
    async def _collector_error_handler(request: Request, exc: CollectorError) -> JSONResponse:
        logger.error("app.error", extra={"stage": "app", "error": str(exc)})
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": {"message": str(exc)}},
        )

    return app
