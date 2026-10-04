"""
Anomaly detector: runs after every telemetry ingest.

For each interface in the ingested batch:
  1. Pull the latest scoring window from the DB.
  2. Run score_interface().
  3. If anomaly_flagged and no recent matching alert exists, create one.

This is a *synchronous-style async* function called inside the ingest
route handler so alerts are created in the same HTTP cycle.
"""
from __future__ import annotations

from typing import Any

import aiomysql

from app.config import Settings
from app.core.logging import get_logger
from app.db import acquire, fetch_many, fetch_one, execute
from app.db import queries as Q
from app.scoring.formula import score_interface, RiskScore

logger = get_logger(__name__)


async def run_detection(
    pool: aiomysql.Pool,
    interface_ids: list[int],
    settings: Settings,
) -> list[RiskScore]:
    """
    Score each interface and fire alerts if anomalous.

    Parameters
    ----------
    pool          : active DB pool
    interface_ids : interfaces that just received new data
    settings      : app settings

    Returns
    -------
    List of RiskScore (one per interface).
    """
    scores: list[RiskScore] = []

    async with acquire(pool) as conn:
        for iid in interface_ids:
            # Fetch the interface's speed for utilisation normalisation
            iface = await fetch_one(conn, Q.INTERFACE_BY_ID, (iid,))
            speed_bps: int | None = iface.get("speed_bps") if iface else None

            # Fetch the scoring window
            window = await fetch_many(
                conn, Q.METRICS_LATEST, (iid, settings.scoring_window)
            )

            rs = score_interface(iid, window, speed_bps, settings)
            scores.append(rs)

            if rs.anomaly_flagged:
                await _maybe_create_alert(conn, rs, iface, settings)

    return scores


async def _maybe_create_alert(
    conn: aiomysql.Connection,
    rs: RiskScore,
    iface: dict[str, Any] | None,
    settings: Settings,
) -> None:
    """Create an alert only if no matching alert fired in the last 5 minutes."""
    alert_type = _alert_type(rs)

    existing = await fetch_one(
        conn,
        Q.ALERT_RECENT_UNRESOLVED,
        (rs.interface_id, alert_type),
    )
    if existing:
        return  # de-duplicate

    message = _build_message(rs, iface)
    await execute(
        conn,
        Q.ALERT_INSERT,
        (rs.interface_id, rs.severity_label, alert_type, message),
    )
    logger.info(
        "alert.created",
        extra={
            "interface_id": rs.interface_id,
            "severity": rs.severity_label,
            "alert_type": alert_type,
            "score": round(rs.severity_score, 3),
        },
    )


def _alert_type(rs: RiskScore) -> str:
    """Pick the dominant alert type from the score components."""
    comps = {
        "high_drop_rate": rs.drop_score,
        "high_error_rate": rs.error_score,
        "high_utilisation": rs.util_score,
        "rising_traffic": rs.trend_score,
    }
    return max(comps, key=comps.get)   # type: ignore[arg-type]


def _build_message(rs: RiskScore, iface: dict[str, Any] | None) -> str:
    iname = iface.get("name", f"iface#{rs.interface_id}") if iface else f"iface#{rs.interface_id}"
    host  = iface.get("hostname", "unknown") if iface else "unknown"
    return (
        f"{host}/{iname}: severity={rs.severity_label} "
        f"(score={rs.severity_score:.3f}, z={rs.max_z:.1f}σ) — "
        f"util={rs.util_score:.1%} drops={rs.drop_score:.4%} "
        f"errors={rs.error_score:.4%}"
    )
