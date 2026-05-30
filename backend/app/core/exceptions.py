from __future__ import annotations

from typing import Any


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: list[dict[str, Any]] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        self.correlation_id = correlation_id
        super().__init__(self.message)


class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        details: list[dict[str, Any]] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details,
            correlation_id=correlation_id,
        )


class NotFoundError(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=404,
            correlation_id=correlation_id,
        )


class UnauthorizedError(AppException):
    def __init__(
        self,
        message: str = "Unauthorized",
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
            correlation_id=correlation_id,
        )


class ForbiddenError(AppException):
    def __init__(
        self,
        message: str = "Forbidden",
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403,
            correlation_id=correlation_id,
        )


class ConflictError(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        details: list[dict[str, Any]] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
            details=details,
            correlation_id=correlation_id,
        )


class RateLimitError(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            status_code=429,
            correlation_id=correlation_id,
        )


class ServiceUnavailableError(AppException):
    def __init__(
        self,
        message: str = "Service unavailable",
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=503,
            correlation_id=correlation_id,
        )
