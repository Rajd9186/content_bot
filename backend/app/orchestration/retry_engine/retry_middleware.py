from __future__ import annotations

import asyncio
import time
from typing import Optional, Callable, Awaitable, TypeVar
from dataclasses import dataclass, field

from app.log_config.logger import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retryable_exceptions: tuple = (Exception,)
    jitter: bool = True


@dataclass
class RetryAttempt:
    attempt: int
    error: str
    duration_ms: float
    recovered: bool = False


@dataclass
class RetryResult:
    success: bool
    result: Optional[T] = None
    error: Optional[str] = None
    attempts: list[RetryAttempt] = field(default_factory=list)
    total_duration_ms: float = 0.0


async def execute_with_retry(
    func: Callable[..., Awaitable[T]],
    *args,
    config: RetryConfig = RetryConfig(),
    **kwargs,
) -> RetryResult:
    attempts: list[RetryAttempt] = []
    start = time.monotonic()

    for attempt in range(1, config.max_retries + 2):
        attempt_start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            duration = (time.monotonic() - attempt_start) * 1000
            attempts.append(RetryAttempt(attempt=attempt, error="", duration_ms=duration, recovered=False))
            total_duration = (time.monotonic() - start) * 1000
            return RetryResult(success=True, result=result, attempts=attempts, total_duration_ms=total_duration)
        except config.retryable_exceptions as e:
            duration = (time.monotonic() - attempt_start) * 1000
            error = f"{type(e).__name__}: {str(e)[:200]}"
            attempts.append(RetryAttempt(attempt=attempt, error=error, duration_ms=duration))

            if attempt <= config.max_retries:
                delay = min(config.base_delay * (config.backoff_factor ** (attempt - 1)), config.max_delay)
                if config.jitter:
                    import random
                    delay = delay * (0.5 + random.random())
                logger.warning(
                    "Retry %d/%d after error: %s (waiting %.1fs)",
                    attempt, config.max_retries, error, delay,
                )
                await asyncio.sleep(delay)
            else:
                total_duration = (time.monotonic() - start) * 1000
                return RetryResult(success=False, error=error, attempts=attempts, total_duration_ms=total_duration)

    total_duration = (time.monotonic() - start) * 1000
    return RetryResult(success=False, error="Exhausted retries", attempts=attempts, total_duration_ms=total_duration)


def async_retry(config: Optional[RetryConfig] = None):
    cfg = config or RetryConfig()

    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await execute_with_retry(func, *args, config=cfg, **kwargs)
            if not result.success:
                raise RuntimeError(f"All retries exhausted: {result.error}")
            return result.result
        return wrapper
    return decorator
