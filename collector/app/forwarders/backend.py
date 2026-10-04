"""Backend forwarder — POSTs validated samples to the FastAPI backend.

Retries on transient network errors with exponential backoff.
HTTP 4xx from the backend is NOT retried (that is a bug, not a glitch).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.errors import ForwardError
from app.forwarders.base import BaseForwarder
from app.models import SampleRecord

logger = logging.getLogger(__name__)

# Transport-level errors worth retrying.
_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)


def _chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


class BackendForwarder(BaseForwarder):
    """Forwards sample batches to the FastAPI backend's ingest endpoint."""

    name = "backend"

    def __init__(
        self,
        forward_url: str,
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
        batch_size: int = 200,
    ) -> None:
        self._url = forward_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._batch_size = batch_size
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def send(self, samples: list[SampleRecord]) -> dict:
        if not samples:
            return {"accepted": 0, "batches": 0}

        accepted = 0
        batches = 0

        for batch in _chunked(samples, self._batch_size):
            body = {"samples": [s.as_backend_body() for s in batch]}
            result = await self._post_with_retry(body)
            accepted += int(result.get("accepted", len(batch)))
            batches += 1

        logger.info(
            "forwarder.backend.sent",
            extra={
                "stage": "forwarder",
                "accepted": accepted,
                "batches": batches,
                "forwarder": self.name,
            },
        )
        return {"accepted": accepted, "batches": batches}

    async def _post_with_retry(self, body: dict) -> dict:
        last_exc: BaseException | None = None
        for attempt in range(1, max(1, self._max_retries) + 1):
            try:
                resp = await self._client.post(self._url, json=body)
                resp.raise_for_status()
                data = resp.json()
                # Unwrap envelope: { "success": true, "data": {...} }
                if isinstance(data, dict) and "data" in data:
                    return data["data"] if isinstance(data["data"], dict) else data
                return data if isinstance(data, dict) else {}
            except _RETRYABLE as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    break
                delay = self._backoff * (2 ** (attempt - 1))
                logger.warning(
                    "forwarder.retry",
                    extra={"stage": "forwarder", "attempt": attempt},
                )
                await asyncio.sleep(delay)
            except httpx.HTTPStatusError as exc:
                snippet = exc.response.text[:200]
                raise ForwardError(
                    f"backend rejected: HTTP {exc.response.status_code} {snippet}",
                    status_code=exc.response.status_code,
                ) from exc

        assert last_exc is not None
        raise ForwardError(f"backend unreachable after {self._max_retries} attempts: {last_exc}")
