"""Structured logging for the simulator.

Every log record carries the module name (``logger=app.generators.packet_drops``)
so when something breaks you immediately know which function to revisit.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Minimal JSON line formatter (no external dependency)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach the ``stage`` extra when present (set via logger.info(..., extra=...)).
        for key in ("stage", "device", "interface", "scenario", "generator", "tick"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    """Human friendly formatter for interactive terminal use."""

    def format(self, record: logging.LogRecord) -> str:
        extra = ""
        for key in ("stage", "device", "interface", "scenario", "tick"):
            if hasattr(record, key):
                extra += f" {key}={getattr(record, key)}"
        base = f"{record.levelname:<8} {record.name}{extra} :: {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def configure_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    """Configure the root logger once.

    Call this from the CLI / entry point; modules simply use
    ``logging.getLogger(__name__)``.
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_logs else TextFormatter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper mirroring ``logging.getLogger``."""
    return logging.getLogger(name)
