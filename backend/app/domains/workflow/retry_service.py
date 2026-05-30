from __future__ import annotations

import logging
import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.infrastructure.models.telemetry import RetryRecord
from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


def full_jitter_delay(attempt: int, base_ms: int = 1000, max_ms: int = 300000) -> float:
    """Exponential backoff with full jitter.
    delay = random_between(0, min(max_ms, base_ms * 2^attempt))
    """
    cap = min(max_ms, base_ms * (2 ** attempt))
    return random.uniform(0, cap)


def equal_jitter_delay(attempt: int, base_ms: int = 1000, max_ms: int = 300000) -> float:
    """Exponential backoff with equal jitter.
    temp = min(max_ms, base_ms * 2^attempt)
    delay = temp/2 + random_between(0, temp/2)
    """
    temp = min(max_ms, base_ms * (2 ** attempt))
    half = temp / 2
    return half + random.uniform(0, half)


class RetryService:
    def __init__(self, strategy: str = "full_jitter") -> None:
        self.strategy = strategy

    def calculate_delay(self, attempt: int, base_ms: int = 1000, max_ms: int = 300000) -> float:
        if self.strategy == "full_jitter":
            return full_jitter_delay(attempt, base_ms, max_ms)
        return equal_jitter_delay(attempt, base_ms, max_ms)

    async def record_attempt(
        self,
        uow: UnitOfWork,
        target_type: str,
        target_id: str,
        attempt_number: int,
        max_retries: int = 3,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> RetryRecord:
        delay_ms = self.calculate_delay(attempt_number)
        scheduled_at = datetime.now(UTC) + timedelta(milliseconds=delay_ms)

        record = RetryRecord(
            id=str(uuid4()),
            target_type=target_type,
            target_id=target_id,
            attempt_number=attempt_number,
            status="scheduled",
            error_code=error_code,
            error_message=error_message,
            scheduled_at=scheduled_at,
        )
        self.session.add(record)
        await self.session.flush()

        logger.info(
            "Retry scheduled: %s/%s attempt=%d delay=%.0fms max=%d",
            target_type, target_id, attempt_number, delay_ms, max_retries,
        )
        return record

    async def record_dead_letter(
        self,
        uow: UnitOfWork,
        original_job_id: str,
        error_code: str,
        error_message: str | None = None,
        retry_attempts: int = 0,
        payload: dict | None = None,
    ) -> None:
        from app.domains.workflow.models import DeadLetterJob

        entry = DeadLetterJob(
            id=str(uuid4()),
            original_job_id=original_job_id,
            error_code=error_code,
            error_message=error_message,
            retry_attempts=retry_attempts,
            payload=payload,
        )
        self.session.add(entry)
        await self.session.flush()

        logger.warning(
            "Dead letter created: job=%s error=%s attempts=%d",
            original_job_id, error_code, retry_attempts,
        )

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value


retry_service = RetryService()
