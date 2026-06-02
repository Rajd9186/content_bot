from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_create_skill(client: AsyncClient) -> None:
    response = await client.post(
        "/api/skills",
        json={
            "name": "Reuters Style",
            "description": "News writing standards",
            "content_markdown": "# Reuters Style\n\n* Neutral tone\n* Cite sources\n* Avoid sensationalism",
            "category": "writing",
            "agent_targets": ["writer_agent", "research_agent"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Reuters Style"
    assert data["category"] == "writing"
    assert data["version"] == 1
    assert data["active"] is True
    assert data["agent_targets"] == ["writer_agent", "research_agent"]
    assert "id" in data


async def test_create_skill_invalid_category(client: AsyncClient) -> None:
    response = await client.post(
        "/api/skills",
        json={
            "name": "Bad Skill",
            "content_markdown": "# Bad\n\nContent",
            "category": "invalid_category",
        },
    )
    assert response.status_code in (400, 422)


async def test_list_skills(client: AsyncClient) -> None:
    await client.post(
        "/api/skills",
        json={
            "name": "Test Skill 1",
            "content_markdown": "# Test\n\nContent",
            "category": "writing",
        },
    )
    await client.post(
        "/api/skills",
        json={
            "name": "Test Skill 2",
            "content_markdown": "# Test\n\nSEO Content",
            "category": "seo",
        },
    )
    response = await client.get("/api/skills")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


async def test_list_skills_by_category(client: AsyncClient) -> None:
    await client.post(
        "/api/skills",
        json={"name": "SEO Skill", "content_markdown": "# SEO", "category": "seo"},
    )
    response = await client.get("/api/skills?category=seo")
    assert response.status_code == 200
    data = response.json()
    assert all(s["category"] == "seo" for s in data)


async def test_get_skill(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={"name": "Get Test", "content_markdown": "# Get", "category": "research"},
    )
    skill_id = create_resp.json()["id"]
    response = await client.get(f"/api/skills/{skill_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == skill_id
    assert data["name"] == "Get Test"


async def test_get_skill_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/skills/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_update_skill(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={"name": "Original", "content_markdown": "# Original", "category": "writing"},
    )
    skill_id = create_resp.json()["id"]
    response = await client.put(
        f"/api/skills/{skill_id}",
        json={"name": "Updated", "content_markdown": "# Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["version"] == 2


async def test_delete_skill(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={"name": "Delete Me", "content_markdown": "# Delete", "category": "custom"},
    )
    skill_id = create_resp.json()["id"]
    response = await client.delete(f"/api/skills/{skill_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/api/skills/{skill_id}")
    assert get_resp.status_code == 404


async def test_skill_versions(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={"name": "Version Test", "content_markdown": "# V1", "category": "writing"},
    )
    skill_id = create_resp.json()["id"]
    await client.put(
        f"/api/skills/{skill_id}",
        json={"content_markdown": "# V2 - Updated content"},
    )
    response = await client.get(f"/api/skills/{skill_id}/versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 2
    assert versions[1]["version"] == 1


async def test_rollback_skill(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={"name": "Rollback Test", "content_markdown": "# V1", "category": "seo"},
    )
    skill_id = create_resp.json()["id"]
    await client.put(
        f"/api/skills/{skill_id}",
        json={"content_markdown": "# V2 - Changed"},
    )
    response = await client.post(f"/api/skills/{skill_id}/rollback?version=1")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1


async def test_skill_test_endpoint(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={
            "name": "Test Skill",
            "content_markdown": "# Test\n\nUse formal language\nAvoid jargon",
            "category": "brand_voice",
        },
    )
    skill_id = create_resp.json()["id"]
    response = await client.post(
        "/api/skills/test",
        json={"prompt": "Write a formal introduction", "skill_id": skill_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "without_skill" in data
    assert "with_skill" in data
    assert "compliance_score" in data


async def test_skill_analytics(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/skills",
        json={"name": "Analytics Skill", "content_markdown": "# Test", "category": "fact_check"},
    )
    skill_id = create_resp.json()["id"]
    response = await client.get(f"/api/skills/{skill_id}/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "usage_count" in data
    assert data["skill_id"] == skill_id


async def test_top_skills(client: AsyncClient) -> None:
    await client.post(
        "/api/skills",
        json={"name": "Top Skill 1", "content_markdown": "# Test", "category": "finance"},
    )
    response = await client.get("/api/skills/analytics/top")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_skill_templates(client: AsyncClient) -> None:
    response = await client.get("/api/skills/templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    create_resp = await client.post(
        "/api/skills",
        json={"name": "Template Source", "content_markdown": "# Source", "category": "youtube"},
    )
    skill_id = create_resp.json()["id"]
    clone_resp = await client.post(f"/api/skills/{skill_id}/clone-template")
    assert clone_resp.status_code == 201