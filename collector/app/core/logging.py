"""Structured logging for the collection layer.

Mirrors the pattern used in the simulator so both services emit the same
log shape in dev (text) and production (JSON → log aggregator).
"""

from __future__ import annotations

import logging
import json
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line (for Docker / log aggregators)."""

    _EXTRAS = ("stage", "source", "forwarder", "batch_size", "accepted")

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        obj: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in self._EXTRAS:
            if (val := getattr(record, key, None)) is not None:
                obj[key] = val
        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(obj)


class TextFormatter(logging.Formatter):
    """Human-friendly colourless output for terminal use."""

    _FMT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"

    def __init__(self) -> None:
        super().__init__(fmt=self._FMT, datefmt="%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        base = super().format(record)
        extras = {
            k: getattr(record, k)
            for k in ("stage", "source", "forwarder", "batch_size", "accepted")
            if hasattr(record, k)
        }
        if extras:
            base += "  " + "  ".join(f"{k}={v}" for k, v in extras.items())
        return base


def configure_logging(level: str, *, json_logs: bool = False) -> None:
    """Call once at startup to configure the root logger."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if json_logs else TextFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Silence noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-specific logger."""
    return logging.getLogger(name)
