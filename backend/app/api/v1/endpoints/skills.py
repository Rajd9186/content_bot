from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.skills.repository import SkillRepository
from app.infrastructure.database import get_db
from app.schemas.skills import (
    ProjectSkillAssign,
    ProjectSkillResponse,
    SkillAnalyticsResponse,
    SkillCreate,
    SkillResponse,
    SkillTemplateResponse,
    SkillTestRequest,
    SkillTestResult,
    SkillUpdate,
    SkillVersionResponse,
)
from app.services.skill_analytics_service import SkillAnalyticsService
from app.services.skill_testing import SkillTestingSandbox

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skills"])


@router.post(
    "/skills",
    response_model=SkillResponse,
    summary="Create a new skill",
    operation_id="createSkill",
    status_code=status.HTTP_201_CREATED,
)
async def create_skill(
    body: SkillCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    try:
        skill = await repo.create_skill(
            name=body.name,
            content_markdown=body.content_markdown,
            category=body.category,
            description=body.description,
            created_by=body.created_by,
            agent_targets=body.agent_targets,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    targets = await repo.get_agent_targets(skill.id)
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content_markdown=skill.content_markdown,
        category=skill.category,
        version=skill.version,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        created_by=skill.created_by,
        active=skill.active,
        agent_targets=targets,
    )


@router.get(
    "/skills",
    response_model=list[SkillResponse],
    summary="List all skills",
    operation_id="listSkills",
)
async def list_skills(
    category: str | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    skills = await repo.list_skills(category=category, active_only=active_only)
    result = []
    for skill in skills:
        targets = await repo.get_agent_targets(skill.id)
        result.append(SkillResponse(
            id=skill.id,
            name=skill.name,
            description=skill.description,
            content_markdown=skill.content_markdown,
            category=skill.category,
            version=skill.version,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
            created_by=skill.created_by,
            active=skill.active,
            agent_targets=targets,
        ))
    return result


@router.get(
    "/skills/{skill_id}",
    response_model=SkillResponse,
    summary="Get skill details",
    operation_id="getSkill",
)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    skill = await repo.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    targets = await repo.get_agent_targets(skill.id)
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content_markdown=skill.content_markdown,
        category=skill.category,
        version=skill.version,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        created_by=skill.created_by,
        active=skill.active,
        agent_targets=targets,
    )


@router.put(
    "/skills/{skill_id}",
    response_model=SkillResponse,
    summary="Update a skill",
    operation_id="updateSkill",
)
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    skill = await repo.update_skill(skill_id, updates)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    targets = await repo.get_agent_targets(skill.id)
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content_markdown=skill.content_markdown,
        category=skill.category,
        version=skill.version,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        created_by=skill.created_by,
        active=skill.active,
        agent_targets=targets,
    )


