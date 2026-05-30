from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.pipeline.graph import WorkflowPipeline
from app.pipeline.state import NodeResult, NodeStatus, PipelineState


@pytest.fixture
def pipeline() -> WorkflowPipeline:
    return WorkflowPipeline()


@pytest.fixture
def sample_state() -> PipelineState:
    return PipelineState(
        workflow_id="test-123",
        topic="Artificial Intelligence",
        research_data={},
        plan={},
        outline={},
    )


async def _mock_agent_success(
    _state: PipelineState,
    provider_override=None,
    model_override=None,
) -> NodeResult:
    return NodeResult(
        node="research",
        status=NodeStatus.SUCCESS,
        output={"summary": "Research complete", "key_points": ["AI is evolving"]},
    )


async def _mock_agent_failure(
    _state: PipelineState,
    provider_override=None,
    model_override=None,
) -> NodeResult:
    return NodeResult(
        node="research",
        status=NodeStatus.FAILED,
        error="Agent execution failed",
    )


@pytest.mark.asyncio
async def test_pipeline_full_execution(pipeline, sample_state) -> None:
    with (
        patch.object(pipeline._research_agent, "execute", _mock_agent_success),
        patch.object(pipeline._planner_agent, "execute", _mock_agent_success),
        patch.object(pipeline._writer_agent, "execute", _mock_agent_success),
        patch.object(pipeline._seo_agent, "execute", _mock_agent_success),
        patch.object(pipeline._fact_checker_agent, "execute", _mock_agent_success),
        patch.object(pipeline._compliance_agent, "execute", _mock_agent_success),
        patch.object(pipeline._finalizer_agent, "execute", _mock_agent_success),
    ):
        result = await pipeline.execute(sample_state, skip_human_review=True)

        assert result.all_nodes_completed() is True
        assert result.has_failures() is False
        assert "research" in result.node_results
        assert "planner" in result.node_results
        assert "writer" in result.node_results
        assert "seo" in result.node_results
        assert "fact_checker" in result.node_results
        assert "compliance" in result.node_results
        assert "finalizer" in result.node_results


@pytest.mark.asyncio
async def test_pipeline_stops_on_failure(pipeline, sample_state) -> None:
    with (
        patch.object(pipeline._research_agent, "execute", _mock_agent_failure),
        patch.object(pipeline._planner_agent, "execute", _mock_agent_success),
        patch.object(pipeline._writer_agent, "execute", _mock_agent_success),
        patch.object(pipeline._seo_agent, "execute", _mock_agent_success),
        patch.object(pipeline._fact_checker_agent, "execute", _mock_agent_success),
        patch.object(pipeline._compliance_agent, "execute", _mock_agent_success),
        patch.object(pipeline._finalizer_agent, "execute", _mock_agent_success),
    ):
        result = await pipeline.execute(sample_state, skip_human_review=True)

        assert result.has_failures() is True
        assert result.node_results["research"].status == NodeStatus.FAILED
        assert "planner" not in result.node_results


@pytest.mark.asyncio
async def test_pipeline_with_human_review(pipeline, sample_state) -> None:
    with (
        patch.object(pipeline._research_agent, "execute", _mock_agent_success),
        patch.object(pipeline._planner_agent, "execute", _mock_agent_success),
        patch.object(pipeline._writer_agent, "execute", _mock_agent_success),
        patch.object(pipeline._seo_agent, "execute", _mock_agent_success),
        patch.object(pipeline._fact_checker_agent, "execute", _mock_agent_success),
        patch.object(pipeline._compliance_agent, "execute", _mock_agent_success),
        patch.object(pipeline._finalizer_agent, "execute", _mock_agent_success),
    ):
        result = await pipeline.execute(sample_state, skip_human_review=False)
        assert "human_review" in result.node_results
        assert result.node_results["human_review"].status == NodeStatus.SUCCESS


@pytest.mark.asyncio
async def test_pipeline_progress_callbacks(pipeline, sample_state) -> None:
    callback_results: list[tuple[str, NodeResult]] = []

    def on_progress(node: str, result: NodeResult) -> None:
        callback_results.append((node, result))

    pipeline.on_progress(on_progress)

    with (
        patch.object(pipeline._research_agent, "execute", _mock_agent_success),
        patch.object(pipeline._planner_agent, "execute", _mock_agent_success),
        patch.object(pipeline._writer_agent, "execute", _mock_agent_success),
        patch.object(pipeline._seo_agent, "execute", _mock_agent_success),
        patch.object(pipeline._fact_checker_agent, "execute", _mock_agent_success),
        patch.object(pipeline._compliance_agent, "execute", _mock_agent_success),
        patch.object(pipeline._finalizer_agent, "execute", _mock_agent_success),
    ):
        await pipeline.execute(sample_state, skip_human_review=True)
        assert len(callback_results) == 7  # 7 nodes executed
        nodes_called = [n for n, _ in callback_results]
        expected = ["research", "planner", "writer", "seo", "fact_checker", "compliance", "finalizer"]
        assert nodes_called == expected
