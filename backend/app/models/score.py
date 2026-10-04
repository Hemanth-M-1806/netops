"""Risk score Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel


class ScoreComponents(BaseModel):
    utilisation: float
    packet_drops: float
    errors: float
    trend: float


class RiskScoreOut(BaseModel):
    interface_id: int
    severity_score: float
    severity_label: str
    impact_score: float
    max_z: float
    anomaly_flagged: bool
    components: ScoreComponents
