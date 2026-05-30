from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.workers.pipeline_worker import PipelineWorker, PIPELINE_QUEUE


@pytest.fixture
def worker() -> PipelineWorker:
    return PipelineWorker()


class TestPipelineWorker:
    def test_init_defaults(self, worker: PipelineWorker) -> None:
        assert worker._running is False
        assert worker._pipeline is not None
        assert worker.active_count == 0
        assert worker.is_running is False

    async def test_start_without_redis(self, worker: PipelineWorker) -> None:
        with patch("app.infrastructure.workers.pipeline_worker.redis_client") as mock_redis:
            mock_redis._client = None
            await worker.start()
            assert worker._running is False

    async def test_start_with_redis(self, worker: PipelineWorker) -> None:
        with patch("app.infrastructure.workers.pipeline_worker.redis_client") as mock_redis:
            mock_redis._client = MagicMock()
            await worker.start()
            assert worker._running is True
            await worker.stop()
            assert worker._running is False

    async def test_stop_when_not_running(self, worker: PipelineWorker) -> None:
        await worker.stop()
        assert worker._running is False

    async def test_enqueue_calls_redis(self, worker: PipelineWorker) -> None:
        with patch("app.infrastructure.workers.pipeline_worker.redis_client") as mock_redis:
            mock_redis._client = MagicMock()
            mock_redis.queue_push_json = AsyncMock()
            await worker.enqueue("wf-enqueue-1", skip_human_review=True)
            mock_redis.queue_push_json.assert_called_once()
            call_args = mock_redis.queue_push_json.call_args
            assert call_args[0][0] == PIPELINE_QUEUE
            job = call_args[0][1]
            assert job["workflow_id"] == "wf-enqueue-1"
            assert job["skip_human_review"] is True

    async def test_enqueue_without_redis_raises(self, worker: PipelineWorker) -> None:
        with patch("app.infrastructure.workers.pipeline_worker.redis_client") as mock_redis:
            mock_redis._client = None
            mock_redis.queue_push_json = AsyncMock(side_effect=RuntimeError("No Redis"))
            with pytest.raises(RuntimeError):
                await worker.enqueue("wf-no-redis")

    async def test_active_count_zero_initially(self, worker: PipelineWorker) -> None:
        assert worker.active_count == 0

    async def test_stop_cancels_active_tasks(self, worker: PipelineWorker) -> None:
        with patch("app.infrastructure.workers.pipeline_worker.redis_client") as mock_redis:
            mock_redis._client = MagicMock()
            await worker.start()
            await worker.stop()
            assert len(worker._active_executions) == 0
