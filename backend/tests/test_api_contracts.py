from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestApiRootRoutes:
    async def test_get_api_root(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1")
        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "AI Content Intelligence Platform"
        assert body["version"] == "1.0.0"
        assert "endpoints" in body
        assert "docs" in body

    async def test_get_api_info(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/info")
        assert response.status_code == 200
        body = response.json()
        assert "service" in body
        assert "version" in body
        assert "environment" in body
        assert "debug" in body

    async def test_get_api_version(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/version")
        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "1.0.0"
        assert body["service"] == "AI Content Intelligence Platform"


class TestHealthEndpoints:
    async def test_liveness(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["version"] == "1.0.0"
        assert "uptimeSeconds" in body

    async def test_readiness(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert "checks" in body


class TestMetricsEndpoints:
    async def test_prometheus_metrics(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "app_uptime_seconds" in response.text

    async def test_json_metrics(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/metrics/json")
        assert response.status_code == 200
        body = response.json()
        assert "counters" in body
        assert "gauges" in body
        assert "histogram_counts" in body


class TestPipelineEndpoints:
    async def test_start_pipeline(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/start",
            params={"topic": "AI in Healthcare"},
        )
        assert response.status_code == 201
        body = response.json()
        assert "workflow_id" in body
        assert body["status"] == "created"
        assert body["topic"] == "AI in Healthcare"

    async def test_start_pipeline_missing_topic(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/start",
        )
        assert response.status_code == 422

    async def test_start_pipeline_short_topic(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/start",
            params={"topic": "AB"},
        )
        assert response.status_code == 422

    async def test_get_pipeline_status_not_found(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/content-pipeline/pipeline/nonexistent-id",
        )
        assert response.status_code == 404

    async def test_run_pipeline_not_found(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/nonexistent-id/run",
        )
        assert response.status_code == 404

    async def test_cancel_pipeline_not_found(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/nonexistent-id/cancel",
        )
        assert response.status_code == 404

    async def test_pipeline_content_not_found(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/content-pipeline/pipeline/nonexistent-id/content",
        )
        assert response.status_code == 404

    async def test_pipeline_timeline_not_found(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/content-pipeline/pipeline/nonexistent-id/timeline",
        )
        assert response.status_code == 404

    async def test_pipeline_events_not_found(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/content-pipeline/pipeline/nonexistent-id/events",
        )
        assert response.status_code == 404

    async def test_review_not_found(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/nonexistent-id/review",
            params={"action": "approved"},
        )
        assert response.status_code == 404


class TestContractValidation:
    async def test_health_response_schema(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        body = response.json()
        assert isinstance(body["status"], str)
        assert isinstance(body["version"], str)
        assert isinstance(body["uptimeSeconds"], (int, float))

    async def test_readiness_response_schema(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/ready")
        body = response.json()
        assert isinstance(body["status"], str)
        assert isinstance(body["checks"], dict)

    async def test_api_root_schema(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1")
        body = response.json()
        assert isinstance(body["service"], str)
        assert isinstance(body["version"], str)
        assert isinstance(body["endpoints"], list)
        assert isinstance(body["docs"], str)

    async def test_start_pipeline_response_schema(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/content-pipeline/pipeline/start",
            params={"topic": "Test Topic"},
        )
        body = response.json()
        assert isinstance(body["workflow_id"], str)
        assert isinstance(body["correlation_id"], str)
        assert isinstance(body["topic"], str)
        assert isinstance(body["status"], str)

    async def test_404_response_format(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/content-pipeline/pipeline/nonexistent")
        assert response.status_code == 404
        body = response.json()
        assert "detail" in body

    async def test_cors_headers(self, client: AsyncClient) -> None:
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
