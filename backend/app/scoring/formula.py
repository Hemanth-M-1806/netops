"""
Dynamic risk scoring formula.

    score_interface(window, speed_bps, settings) → RiskScore

Input: last N metric rows (dicts from interface_metrics table).
Output: RiskScore dataclass.

Two-phase scoring
─────────────────
Phase 1 — Impact score (0..1)
    Combines 4 normalised metrics with configurable weights:
      - link utilisation  (W_util  = 0.30)
      - packet drop rate  (W_drop  = 0.40)
      - error rate        (W_error = 0.20)
      - traffic trend     (W_trend = 0.10)

Phase 2 — Baseline Z-score amplifier
    For each metric, compute how many standard-deviations the *latest*
    reading is from the interface's *own historical mean* (in the window).
    If the max |z| > threshold the score is scaled upward slightly, but
    the flag is also raised so the detector can create an alert.

Final severity
──────────────
    severity_score = clamp(impact * (1 + 0.5 * clamp(max_z / sigma, 0, 1)))
    label = CRITICAL ≥ 0.80 | HIGH ≥ 0.60 | MEDIUM ≥ 0.30 | LOW
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings


# ── helpers ──────────────────────────────────────────────────────────────────

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float], mean: float) -> float:
    if len(xs) < 2:
        return 0.0
    variance = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(variance)


def _z(value: float, mean: float, std: float) -> float:
    """Z-score; returns elevated score when std is near zero but value diverges from mean."""
    if std > 1e-9:
        return abs(value - mean) / std
    if abs(value - mean) > 1e-4:
        # Significant jump from a flat zero baseline is a major anomaly
        return 10.0
    return 0.0


# ── output dataclass ─────────────────────────────────────────────────────────

@dataclass
class RiskScore:
    interface_id: int
    severity_score: float             # 0..1
    severity_label: str               # LOW | MEDIUM | HIGH | CRITICAL
    # phase-1 component scores (0..1)
    util_score: float = 0.0
    drop_score: float = 0.0
    error_score: float = 0.0
    trend_score: float = 0.0
    impact_score: float = 0.0
    # phase-2 z-scores for each metric
    z_drop: float = 0.0
    z_error: float = 0.0
    z_util: float = 0.0
    max_z: float = 0.0
    anomaly_flagged: bool = False
    # explainability fields (shown in copilot context)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def as_dict(self) -> dict[str, Any]:
        return {
            "interface_id": self.interface_id,
            "severity_score": round(self.severity_score, 4),
            "severity_label": self.severity_label,
            "impact_score": round(self.impact_score, 4),
            "max_z": round(self.max_z, 2),
            "anomaly_flagged": self.anomaly_flagged,
            "components": {
                "utilisation": round(self.util_score, 4),
                "packet_drops": round(self.drop_score, 4),
                "errors": round(self.error_score, 4),
                "trend": round(self.trend_score, 4),
            },
        }


# ── labelling ─────────────────────────────────────────────────────────────────

def _label(score: float) -> str:
    if score >= 0.80:
        return "CRITICAL"
    if score >= 0.60:
        return "HIGH"
    if score >= 0.30:
        return "MEDIUM"
    return "LOW"


# ── main scoring function ─────────────────────────────────────────────────────

def score_interface(
    interface_id: int,
    window: list[dict[str, Any]],
    speed_bps: int | None,
    settings: Settings,
) -> RiskScore:
    """
    Compute a dynamic risk score for one interface from its metric window.

    Parameters
    ----------
    interface_id : int
    window       : list of dicts from interface_metrics (newest first)
    speed_bps    : link capacity from interfaces table (None = unknown)
    settings     : runtime Settings for weights and thresholds

    Returns
    -------
    RiskScore
    """
    if not window:
        return RiskScore(interface_id=interface_id, severity_score=0.0,
                         severity_label="LOW")

    # Unpack metric series (window is newest-first, reverse for chronological)
    chron = list(reversed(window))
    latest = chron[-1]

    interval_s = max(
        float(latest.get("interval_seconds", 5.0)),
        1.0,
    )

    # ── Link utilisation ────────────────────────────────────────────────────
    cap = float(speed_bps) if speed_bps else None
    util_series: list[float] = []
    for row in chron:
        total_bytes = float(row["rx_bytes"] + row["tx_bytes"])
        total_bps = (total_bytes * 8) / interval_s
        if cap and cap > 0:
            util_series.append(_clamp(total_bps / cap))
        else:
            # No capacity known: saturate heuristic at 100 Mbps
            util_series.append(_clamp(total_bps / 100_000_000))

    util_now = util_series[-1]

    # ── Packet drop rate (drops / estimated RX packets) ────────────────────
    # Estimate RX packets: rx_bytes / 1400 (avg IP packet size heuristic)
    drop_series: list[float] = []
    for row in chron:
        rx_pkts = max(float(row["rx_bytes"]) / 1400.0, 1.0)
        drop_series.append(_clamp(float(row["packet_drops"]) / rx_pkts))

    drop_now = drop_series[-1]

    # ── Error rate (errors / (rx+tx) bytes) ────────────────────────────────
    error_series: list[float] = []
    for row in chron:
        total = max(float(row["rx_bytes"] + row["tx_bytes"]), 1.0)
        # Scale: 1 error per 1 MB → rate ≈ 9.5e-7 — normalise to 0..1
        # at 1e-4 errors/byte we call it saturated (catastrophic link)
        error_series.append(_clamp(float(row["errors"]) / total / 1e-4))

    error_now = error_series[-1]

    # ── Traffic trend (slope normalised) ───────────────────────────────────
    if len(util_series) >= 2:
        # Simple linear slope over the window, normalised by window length
        slope = (util_series[-1] - util_series[0]) / max(len(util_series) - 1, 1)
        # positive slope (rising) contributes; falling doesn't add risk
        trend_score = _clamp(slope * 10)   # amplify small slopes
    else:
        trend_score = 0.0

    # ── Phase-1 weighted impact score ──────────────────────────────────────
    w = settings
    impact = (
        w.scoring_w_util  * util_now  +
        w.scoring_w_drop  * drop_now  +
        w.scoring_w_error * error_now +
        w.scoring_w_trend * trend_score
    )
    impact = _clamp(impact)

    # ── Phase-2 Z-score baseline ───────────────────────────────────────────
    m_util  = _mean(util_series[:-1]) if len(util_series) > 1 else util_now
    s_util  = _std(util_series[:-1], m_util) if len(util_series) > 1 else 0.0

    m_drop  = _mean(drop_series[:-1]) if len(drop_series) > 1 else drop_now
    s_drop  = _std(drop_series[:-1], m_drop) if len(drop_series) > 1 else 0.0

    m_error = _mean(error_series[:-1]) if len(error_series) > 1 else error_now
    s_error = _std(error_series[:-1], m_error) if len(error_series) > 1 else 0.0

    z_util  = _z(util_now,  m_util,  s_util)
    z_drop  = _z(drop_now,  m_drop,  s_drop)
    z_error = _z(error_now, m_error, s_error)
    max_z   = max(z_util, z_drop, z_error)

    sigma = settings.anomaly_drop_sigma  # use drop sigma as the primary threshold
    anomaly = max_z > sigma

    # Amplifier: at max_z == sigma → 0%, at 2*sigma → 50%
    amplifier = 0.5 * _clamp(max_z / sigma - 1.0, 0.0, 1.0)
    final = _clamp(impact * (1.0 + amplifier))

    return RiskScore(
        interface_id=interface_id,
        severity_score=final,
        severity_label=_label(final),
        util_score=util_now,
        drop_score=drop_now,
        error_score=error_now,
        trend_score=trend_score,
        impact_score=impact,
        z_util=z_util,
        z_drop=z_drop,
        z_error=z_error,
        max_z=max_z,
        anomaly_flagged=anomaly,
        details={
            "sample_count": len(window),
            "capacity_bps": speed_bps,
            "util_now": round(util_now, 4),
            "drop_rate_now": round(drop_now, 6),
            "error_rate_now": round(error_now, 6),
        },
    )
