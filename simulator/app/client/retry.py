"""Async retry helper with exponential backoff.

Isolated here so any client (ingestion, directory lookup) can opt into the same
retry policy without repeating the loop.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Transport-level problems worth retrying (NOT 4xx application errors).
DEFAULT_RETRYABLE: tuple[type[BaseException], ...] = (
    httpx.TransportError,
    httpx.TimeoutException,
)


async def call_with_retry(
    factory: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    backoff_seconds: float = 0.5,
    retry_on: tuple[type[BaseException], ...] = DEFAULT_RETRYABLE,
) -> T:
    """Call ``factory()`` until it succeeds or attempts are exhausted.

    ``factory`` is a zero-argument coroutine factory so the call is re-created
    on each attempt (important for streaming/one-shot request objects).
    """
    last_exc: BaseException | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            return await factory()
        except retry_on as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            delay = backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                "retry.attempt",
                extra={"stage": "client"},
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
