from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.pipeline.state import (
    NodeResult,
    NodeStatus,
    PipelineState,
)
from app.api.v1.endpoints.pipeline_api import _memory_fallback, _save_state, _load_state


class TestPipelineAPIMemoryFallback:
    async def test_save_and_load_state(self) -> None:
        state = PipelineState(
            workflow_id="test-mem-1",
            topic="Memory Fallback Test",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        result = await _save_state(state, db=None)
        assert result is False

        loaded = await _load_state("test-mem-1", db=None)
        assert loaded is not None
        assert loaded.workflow_id == "test-mem-1"
        assert loaded.topic == "Memory Fallback Test"

        _memory_fallback.pop("test-mem-1", None)

    async def test_load_nonexistent(self) -> None:
        loaded = await _load_state("nonexistent-mem", db=None)
        assert loaded is None

    async def test_save_overwrites_existing(self) -> None:
        state1 = PipelineState(
            workflow_id="test-overwrite",
            topic="Original",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        await _save_state(state1, db=None)

        state2 = PipelineState(
            workflow_id="test-overwrite",
            topic="Updated",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        await _save_state(state2, db=None)

        loaded = await _load_state("test-overwrite", db=None)
        assert loaded.topic == "Updated"

        _memory_fallback.pop("test-overwrite", None)

    async def test_save_with_db_failure(self) -> None:
        mock_db = AsyncMock()
        mock_uow = MagicMock()
        mock_uow.pipelines.save_pipeline_state = AsyncMock(side_effect=Exception("DB down"))
        mock_uow.rollback = AsyncMock()

        state = PipelineState(
            workflow_id="test-db-fail",
            topic="DB Fail Test",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        with patch("app.api.v1.endpoints.pipeline_api.UnitOfWork", return_value=mock_uow):
            result = await _save_state(state, db=mock_db)
            assert result is False
            loaded = await _load_state("test-db-fail", db=None)
            assert loaded is not None
            assert loaded.topic == "DB Fail Test"

        _memory_fallback.pop("test-db-fail", None)

    async def test_load_with_db_failure(self) -> None:
        mock_db = AsyncMock()
        state = PipelineState(
            workflow_id="test-load-db-fail",
            topic="Load DB Fail",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        await _save_state(state, db=None)

        mock_uow = MagicMock()
        mock_uow.pipelines.get_by_workflow_id = AsyncMock(side_effect=Exception("DB down"))

        with patch("app.api.v1.endpoints.pipeline_api.UnitOfWork", return_value=mock_uow):
            loaded = await _load_state("test-load-db-fail", db=mock_db)
            assert loaded is not None
            assert loaded.topic == "Load DB Fail"

        _memory_fallback.pop("test-load-db-fail", None)


class TestPipelineStateResponse:
    def test_state_to_response_structure(self) -> None:
        from app.api.v1.endpoints.pipeline_api import _state_to_response

        state = PipelineState(
            workflow_id="resp-test-1",
            workspace_id="ws-1",
            topic="Response Structure",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        response = _state_to_response(state)
        assert "workflow_id" in response
        assert "workspace_id" in response
        assert "topic" in response
        assert "status" in response
        assert "nodes" in response
        assert "error_count" in response
        assert response["workflow_id"] == "resp-test-1"

    def test_state_to_response_with_results(self) -> None:
        from app.api.v1.endpoints.pipeline_api import _state_to_response

        state = PipelineState(
            workflow_id="resp-test-2",
            topic="With Results",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        state.add_node_result(
            "research",
            NodeResult(
                node="research",
                status=NodeStatus.SUCCESS,
                output={"summary": "Found data"},
                tokens_used=500,
                latency_ms=1200,
            ),
        )

        response = _state_to_response(state)
        assert "research" in response["nodes"]
        assert response["nodes"]["research"]["status"] == "success"
        assert response["nodes"]["research"]["tokens_used"] == 500
