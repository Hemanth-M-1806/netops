import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.service import CollectorService
from app.sources.push import PushSource
from tests.helpers import FakeForwarder, make_settings


def _make_test_client() -> tuple:
    settings = make_settings()
    forwarder = FakeForwarder()
    source = PushSource()
    service = CollectorService(sources=[source], forwarder=forwarder)

    app = create_app(settings)

    # Override lifespan by injecting service directly.
    app.state.service = service
    return TestClient(app, raise_server_exceptions=True), forwarder


def test_health_ok():
    settings = make_settings()
    app = create_app(settings)
    forwarder = FakeForwarder()
    source = PushSource()
    svc = CollectorService(sources=[source], forwarder=forwarder)
    app.state.service = svc

    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


def test_ingest_endpoint_accepts_samples():
    settings = make_settings()
    app = create_app(settings)
    forwarder = FakeForwarder()
    source = PushSource()
    svc = CollectorService(sources=[source], forwarder=forwarder)
    app.state.service = svc

    payload = {
        "source": "simulator",
        "samples": [
            {
                "interface_id": 1,
                "rx_bytes": 1000,
                "tx_bytes": 2000,
                "packet_drops": 0,
                "errors": 0,
                "measured_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    }

    with TestClient(app) as client:
        resp = client.post("/ingest", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["accepted"] == 1


def test_metrics_endpoint():
    settings = make_settings()
    app = create_app(settings)
    forwarder = FakeForwarder()
    svc = CollectorService(sources=[], forwarder=forwarder)
    app.state.service = svc

    with TestClient(app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "received" in resp.json()["data"]
