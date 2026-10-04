"""Typed simulator errors.

Having explicit exception classes (instead of raising bare ``Exception``) means
a failure message always tells you *which stage* broke, e.g. a topology lookup
problem vs. an HTTP ingest problem. This is what lets you "go back to the one
function" that failed.
"""

from __future__ import annotations


class SimulatorError(Exception):
    """Base class for every simulator error."""

    def __init__(self, message: str, *, stage: str = "unknown") -> None:
        super().__init__(message)
        self.message = message
        self.stage = stage

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.stage}] {self.message}"


class ConfigurationError(SimulatorError):
    """Invalid or missing configuration."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="config")


class TopologyError(SimulatorError):
    """Raised when the topology blueprint cannot be resolved."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="topology")


class GenerationError(SimulatorError):
    """Raised when a traffic generator cannot produce a sample."""

    def __init__(self, generator: str, message: str) -> None:
        super().__init__(f"{generator}: {message}", stage="generator")


class IngestError(SimulatorError):
    """Raised when sending telemetry to the backend fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, stage="ingest")
        self.status_code = status_code


class ScenarioError(SimulatorError):
    """Raised for unknown / invalid scenarios."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="scenario")
