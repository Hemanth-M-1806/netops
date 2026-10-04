"""Tests for the dynamic ML risk scoring formula."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from app.config import Settings
from app.scoring.formula import score_interface, RiskScore


def _make_sample(
    rx_bytes: int = 10_000_000,
    tx_bytes: int = 10_000_000,
    packet_drops: int = 0,
    errors: int = 0,
    seconds_ago: int = 0,
) -> dict:
    return {
        "rx_bytes": rx_bytes,
        "tx_bytes": tx_bytes,
        "packet_drops": packet_drops,
        "errors": errors,
        "measured_at": datetime.now(timezone.utc) - timedelta(seconds=seconds_ago),
    }


def test_empty_window():
    settings = Settings()
    score = score_interface(1, [], 1_000_000_000, settings)
    assert score.severity_label == "LOW"
    assert score.severity_score == 0.0
    assert not score.anomaly_flagged


def test_normal_healthy_traffic():
    settings = Settings()
    # 10 samples of normal, low utilization (10MB on 10Gbps link), zero drops
    window = [_make_sample(rx_bytes=10_000_000, tx_bytes=10_000_000, seconds_ago=i * 5) for i in range(10)]
    score = score_interface(1, window, 10_000_000_000, settings)
    assert score.severity_label == "LOW"
    assert score.severity_score < 0.20
    assert not score.anomaly_flagged


def test_heavy_packet_drops_flags_anomaly():
    settings = Settings()
    # 9 healthy samples, followed by sudden massive drop spike
    window = [_make_sample(rx_bytes=50_000_000, packet_drops=0, seconds_ago=i * 5) for i in range(1, 10)]
    # Latest sample has drops causing high drop rate
    # rx_pkts ~ 50_000_000 / 1400 ~ 35,714 pkts. 15,000 drops ~ 42% drops
    window.insert(0, _make_sample(rx_bytes=50_000_000, packet_drops=15000, seconds_ago=0))

    score = score_interface(1, window, 1_000_000_000, settings)
    assert score.drop_score > 0.4
    assert score.z_drop >= 3.0
    assert score.anomaly_flagged
    assert score.severity_score > 0.20


def test_critical_saturation_and_errors():
    settings = Settings()
    # 100% capacity utilization, high drops and errors
    speed_bps = 1_000_000_000  # 1 Gbps
    # bytes in 5s interval for 1Gbps ~ 625,000,000 bytes
    # rx_pkts ~ 600,000,000 / 1400 ~ 428,571 pkts. 300,000 drops is ~70% drop rate
    # errors: 150,000 errors on 1.2GB ~ error_rate_norm = 150,000 / 1.2e9 / 1e-4 = 1.25 -> clamped to 1.0
    window = [
        _make_sample(
            rx_bytes=600_000_000,
            tx_bytes=600_000_000,
            packet_drops=300000,
            errors=150000,
            seconds_ago=i * 5,
        )
        for i in range(10)
    ]
    score = score_interface(1, window, speed_bps, settings)
    assert score.severity_label in ("HIGH", "CRITICAL")
    assert score.severity_score >= 0.60
