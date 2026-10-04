"""Typed exceptions → HTTP status codes."""
from __future__ import annotations

from fastapi import HTTPException, status


class AppError(Exception):
    """Base application error."""
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)

    def as_http(self) -> HTTPException:
        return HTTPException(status_code=self.http_status, detail=self.detail)


class NotFoundError(AppError):
    http_status = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ValidationError(AppError):
    http_status = 422
    detail = "Validation error"


class DatabaseError(AppError):
    http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Database unavailable"


class ScoringError(AppError):
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Risk scoring failed"


class LLMError(AppError):
    http_status = status.HTTP_502_BAD_GATEWAY
    detail = "LLM provider error"
