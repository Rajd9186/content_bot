from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import Any

from app.agents.contracts import RetryPolicy
from app.agents.retry.strategy import FullJitterBackoff

logger = logging.getLogger(__name__)


class RetryReason(StrEnum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PROVIDER_ERROR = "provider_error"
    SERVER_ERROR = "server_error"
    MALFORMED_RESPONSE = "malformed_response"
    VALIDATION_FAILED = "validation_failed"
    UNKNOWN = "unknown"


class RetryPolicyExecutor:
    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy
        self._backoff = FullJitterBackoff(
            base_delay_ms=policy.base_delay_ms,
            max_delay_ms=policy.max_delay_ms,
            jitter_factor=policy.jitter_factor,
        )
        self._attempt = 0
        self._last_error: str | None = None
        self._retry_history: list[dict[str, Any]] = []

    @property
    def attempt(self) -> int:
        return self._attempt

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def retry_history(self) -> list[dict[str, Any]]:
        return list(self._retry_history)

    def should_retry(self, error: str) -> bool:
        if self._attempt >= self._policy.max_retries:
            return False
        reason = self._classify_error(error)
        return reason.value in self._policy.retryable_errors

    def _classify_error(self, error: str) -> RetryReason:
        error_lower = error.lower()
        if "timeout" in error_lower:
            return RetryReason.TIMEOUT
        if "rate limit" in error_lower or "429" in error_lower:
            return RetryReason.RATE_LIMIT
        if "500" in error_lower or "503" in error_lower:
            return RetryReason.SERVER_ERROR
        if "provider" in error_lower or "api" in error_lower:
            return RetryReason.PROVIDER_ERROR
        if "json" in error_lower or "parse" in error_lower or "malformed" in error_lower:
            return RetryReason.MALFORMED_RESPONSE
        if "valid" in error_lower or "schema" in error_lower:
            return RetryReason.VALIDATION_FAILED
        return RetryReason.UNKNOWN

    async def execute_with_retry(
        self,
        func: Callable[..., Coroutine[Any, Any, tuple[bool, Any, str | None]]],
        *args: Any,
        on_retry: Callable[[int, str], Coroutine[Any, Any, None]] | None = None,
        **kwargs: Any,
    ) -> tuple[bool, Any, str | None]:
        self._attempt = 0
        self._retry_history = []

        while self._attempt <= self._policy.max_retries:
            self._attempt += 1
            try:
                success, result, error = await func(*args, **kwargs)
            except Exception as e:
                success, result, error = False, None, str(e)

            self._retry_history.append({
                "attempt": self._attempt,
                "success": success,
                "error": error,
            })

            if success:
                return True, result, None

            self._last_error = error

            if self._attempt > self._policy.max_retries:
                logger.warning(
                    "All %d retries exhausted for %s: %s",
                    self._policy.max_retries, func.__name__, error,
                )
                return False, None, error

            if not self.should_retry(error or ""):
                logger.warning(
                    "Non-retryable error on attempt %d: %s",
                    self._attempt, error,
                )
                return False, None, error

            delay = self._backoff.delay(self._attempt)
            logger.info(
                "Retry %d/%d for %s after %.1fms: %s",
                self._attempt, self._policy.max_retries,
                func.__name__, delay, error,
            )

            if on_retry:
                await on_retry(self._attempt, error or "")

            await asyncio.sleep(delay / 1000.0)

        return False, None, self._last_error
