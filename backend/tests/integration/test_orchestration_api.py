from __future__ import annotations

from httpx import AsyncClient

API_PREFIX = "/api/v1/orchestration"


class TestOrchestrationAPI:
    async def test_create_workflow(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["workspace_id"] == "ws-1"
        assert body["correlation_id"] == "corr-1"
        assert body["status"] == "running"
        assert body["current_stage"] == "INIT"
        assert body["version"] == 1
        assert "id" in body

    async def test_create_workflow_validates_input(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows",
            params={"workspace_id": "", "correlation_id": "corr-1"},
        )
        assert response.status_code == 400

    async def test_run_workflow(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows/test-run-1/run",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["current_stage"] == "PUBLISHED"
        assert body["stage_count"] == len([
            "INIT", "PLANNING", "RESEARCH", "SYNTHESIS",
            "OUTLINING", "WRITING", "VALIDATION", "SEO",
            "FACT_CHECK", "FINALIZATION", "PUBLISHED",
        ])

    async def test_run_workflow_with_content_item(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows/test-run-2/run",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
                "content_item_id": "item-1",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"

    async def test_resume_workflow(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows/test-resume-1/resume",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
                "current_stage": "VALIDATION",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["current_stage"] == "PUBLISHED"

    async def test_resume_workflow_invalid_stage(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows/test-resume-2/resume",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
                "current_stage": "INVALID",
            },
        )
        assert response.status_code == 422

    async def test_cancel_workflow(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows/test-cancel-1/cancel",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
                "reason": "user_requested",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "cancelled"
        assert body["error"] == "user_requested"

    async def test_cancel_workflow_response_structure(self, client: AsyncClient) -> None:
        response = await client.post(
            f"{API_PREFIX}/workflows/test-cancel-2/cancel",
            params={
                "workspace_id": "ws-1",
                "correlation_id": "corr-1",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "id" in body
        assert body["status"] == "cancelled"
        assert "version" in body

    async def test_get_workflow(self, client: AsyncClient) -> None:
        response = await client.get(f"{API_PREFIX}/workflows/test-get-1")
        assert response.status_code == 200

    async def test_get_completed_stages(self, client: AsyncClient) -> None:
        response = await client.get(f"{API_PREFIX}/workflows/test-stages-1/stages")
        assert response.status_code == 200
