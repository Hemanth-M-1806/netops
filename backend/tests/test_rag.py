"""Tests for RAG pipeline: context assembly, versioned prompt builder, and LLM client."""
import pytest
from app.rag import build_prompt, RetrievedContext, get_llm_client
from app.config import Settings


def test_retrieved_context_prompt_formatting():
    ctx = RetrievedContext(
        device={"hostname": "R1", "ip_address": "10.0.0.1", "device_type": "router", "status": "UP"},
        interface={"name": "Gi0/0", "interface_type": "ethernet", "status": "UP", "speed_bps": 10_000_000_000},
        metrics=[{
            "measured_at": "2026-10-04T12:00:00Z",
            "rx_bytes": 100_000_000,
            "tx_bytes": 80_000_000,
            "packet_drops": 5,
            "errors": 1,
        }],
        alerts=[{
            "severity": "HIGH",
            "alert_type": "high_drop_rate",
            "message": "Drops spike detected",
            "resolved": 0,
        }],
    )

    messages = build_prompt("v1", ctx, "What is causing packet drops on R1?")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "NetOps Copilot" in messages[0]["content"]
    assert "R1" in messages[0]["content"]
    assert "Gi0/0" in messages[0]["content"]
    assert "high_drop_rate" in messages[0]["content"]
    assert messages[1]["content"] == "What is causing packet drops on R1?"


@pytest.mark.asyncio
async def test_mock_llm_client():
    settings = Settings(llm_provider="mock")
    client = get_llm_client(settings)
    messages = [
        {"role": "system", "content": "You are a test assistant"},
        {"role": "user", "content": "Test prompt"},
    ]
    reply, tokens = await client.complete(messages)
    assert "[Mock Copilot]" in reply
    assert tokens > 0


def test_openrouter_client_factory():
    settings = Settings(
        llm_provider="openrouter",
        llm_model="qwen/qwen3.8-27b:free",
        openrouter_api_key="test-key",
    )
    client = get_llm_client(settings)
    from app.rag.llm import OpenRouterClient
    assert isinstance(client, OpenRouterClient)
    assert client._model == "qwen/qwen3.8-27b:free"
    assert client._api_key == "test-key"


@pytest.mark.asyncio
async def test_openrouter_body_error_is_retried(monkeypatch):
    """OpenRouter answers HTTP 200 with an `error` body when the upstream provider
    is overloaded. It must be retried — never returned as an empty assistant reply."""
    import asyncio
    import httpx as httpx_mod

    from app.rag.llm import OpenRouterClient

    calls = {"count": 0}

    async def fake_post(self, url, json=None, headers=None, **kwargs):
        calls["count"] += 1
        request = httpx_mod.Request("POST", url)
        if calls["count"] < 3:
            return httpx_mod.Response(
                200,
                json={
                    "error": {
                        "message": "Upstream error from Nvidia: Service temporarily overloaded",
                        "code": 503,
                    }
                },
                request=request,
            )
        return httpx_mod.Response(
            200,
            json={
                "choices": [{"message": {"content": "Ping"}}],
                "usage": {"total_tokens": 12},
            },
            request=request,
        )

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(httpx_mod.AsyncClient, "post", fake_post)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    client = OpenRouterClient(
        Settings(
            llm_provider="openrouter",
            llm_model="nvidia/nemotron-3-ultra-550b-a55b:free",
            openrouter_api_key="test-key",
        )
    )
    reply, tokens = await client.complete([{"role": "user", "content": "hi"}])
    assert reply == "Ping"
    assert tokens == 12
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_openrouter_body_error_exhausted_raises(monkeypatch):
    """Persistent upstream overload surfaces as LLMError, not an empty reply."""
    import asyncio
    import httpx as httpx_mod

    from app.core.errors import LLMError
    from app.rag.llm import OpenRouterClient

    async def fake_post(self, url, json=None, headers=None, **kwargs):
        return httpx_mod.Response(
            200,
            json={"error": {"message": "Upstream error: overloaded", "code": 503}},
            request=httpx_mod.Request("POST", url),
        )

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(httpx_mod.AsyncClient, "post", fake_post)
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    client = OpenRouterClient(
        Settings(llm_provider="openrouter", openrouter_api_key="test-key")
    )
    with pytest.raises(LLMError, match="upstream"):
        await client.complete([{"role": "user", "content": "hi"}])

