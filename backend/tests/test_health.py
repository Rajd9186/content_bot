from __future__ import annotations

from httpx import AsyncClient


class TestHealthEndpoints:
    async def test_liveness(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["version"] == "1.0.0"
        assert "uptimeSeconds" in body

    async def test_readiness_without_db(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert "checks" in body
