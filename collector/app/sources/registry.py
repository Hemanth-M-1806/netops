"""Source registry: maps source names to classes and builds the active list.

To add a new source (e.g. SNMP):
  1. Create `app/sources/snmp.py` with a `SnmpSource(BaseSource)` subclass.
  2. Add one line to `SOURCE_REGISTRY` below.
  3. Set `COLLECTOR_SOURCES=push,snmp` in `.env`.
"""

from __future__ import annotations

from app.core.errors import ConfigurationError
from app.sources.base import BaseSource
from app.sources.push import PushSource

# --- registry ---------------------------------------------------------------
SOURCE_REGISTRY: dict[str, type[BaseSource]] = {
    "push": PushSource,
    # Future entries (uncomment + implement):
    # "snmp": SnmpSource,
    # "gnmi": GnmiSource,
    # "sflow": SflowSource,
}


def build_sources(active: list[str]) -> list[BaseSource]:
    """Instantiate every source name in *active*.

    Raises `ConfigurationError` for unknown names so the service fails
    fast at startup rather than silently collecting no data.
    """
    sources: list[BaseSource] = []
    for name in active:
        cls = SOURCE_REGISTRY.get(name)
        if cls is None:
            known = ", ".join(sorted(SOURCE_REGISTRY))
            raise ConfigurationError(
                f"Unknown source '{name}'. Known sources: {known}"
            )
        sources.append(cls())
    return sources
