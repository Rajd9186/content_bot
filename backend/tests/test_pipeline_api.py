from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.pipeline.state import NodeResult, NodeStatus, PipelineState


def _make_completed_state(workflow_id: str, topic: str = "Test") -> PipelineState:
    state = PipelineState(workflow_id=workflow_id, topic=topic)
    for node in ["research", "planner", "writer", "seo", "fact_checker", "compliance", "finalizer"]:
        state.add_node_result(
            node,
            NodeResult(
                node=node, status=NodeStatus.SUCCESS,
                output={"summary": "ok"}, tokens_used=100, latency_ms=500,
            ),
        )
    state.final_content = f"# {topic}\n\nGenerated content."
    return state


@pytest.fixture
def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="https://test")


@pytest.mark.asyncio
async def test_pipeline_start_endpoint(client) -> None:
    response = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=Artificial+Intelligence&audience=developers&tone=technical&goals=Explain+AI+concepts",
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "workflow_id" in data
    assert data["topic"] == "Artificial Intelligence"
    assert data["status"] == "created"


@pytest.mark.asyncio
async def test_pipeline_run_endpoint(client) -> None:
    start_resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=AI+Research&audience=developers",
    )
    workflow_id = start_resp.json()["workflow_id"]

    with patch("app.api.v1.endpoints.pipeline_api.pipeline.execute") as mock_exec:
        mock_exec.return_value = _make_completed_state(workflow_id, "AI Research")
        run_resp = await client.post(
            f"/api/v1/content-pipeline/pipeline/{workflow_id}/run",
        )
    assert run_resp.status_code in (200, 202)
    data = run_resp.json()
    assert data["workflow_id"] == workflow_id


@pytest.mark.asyncio
async def test_pipeline_status_endpoint(client) -> None:
    start_resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=Status+Test&audience=general",
    )
    workflow_id = start_resp.json()["workflow_id"]

    status_resp = await client.get(
        f"/api/v1/content-pipeline/pipeline/{workflow_id}"
    )
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["workflow_id"] == workflow_id
    assert data["status"] in ("completed", "running")


@pytest.mark.asyncio
async def test_pipeline_status_not_found(client) -> None:
    resp = await client.get(
        "/api/v1/content-pipeline/pipeline/nonexistent-workflow"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pipeline_cancel_endpoint(client) -> None:
    start_resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=Cancel+Test&audience=general",
    )
    workflow_id = start_resp.json()["workflow_id"]

    cancel_resp = await client.post(
        f"/api/v1/content-pipeline/pipeline/{workflow_id}/cancel"
    )
    assert cancel_resp.status_code == 200
    data = cancel_resp.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_pipeline_content_endpoint(client) -> None:
    start_resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=Content+Test&audience=general",
    )
    workflow_id = start_resp.json()["workflow_id"]

    content_resp = await client.get(
        f"/api/v1/content-pipeline/pipeline/{workflow_id}/content"
    )
    assert content_resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_pipeline_timeline_endpoint(client) -> None:
    start_resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=Timeline+Test&audience=general",
    )
    workflow_id = start_resp.json()["workflow_id"]

    timeline_resp = await client.get(
        f"/api/v1/content-pipeline/pipeline/{workflow_id}/timeline"
    )
    assert timeline_resp.status_code == 200
    data = timeline_resp.json()
    assert "timeline" in data
    assert isinstance(data["timeline"], list)


@pytest.mark.asyncio
async def test_pipeline_cancel_non_existent(client) -> None:
    resp = await client.post(
        "/api/v1/content-pipeline/pipeline/nonexistent/cancel"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pipeline_start_missing_topic(client) -> None:
    resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start",
        json={},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pipeline_review_endpoint(client) -> None:
    start_resp = await client.post(
        "/api/v1/content-pipeline/pipeline/start?topic=Review+Test&audience=general",
    )
    workflow_id = start_resp.json()["workflow_id"]

    with patch("app.api.v1.endpoints.pipeline_api.pipeline.run_finalizer") as mock_final:
        mock_final.return_value = _make_completed_state(workflow_id, "Review Test")
        review_resp = await client.post(
            f"/api/v1/content-pipeline/pipeline/{workflow_id}/review?action=approved&reviewer_id=user-1&comments=Looks+good",
        )
    assert review_resp.status_code in (200, 400, 404)
