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
