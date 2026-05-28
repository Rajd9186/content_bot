from __future__ import annotations

from typing import Any, Dict

import pytest

from app.orchestration.retry_manager import RetryManager, compute_backoff, StageTimeoutError
from app.orchestration.stages import WorkflowStage, WorkflowRun, WorkflowStatus


class TestComputeBackoff:
    def test_full_jitter_within_bounds(self) -> None:
        for attempt in range(1, 10):
            delay = compute_backoff(attempt, base_ms=1000, max_ms=60000)
            cap = min(60000, 1000 * (2 ** (attempt - 1)))
            assert 0 <= delay <= cap

    def test_backoff_increases_with_attempts(self) -> None:
        max_delays = []
        for attempt in range(1, 8):
            delays = [compute_backoff(attempt) for _ in range(100)]
            max_delays.append(max(delays))
        for i in range(1, len(max_delays)):
            assert max_delays[i] >= max_delays[i - 1] * 0.5

    def test_capped_at_max(self) -> None:
        delay = compute_backoff(20, base_ms=1000, max_ms=5000)
        assert delay <= 5000


class TestRetryManager:
    @pytest.fixture
    def manager(self) -> RetryManager:
        return RetryManager()

    @pytest.fixture
    def run(self) -> WorkflowRun:
        return WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")

    async def test_successful_execution(self, manager: RetryManager, run: WorkflowRun) -> None:
        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        success, output, error, attempts = await manager.execute_with_retry(
            stage=WorkflowStage.PLANNING,
            executor=executor,
            run=run,
            context={},
            max_retries=3,
            timeout_s=30,
        )

        assert success is True
        assert output["result"] == "success"
        assert error is None
        assert attempts == 0

    async def test_retry_on_failure(self, manager: RetryManager, run: WorkflowRun) -> None:
        call_count = 0

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return {"result": "success"}

        success, output, error, attempts = await manager.execute_with_retry(
            stage=WorkflowStage.PLANNING,
            executor=executor,
            run=run,
            context={},
            max_retries=3,
            timeout_s=30,
        )

        assert success is True
        assert output["result"] == "success"
        assert attempts == 2

    async def test_exhaust_retries(self, manager: RetryManager, run: WorkflowRun) -> None:
        call_count = 0

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        success, output, error, attempts = await manager.execute_with_retry(
            stage=WorkflowStage.PLANNING,
            executor=executor,
            run=run,
            context={},
            max_retries=2,
            timeout_s=30,
        )

        assert success is False
        assert error is not None
        assert attempts == 2

    async def test_timeout_triggers_retry(self, manager: RetryManager, run: WorkflowRun) -> None:
        call_count = 0

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            import asyncio
            await asyncio.sleep(10)
            return {"result": "ok"}

        success, output, error, attempts = await manager.execute_with_retry(
            stage=WorkflowStage.PLANNING,
            executor=executor,
            run=run,
            context={},
            max_retries=1,
            timeout_s=0.01,
        )

        assert success is False
        assert "timed out" in (error or "").lower()

    async def test_dead_letter_on_exhaust(self) -> None:
        dead_letter_called = False

        async def dead_letter_fn(run: WorkflowRun, stage: WorkflowStage,
                                 error: str, attempts: int) -> None:
            nonlocal dead_letter_called
            dead_letter_called = True

        manager = RetryManager(dead_letter_fn=dead_letter_fn)

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            raise ValueError("Fatal error")

        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        await manager.execute_with_retry(
            stage=WorkflowStage.WRITING,
            executor=executor,
            run=run,
            context={},
            max_retries=0,
            timeout_s=30,
        )

        assert dead_letter_called is True

    async def test_no_executor_returns_success(self, manager: RetryManager, run: WorkflowRun) -> None:
        success, output, error, attempts = await manager.execute_with_retry(
            stage=WorkflowStage.INIT,
            executor=None,
            run=run,
            context={},
            max_retries=0,
            timeout_s=30,
        )

        assert success is True
        assert output == {}

    async def test_execute_with_timeout_only_success(self, manager: RetryManager, run: WorkflowRun) -> None:
        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "ok"}

        success, output, error = await manager.execute_with_timeout_only(
            stage=WorkflowStage.PLANNING,
            executor=executor,
            run=run,
            context={},
            timeout_s=30,
        )

        assert success is True
        assert output["result"] == "ok"

    async def test_execute_with_timeout_only_failure(self, manager: RetryManager, run: WorkflowRun) -> None:
        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            raise RuntimeError("Boom")

        success, output, error = await manager.execute_with_timeout_only(
            stage=WorkflowStage.PLANNING,
            executor=executor,
            run=run,
            context={},
            timeout_s=30,
        )

        assert success is False
        assert "Boom" in (error or "")
