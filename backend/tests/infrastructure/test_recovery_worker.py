from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.workers.recovery_worker import RecoveryService, PipelineRecoveryWorker


@pytest.fixture
def recovery() -> RecoveryService:
    return RecoveryService()


class TestRecoveryService:
    async def test_recover_on_startup_db_unavailable(self, recovery: RecoveryService) -> None:
        with patch("app.infrastructure.workers.recovery_worker.async_session_factory", side_effect=RuntimeError("No DB")):
            result = await recovery.recover_on_startup()
            assert result == 0

    async def test_detect_and_recover_zombies_db_unavailable(self, recovery: RecoveryService) -> None:
        with patch("app.infrastructure.workers.recovery_worker.async_session_factory", side_effect=RuntimeError("No DB")):
            result = await recovery.detect_and_recover_zombies()
            assert result == 0

    async def test_recover_on_startup_with_active_pipelines(self, recovery: RecoveryService) -> None:
        mock_pipeline_run = MagicMock()
        mock_pipeline_run.workflow_id = "wf-recover-1"
        mock_pipeline_run.status = "running"
        mock_pipeline_run.current_node = "research"

        mock_uow = MagicMock()
        mock_uow.pipelines.get_active_pipelines = AsyncMock(return_value=[mock_pipeline_run])
        mock_uow.pipelines.to_pipeline_state = MagicMock()
        mock_uow.pipelines.update_status = AsyncMock()
        mock_uow.commit = AsyncMock()
        mock_uow.rollback = AsyncMock()

        mock_state = MagicMock()
        mock_state.has_failures.return_value = False
        mock_state.all_nodes_completed.return_value = False
        mock_uow.pipelines.to_pipeline_state.return_value = mock_state

        mock_session = AsyncMock()

        with patch("app.infrastructure.workers.recovery_worker.async_session_factory") as mock_sf:
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)
            with patch("app.infrastructure.workers.recovery_worker.UnitOfWork", return_value=mock_uow):
                with patch("app.infrastructure.workers.recovery_worker.redis_client") as mock_redis:
                    mock_redis._client = MagicMock()
                    with patch("app.infrastructure.workers.pipeline_worker.pipeline_worker") as mock_pw:
                        mock_pw.enqueue = AsyncMock()
                        result = await recovery.recover_on_startup()
                        assert result == 1

    async def test_detect_zombies_with_stale_runs(self, recovery: RecoveryService) -> None:
        mock_zombie = MagicMock()
        mock_zombie.workflow_id = "wf-zombie-1"
        mock_zombie.heartbeat_at = None

        mock_uow = MagicMock()
        mock_uow.pipelines.get_zombie_pipelines = AsyncMock(return_value=[mock_zombie])
        mock_uow.pipelines.update_status = AsyncMock()
        mock_uow.commit = AsyncMock()
        mock_uow.rollback = AsyncMock()

        mock_session = AsyncMock()

        with patch("app.infrastructure.workers.recovery_worker.async_session_factory") as mock_sf:
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)
            with patch("app.infrastructure.workers.recovery_worker.UnitOfWork", return_value=mock_uow):
                with patch("app.infrastructure.workers.recovery_worker.redis_client") as mock_redis:
                    mock_redis._client = None
                    result = await recovery.detect_and_recover_zombies()
                    assert result == 1


class TestPipelineRecoveryWorker:
    def test_init(self) -> None:
        worker = PipelineRecoveryWorker()
        assert worker._running is False

    async def test_start_and_stop(self) -> None:
        worker = PipelineRecoveryWorker()
        with patch.object(worker, "_loop", new_callable=AsyncMock):
            await worker.start()
            assert worker._running is True
            await worker.stop()
            assert worker._running is False

    async def test_stop_when_not_running(self) -> None:
        worker = PipelineRecoveryWorker()
        await worker.stop()
        assert worker._running is False
