from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable, Coroutine
from typing import Any

from app.orchestration.stages import (
    WorkflowRun,
    WorkflowStage,
)

logger = logging.getLogger(__name__)

StageExecutor = Callable[
    [WorkflowRun, WorkflowStage, dict[str, Any]],
    Coroutine[Any, Any, dict[str, Any]],
]


def compute_backoff(attempt: int, base_ms: int = 2000, max_ms: int = 60000) -> float:
    """Exponential backoff with full jitter.
    delay = random(0, min(max_ms, base_ms * 2^(attempt-1)))
    """
    cap = min(max_ms, base_ms * (2 ** (attempt - 1)))
    return random.uniform(0, cap)


class StageTimeoutError(Exception):
    pass


class RetryManager:
    """Manages retry-safe execution of workflow stages with timeout and backoff.

    Each stage execution is wrapped in:
    1. Timeout guard (asyncio.wait_for)
    2. Retry loop with exponential backoff + full jitter
    3. Dead-letter detection when max retries exhausted
    """

    def __init__(
        self,
        dead_letter_fn: Callable[[WorkflowRun, WorkflowStage, str, int], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        self._dead_letter_fn = dead_letter_fn

    async def execute_with_retry(
        self,
        stage: WorkflowStage,
        executor: StageExecutor | None,
        run: WorkflowRun,
        context: dict[str, Any],
        max_retries: int = 3,
        timeout_s: int = 120,
    ) -> tuple[bool, dict[str, Any], str | None, int]:
        """Execute a stage with retry logic. Returns (success, output, error, attempts)."""
        last_error: str | None = None
        attempt = 0

        while attempt <= max_retries:
            if attempt > 0:
                delay_s = compute_backoff(attempt) / 1000.0
                logger.info(
                    "Retrying stage %s for workflow %s: attempt %d/%d, delay=%.2fs",
                    stage.value, run.id, attempt, max_retries, delay_s,
                )
                await asyncio.sleep(delay_s)

            attempt += 1
            try:
                if executor is None:
                    return True, {}, None, attempt - 1

                output = await asyncio.wait_for(
                    executor(run, stage, context),
                    timeout=timeout_s,
                )
                return True, output, None, attempt - 1

            except TimeoutError:
                last_error = f"Stage '{stage.value}' timed out after {timeout_s}s"
                logger.warning(
                    "Timeout on stage %s for workflow %s: attempt %d/%d",
                    stage.value, run.id, attempt, max_retries,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Error on stage %s for workflow %s: attempt %d/%d: %s",
                    stage.value, run.id, attempt, max_retries, last_error,
                )

        logger.error(
            "All retries exhausted for stage %s on workflow %s: %s",
            stage.value, run.id, last_error,
        )

        if self._dead_letter_fn:
            await self._dead_letter_fn(run, stage, last_error or "Unknown error", attempt - 1)

        return False, {}, last_error, attempt - 1

    async def execute_with_timeout_only(
        self,
        stage: WorkflowStage,
        executor: StageExecutor,
        run: WorkflowRun,
        context: dict[str, Any],
        timeout_s: int = 120,
    ) -> tuple[bool, dict[str, Any], str | None]:
        """Execute a stage with timeout but no retry."""
        try:
            output = await asyncio.wait_for(
                executor(run, stage, context),
                timeout=timeout_s,
            )
            return True, output, None
        except TimeoutError:
            return False, {}, f"Stage '{stage.value}' timed out after {timeout_s}s"
        except Exception as e:
            return False, {}, str(e)
