"""Forwarder registry.

To add a new forwarder (e.g. Kafka):
  1. Create `app/forwarders/kafka.py` with `KafkaForwarder(BaseForwarder)`.
  2. Add one line to `FORWARDER_REGISTRY` below.
  3. Set `COLLECTOR_FORWARDER=kafka` in `.env`.
"""

from __future__ import annotations

from app.config import Settings
from app.core.errors import ConfigurationError
from app.forwarders.backend import BackendForwarder
from app.forwarders.base import BaseForwarder
from app.forwarders.log_forwarder import LogForwarder

FORWARDER_REGISTRY: dict[str, type[BaseForwarder]] = {
    "backend": BackendForwarder,
    "log": LogForwarder,
    # Future entries:
    # "kafka": KafkaForwarder,
    # "influx": InfluxForwarder,
}


def build_forwarder(settings: Settings) -> BaseForwarder:
    """Instantiate the configured forwarder.

    Falls back to `LogForwarder` when `dry_run=True` regardless of the
    `forwarder` setting, so you can never accidentally write to the backend
    during a dry run.
    """
    if settings.dry_run:
        return LogForwarder()

    name = settings.forwarder.lower()
    cls = FORWARDER_REGISTRY.get(name)
    if cls is None:
        known = ", ".join(sorted(FORWARDER_REGISTRY))
        raise ConfigurationError(
            f"Unknown forwarder '{name}'. Known forwarders: {known}"
        )

    if cls is BackendForwarder:
        return BackendForwarder(
            settings.forward_url,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
            backoff_seconds=settings.retry_backoff_seconds,
            batch_size=settings.batch_size,
        )
    return cls()
