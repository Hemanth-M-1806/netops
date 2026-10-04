"""Tests for the client envelope + retry helpers (no network)."""

from __future__ import annotations

import pytest

from app.client.envelope import unwrap
from app.client.retry import call_with_retry
from app.core.errors import IngestError


def test_unwrap_returns_data_payload() -> None:
    assert unwrap({"success": True, "data": [1, 2]}) == [1, 2]


def test_unwrap_passthrough_for_plain_body() -> None:
    assert unwrap({"foo": "bar"}) == {"foo": "bar"}


def test_unwrap_raises_on_error_envelope() -> None:
    with pytest.raises(IngestError):
        unwrap({"success": False, "error": {"code": "X", "message": "boom"}})


async def test_retry_succeeds_after_transient_failures() -> None:
    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("transient")
        return "ok"

    result = await call_with_retry(
        flaky, attempts=5, backoff_seconds=0.0, retry_on=(ValueError,)
    )
    assert result == "ok"
    assert attempts["count"] == 3


async def test_retry_raises_after_exhaustion() -> None:
    async def always_fail() -> str:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        await call_with_retry(
            always_fail, attempts=2, backoff_seconds=0.0, retry_on=(ValueError,)
        )
