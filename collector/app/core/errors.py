"""Typed exceptions for the collection layer."""

from __future__ import annotations


class CollectorError(Exception):
    """Base class for all collection-layer errors.  Never raise directly."""

    def __init__(self, message: str, *, stage: str = "unknown") -> None:
        super().__init__(message)
        self.stage = stage

    def __str__(self) -> str:
        return f"[{self.stage}] {super().__str__()}"


class ForwardError(CollectorError):
    """Forwarding a batch to the backend failed."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, stage="forwarder")
        self.status_code = status_code


class SourceError(CollectorError):
    """A data source (push / SNMP / gNMI) could not be initialised or polled."""

    def __init__(self, message: str, *, source: str = "unknown") -> None:
        super().__init__(message, stage=f"source.{source}")


class ConfigurationError(CollectorError):
    """Invalid or missing configuration value."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="config")