@router.delete(
    "/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a skill",
    operation_id="deleteSkill",
)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = SkillRepository(db)
    deleted = await repo.delete_skill(skill_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")


@router.get(
    "/skills/{skill_id}/versions",
    response_model=list[SkillVersionResponse],
    summary="Get skill version history",
    operation_id="getSkillVersions",
)
async def get_versions(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    versions = await repo.get_versions(skill_id)
    return [
        SkillVersionResponse(
            id=v.id,
            skill_id=v.skill_id,
            version=v.version,
            content_markdown=v.content_markdown,
            created_at=v.created_at,
            created_by=v.created_by,
        )
        for v in versions
    ]


@router.post(
    "/skills/{skill_id}/rollback",
    response_model=SkillResponse,
    summary="Rollback skill to a previous version",
    operation_id="rollbackSkill",
)
async def rollback(
    skill_id: str,
    version: int = Query(..., description="Version number to rollback to"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    skill = await repo.rollback_skill(skill_id, version)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill or version not found",
        )
    targets = await repo.get_agent_targets(skill.id)
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content_markdown=skill.content_markdown,
        category=skill.category,
        version=skill.version,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        created_by=skill.created_by,
        active=skill.active,
        agent_targets=targets,
    )


@router.get(
    "/projects/{project_id}/skills",
    response_model=list[ProjectSkillResponse],
    summary="Get skills assigned to a project",
    operation_id="getProjectSkills",
)
async def get_project_skills(
    project_id: str,
    enabled_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    rows = await repo.get_project_skills(project_id, enabled_only=enabled_only)
    return [
        ProjectSkillResponse(
            id=r["id"],
            project_id=r["project_id"],
            skill_id=r["skill_id"],
            skill_name=r["skill_name"],
            skill_category=r["skill_category"],
            priority=r["priority"],
            enabled=r["enabled"],
        )
        for r in rows
    ]


@router.post(
    "/projects/{project_id}/skills",
    response_model=ProjectSkillResponse,
    summary="Assign a skill to a project",
    operation_id="assignProjectSkill",
    status_code=status.HTTP_201_CREATED,
)
async def assign_skill(
    project_id: str,
    body: ProjectSkillAssign,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    skill = await repo.get_skill(body.skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    ps = await repo.assign_to_project(project_id, body.skill_id, body.priority)
    return ProjectSkillResponse(
        id=ps.id,
        project_id=ps.project_id,
        skill_id=ps.skill_id,
        skill_name=skill.name,
        skill_category=skill.category,
        priority=ps.priority,
        enabled=ps.enabled,
    )


@router.delete(
    "/projects/{project_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Remove a skill from a project",
    operation_id="removeProjectSkill",
)
async def remove_project_skill(
    project_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = SkillRepository(db)
    removed = await repo.remove_from_project(project_id, skill_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project skill not found")


@router.put(
    "/projects/{project_id}/skills/{skill_id}",
    response_model=ProjectSkillResponse,
    summary="Update project skill priority or enabled status",
    operation_id="updateProjectSkill",
)
async def update_project_skill(
    project_id: str,
    skill_id: str,
    priority: int | None = Query(None),
    enabled: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    if priority is not None:
        updated = await repo.update_project_skill_priority(project_id, skill_id, priority)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project skill not found")
    if enabled is not None:
        updated = await repo.set_project_skill_enabled(project_id, skill_id, enabled)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project skill not found")

    rows = await repo.get_project_skills(project_id)
    for r in rows:
        if r["skill_id"] == skill_id:
            return ProjectSkillResponse(
                id=r["id"],
                project_id=r["project_id"],
                skill_id=r["skill_id"],
                skill_name=r["skill_name"],
                skill_category=r["skill_category"],
                priority=r["priority"],
                enabled=r["enabled"],
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project skill not found")


@router.post(
    "/skills/test",
    response_model=SkillTestResult,
    summary="Test a skill against a prompt",
    operation_id="testSkill",
)
async def test_skill(
    body: SkillTestRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    sandbox = SkillTestingSandbox()
    result = await sandbox.run_comparison(body.prompt, body.skill_id, db)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    without = result.get("without_skill", {})
    with_ = result.get("with_skill", {})
    diffs = result.get("differences", {})
    compliance = result.get("compliance", {})
    return SkillTestResult(
        prompt=body.prompt,
        without_skill=without.get("output", ""),
        with_skill=with_.get("output", ""),
        compliance_score=compliance.get("compliance_score", 0.0),
        readability_diff=diffs.get("readability_diff", 0.0),
        seo_diff=diffs.get("seo_diff", 0.0),
        style_diff=diffs.get("style_diff", 0.0),
    )


@router.get(
    "/skills/{skill_id}/analytics",
    response_model=SkillAnalyticsResponse,
    summary="Get analytics for a skill",
    operation_id="getSkillAnalytics",
)
async def get_analytics(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = SkillAnalyticsService(db)
    stats = await service.get_skill_stats(skill_id)
    return SkillAnalyticsResponse(
        skill_id=stats["skill_id"],
        usage_count=stats["usage_count"],
        average_compliance=stats["average_compliance"],
        average_rating=stats["average_rating"],
        last_used=stats["last_used"],
    )


@router.get(
    "/skills/analytics/top",
    response_model=list[SkillAnalyticsResponse],
    summary="Get top skills by usage",
    operation_id="getTopSkills",
)
async def get_top_skills(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = SkillAnalyticsService(db)
    top = await service.get_top_skills(limit=limit)
    return [
        SkillAnalyticsResponse(
            skill_id=s["skill_id"],
            usage_count=s["usage_count"],
            average_compliance=s["average_compliance"],
            average_rating=s["average_rating"],
        )
        for s in top
    ]


@router.get(
    "/workflows/{workflow_id}/compliance",
    summary="Get compliance evaluation for a workflow (deprecated)",
    operation_id="getWorkflowCompliance",
)
async def get_workflow_compliance(
    workflow_id: str,
) -> Any:
    return {"status": "not_implemented"}


@router.get(
    "/skills/templates",
    response_model=list[SkillTemplateResponse],
    summary="List skill templates",
    operation_id="listSkillTemplates",
)
async def list_templates(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    templates = await repo.list_templates(category=category)
    return [
        SkillTemplateResponse(
            id=t.id,
            name=t.name,
            category=t.category,
            description=t.description,
            content_markdown=t.content_markdown,
            author=t.author,
            downloads=t.downloads,
            created_at=t.created_at,
        )
        for t in templates
    ]


@router.post(
    "/skills/templates",
    response_model=SkillTemplateResponse,
    summary="Create a skill template",
    operation_id="createSkillTemplate",
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    body: SkillCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    try:
        tpl = await repo.create_template(
            name=body.name,
            category=body.category,
            content_markdown=body.content_markdown,
            description=body.description,
            author=body.created_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return SkillTemplateResponse(
        id=tpl.id,
        name=tpl.name,
        category=tpl.category,
        description=tpl.description,
        content_markdown=tpl.content_markdown,
        author=tpl.author,
        downloads=tpl.downloads,
        created_at=tpl.created_at,
    )


@router.post(
    "/skills/{skill_id}/clone-template",
    response_model=SkillTemplateResponse,
    summary="Clone a skill to a template",
    operation_id="cloneSkillToTemplate",
    status_code=status.HTTP_201_CREATED,
)
async def clone_to_template(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SkillRepository(db)
    tpl = await repo.clone_skill_to_template(skill_id)
    if not tpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return SkillTemplateResponse(
        id=tpl.id,
        name=tpl.name,
        category=tpl.category,
        description=tpl.description,
        content_markdown=tpl.content_markdown,
        author=tpl.author,
        downloads=tpl.downloads,
        created_at=tpl.created_at,
    )
