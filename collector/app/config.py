"""Configuration for the Collection Layer.

Every tunable lives here.  Values are read from the environment with the
`COLLECTOR_` prefix, or from the repo-root `.env` / local `.env`.

Design rule: this file has zero I/O.  It is imported at startup and cached.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the telemetry collection layer."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        env_prefix="COLLECTOR_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- server ---------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = Field(default=8100, ge=1, le=65535)

    # --- sources (which inputs are active) ------------------------------------
    # Comma-separated list of source names: push, snmp, gnmi, sflow
    # In dev: "push" (simulator posts here).
    # In prod: remove "push", add "snmp" or "gnmi".
    sources: str = "push"

    @property
    def active_sources(self) -> list[str]:
        return [s.strip().lower() for s in self.sources.split(",") if s.strip()]

    # --- forwarder (where to send validated data) -----------------------------
    # "backend"  → POST to the FastAPI backend (normal mode)
    # "log"      → dry-run: log instead of forwarding
    forwarder: str = "backend"
    forward_url: str = "http://localhost:8000/api/v1/telemetry/ingest"

    # --- http tunables --------------------------------------------------------
    timeout_seconds: float = Field(default=10.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=0.5, ge=0)
    batch_size: int = Field(default=200, ge=1, le=2000)

    # --- polling sources (for future SNMP / gNMI) ----------------------------
    poll_interval_seconds: float = Field(default=30.0, gt=0)

    # --- security -------------------------------------------------------------
    # Optional shared-secret header: X-Collector-Key.
    # Empty string = no auth (dev default).
    api_key: str = ""

    # --- observability --------------------------------------------------------
    log_level: str = "INFO"
    dry_run: bool = False


def get_settings() -> Settings:
    """Factory used by FastAPI dependency injection and unit tests."""
    return Settings()
