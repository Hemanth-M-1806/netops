"""Simulator configuration.

All tunables live here so no magic numbers are scattered across the codebase.
Values are read from the environment and/or a ``.env`` file (repo root or the
simulator folder) via ``pydantic-settings``. Every field maps to a
``SIMULATOR_*`` environment variable.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the telemetry simulator microservice."""

    model_config = SettingsConfigDict(
        # Look for .env in the simulator folder first, then the repo root.
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        env_prefix="SIMULATOR_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- identity -----------------------------------------------------------
    name: str = "telemetry-simulator"

    # --- target backend (device/interface discovery) ------------------------
    api_base_url: str = "http://localhost:8000/api/v1"

    # --- collection layer (telemetry destination) ---------------------------
    # Telemetry is pushed here, NOT to the backend directly. In production the
    # collection layer is fed by real collectors (SNMP/gNMI) and the simulator is
    # simply removed — only this URL changes.
    collector_url: str = "http://localhost:8100/ingest"

    timeout_seconds: float = Field(default=10.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=0.5, ge=0)
    batch_size: int = Field(default=200, ge=1, le=2000)

    # --- run loop -----------------------------------------------------------
    interval_seconds: float = Field(default=5.0, gt=0)
    random_seed: int | None = None

    # --- behaviour ----------------------------------------------------------
    default_scenario: str = "mixed"
    dry_run: bool = False
    enabled: bool = False

    # --- observability ------------------------------------------------------
    log_level: str = "INFO"

    # --- status endpoint (browsable run state; see app.status) --------------
    # SIMULATOR_HOST / SIMULATOR_PORT / SIMULATOR_STATUS_ENABLED
    host: str = "0.0.0.0"
    port: int = Field(default=8200, ge=1, le=65535)
    status_enabled: bool = True

    # --- topology resolution ------------------------------------------------
    # When the backend has no devices yet, build synthetic interface ids so the
    # simulator can still be exercised offline (dry-run / unit tests).
    allow_synthetic_topology: bool = True


def get_settings() -> Settings:
    """Factory so tests can build their own Settings without global state."""
    return Settings()
