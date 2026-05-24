import asyncio
import functools
from typing import Any, Callable

from app.log_config.logger import get_logger


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait = delay * (backoff ** attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}",
                            extra={
                                "error": str(e),
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "wait_seconds": wait,
                            },
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.error(
                            f"All retries exhausted for {func.__name__}",
                            extra={"error": str(e), "max_retries": max_retries},
                        )
                        raise
            raise last_exception
        return wrapper
    return decorator
