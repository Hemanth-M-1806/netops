"""Sinks: where generated telemetry goes.

* ``ApiSink`` posts to the backend ingestion endpoint (normal operation).
* ``LogSink`` only logs the samples (``--dry-run``; lets you debug a generator
  with no backend running).

Both implement the same ``Sink`` protocol so the engine does not care which is
active.
"""

from app.sinks.api_sink import ApiSink
from app.sinks.base import Sink
from app.sinks.log_sink import LogSink

__all__ = ["Sink", "ApiSink", "LogSink"]
