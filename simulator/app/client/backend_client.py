"""HTTP client for backend *discovery* (devices and interfaces).

Telemetry submission now lives in ``CollectorClient``: the simulator no longer
posts metrics straight to the backend, it pushes them through the collection
layer instead.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.client.envelope import unwrap
from app.client.retry import call_with_retry
from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BackendClient:
    """Async client for devices and interfaces (the DeviceDirectory role)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=settings.timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BackendClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    # ---- internals --------------------------------------------------------
    async def _get_list(self, url: str) -> list[dict]:
        async def _do() -> Any:
            response = await self._client.get(url, params={"page_size": 200})
            response.raise_for_status()
            return response.json()

        body = await call_with_retry(
            _do,
            attempts=self._settings.max_retries,
            backoff_seconds=self._settings.retry_backoff_seconds,
        )
        data = unwrap(body)
        if isinstance(data, list):
            return data
        # Some endpoints nest the list under "items".
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
        return []

    # ---- DeviceDirectory protocol ----------------------------------------
    async def list_devices(self) -> list[dict]:
        return await self._get_list("/devices")

    async def list_interfaces(self, device_id: int) -> list[dict]:
        return await self._get_list(f"/devices/{device_id}/interfaces")

