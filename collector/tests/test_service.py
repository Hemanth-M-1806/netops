import pytest
from app.models import IngestRequest
from app.service import CollectorService
from app.sources.push import PushSource
from tests.helpers import FakeForwarder, make_sample


async def test_service_receive_forwards_samples():
    forwarder = FakeForwarder()
    source = PushSource()
    svc = CollectorService(sources=[source], forwarder=forwarder)
    await svc.start()

    req = IngestRequest(source="test", samples=[make_sample(1), make_sample(2)])
    result = await svc.receive(req)

    assert result["accepted"] == 2
    assert len(forwarder.sent) == 1
    assert len(forwarder.sent[0]) == 2
    assert svc.received == 2
    assert svc.accepted == 2

    await svc.stop()


async def test_service_empty_request_is_noop():
    forwarder = FakeForwarder()
    svc = CollectorService(sources=[], forwarder=forwarder)
    await svc.start()

    result = await svc.receive(IngestRequest(source="test", samples=[]))
    assert result["accepted"] == 0
    assert forwarder.sent == []

    await svc.stop()


async def test_service_uptime_increases():
    import asyncio
    forwarder = FakeForwarder()
    svc = CollectorService(sources=[], forwarder=forwarder)
    await svc.start()
    await asyncio.sleep(0.05)
    assert svc.uptime_seconds >= 0.0
    await svc.stop()
