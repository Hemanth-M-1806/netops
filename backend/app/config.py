"""
Central configuration for the NetOps backend.

All values read from environment variables (or .env / ../.env).
No magic numbers anywhere else in the codebase.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ─────────────────────────────────────────────────────────
    app_env: Literal["development", "production", "test"] = "development"
    app_name: str = "NetOps Backend"
    log_level: str = "INFO"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"

    # ── MySQL (raw aiomysql — no ORM) ────────────────────────────────────────
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "netops"
    mysql_password: str = "netops"
    mysql_database: str = "netops"
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0)
    db_echo: bool = False  # log every SQL statement when True

    @property
    def db_dsn(self) -> dict:
        """Connection kwargs for aiomysql.create_pool()."""
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "db": self.mysql_database,
            "autocommit": True,
            "charset": "utf8mb4",
        }

    # ── Risk Scoring ─────────────────────────────────────────────────────────
    # Weights must sum to 1.0
    scoring_w_util: float = Field(default=0.30, ge=0, le=1)
    scoring_w_drop: float = Field(default=0.40, ge=0, le=1)
    scoring_w_error: float = Field(default=0.20, ge=0, le=1)
    scoring_w_trend: float = Field(default=0.10, ge=0, le=1)
    # Window size for rolling statistics (number of samples)
    scoring_window: int = Field(default=20, ge=5)
    # Z-score threshold to flag an anomaly
    anomaly_drop_sigma: float = Field(default=3.0, gt=0)
    anomaly_error_sigma: float = Field(default=3.0, gt=0)

    # ── LLM / RAG ────────────────────────────────────────────────────────────
    llm_provider: Literal["mock", "openai", "ollama", "local", "openrouter"] = "openrouter"
    llm_model: str = "qwen/qwen3.8-27b:free"
    llm_temperature: float = Field(default=0.2, ge=0, le=2)
    llm_max_tokens: int = Field(default=800, ge=1)
    prompt_version: str = "v1"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_base_url: str = "http://localhost:11434"
    # RAG context window limits
    cache_max_context_metrics: int = Field(default=50, ge=1)
    cache_max_context_alerts: int = Field(default=10, ge=1)

    # ── Rate limiting ────────────────────────────────────────────────────────
    rate_limit_per_minute: int = Field(default=120, ge=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
