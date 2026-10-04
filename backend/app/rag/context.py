"""
RAG context retriever.

Fetches the most relevant metrics + alerts from MySQL and assembles
a structured context object that the prompt builder converts to text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import aiomysql

from app.config import Settings
from app.db import acquire, fetch_many, fetch_one
from app.db import queries as Q


@dataclass
class RetrievedContext:
    metrics: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    device: dict[str, Any] | None = None
    interface: dict[str, Any] | None = None


async def retrieve_context(
    pool: aiomysql.Pool,
    settings: Settings,
    *,
    device_id: int | None = None,
    interface_id: int | None = None,
) -> RetrievedContext:
    """
    Pull the latest metrics and open alerts from the DB.

    Scoped to a specific interface/device when provided, otherwise
    returns the most recent alerts + an aggregate view of all activity.
    """
    ctx = RetrievedContext()

    async with acquire(pool) as conn:
        # ── Device / interface context ───────────────────────────────────
        if interface_id:
            ctx.interface = await fetch_one(conn, Q.INTERFACE_BY_ID, (interface_id,))
            if ctx.interface:
                device_id = ctx.interface["device_id"]

        if device_id:
            ctx.device = await fetch_one(conn, Q.DEVICE_BY_ID, (device_id,))

        # ── Latest metrics ───────────────────────────────────────────────
        if interface_id:
            ctx.metrics = await fetch_many(
                conn,
                Q.METRICS_LATEST,
                (interface_id, settings.cache_max_context_metrics),
            )

        # ── Recent open alerts ───────────────────────────────────────────
        alert_filter = (
            0, 0,          # resolved = 0 (open only)
            None, None,    # any severity
            device_id, device_id,   # scoped to device or all
        )
        ctx.alerts = await fetch_many(
            conn,
            Q.ALERTS_LIST,
            (*alert_filter, settings.cache_max_context_alerts, 0),
        )

    return ctx
