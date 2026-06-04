"""API endpoint integration tests."""

import uuid

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_health_contains_status(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data


class TestProjectsEndpoint:
    async def test_create_project(self, client: AsyncClient, sample_project_data):
        response = await client.post(
            "/api/v1/projects",
            json=sample_project_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == sample_project_data["topic"]
        assert "id" in data

    async def test_create_project_quick(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/projects/quick",
            json={"topic": "Machine Learning Trends"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "Machine Learning Trends"
        assert "id" in data

    async def test_list_projects_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_projects_with_data(
        self, client: AsyncClient, sample_project_data
    ):
        await client.post("/api/v1/projects", json=sample_project_data)
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_get_nonexistent_project(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/projects/{fake_id}")
        assert response.status_code == 404

    async def test_delete_project(
        self, client: AsyncClient, sample_project_data
    ):
        create_resp = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204

    async def test_create_project_validates_topic_required(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/api/v1/projects",
            json={"title": "No topic"},
        )
        assert response.status_code == 422


class TestOpenAPI:
    async def test_openapi_schema_valid(self, client: AsyncClient):
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/projects" in schema["paths"]


class TestWorkflowEvents:
    async def test_sse_workflow_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/workflows/{fake_id}/stream")
        assert response.status_code == 404

    async def test_events_endpoint(self, client: AsyncClient, sample_project_data):
        # Create a project first
        proj_resp = await client.post("/api/v1/projects", json=sample_project_data)
        project_id = proj_resp.json()["id"]

        # Query events for the project
        response = await client.get(f"/api/v1/projects/{project_id}/chat/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
