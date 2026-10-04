"""FastAPI application factory and lifespan configuration."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger
from app.db import create_pool
from app.routers import (
    alerts_router,
    copilot_router,
    devices_router,
    health_router,
    interfaces_router,
    telemetry_router,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for resource initialization and teardown."""
    settings = get_settings()
    configure_logging(
        level=settings.log_level,
        json_logs=(settings.app_env == "production"),
    )
    logger.info("app.starting", extra={"env": settings.app_env, "version": "0.1.0"})

    # Initialize raw aiomysql connection pool
    pool = await create_pool(settings)
    app.state.pool = pool

    yield

    # Clean pool shutdown
    logger.info("app.stopping")
    pool.close()
    await pool.wait_closed()
    logger.info("app.stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="NetOps RDBMS Telemetry, ML Risk Scoring & AI Copilot Backend",
        lifespan=lifespan,
    )

    # ── CORS Middleware ───────────────────────────────────────────────────────
    # Support development and production frontends cleanly
    origins = [
        settings.frontend_origin,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    if settings.app_env == "development":
        origins.append("*")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ────────────────────────────────────────────────────
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.error("app.unhandled_exception", extra={"error": str(exc), "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = settings.api_v1_prefix
    app.include_router(health_router, prefix=prefix)
    app.include_router(devices_router, prefix=prefix)
    app.include_router(interfaces_router, prefix=prefix)
    app.include_router(telemetry_router, prefix=prefix)
    app.include_router(alerts_router, prefix=prefix)
    app.include_router(copilot_router, prefix=prefix)

    # Root health probe endpoint for Docker / orchestration
    app.include_router(health_router)

    return app


app = create_app()
