from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.skills import (
    ProjectSkill,
    Skill,
    SkillAgentTarget,
    SkillAnalytics,
    SkillConflict,
    SkillTemplate,
    SkillVersion,
)

logger = logging.getLogger(__name__)

CATEGORIES = frozenset({
    "writing", "research", "seo", "fact_check", "compliance",
    "brand_voice", "youtube", "finance", "custom",
})


class SkillRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_skill(self, name: str, content_markdown: str, category: str,
                           description: str | None = None,
                           created_by: str | None = None,
                           agent_targets: list[str] | None = None) -> Skill:
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        skill = Skill(
            name=name,
            description=description,
            content_markdown=content_markdown,
            category=category,
            created_by=created_by,
        )
        self._session.add(skill)
        await self._session.flush()

        if agent_targets:
            for agent_name in agent_targets:
                self._session.add(SkillAgentTarget(skill_id=skill.id, agent_name=agent_name))
            await self._session.flush()

        self._session.add(SkillAnalytics(skill_id=skill.id))
        await self._session.flush()
        return skill

    async def get_skill(self, skill_id: str) -> Skill | None:
        return await self._session.get(Skill, skill_id)

    async def list_skills(self, category: str | None = None,
                          active_only: bool = True) -> list[Skill]:
        stmt = select(Skill).order_by(Skill.name)
        if active_only:
            stmt = stmt.where(Skill.active.is_(True))
        if category:
            stmt = stmt.where(Skill.category == category)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_skill(self, skill_id: str, updates: dict[str, Any]) -> Skill | None:
        skill = await self._session.get(Skill, skill_id)
        if not skill:
            return None

        old_markdown = skill.content_markdown
        for key, value in updates.items():
            if key == "agent_targets":
                continue
            if hasattr(skill, key):
                setattr(skill, key, value)

        if "content_markdown" in updates and updates["content_markdown"] != old_markdown:
            version = skill.version + 1
            skill.version = version
            sv = SkillVersion(
                skill_id=skill.id,
                version=version,
                content_markdown=updates["content_markdown"],
                created_by=updates.get("created_by"),
            )
            self._session.add(sv)

        if "agent_targets" in updates and updates["agent_targets"] is not None:
            delete_stmt = delete(SkillAgentTarget).where(
                SkillAgentTarget.skill_id == skill_id
            )
            await self._session.execute(delete_stmt)
            for agent_name in updates["agent_targets"]:
                self._session.add(SkillAgentTarget(skill_id=skill_id, agent_name=agent_name))

        skill.updated_at = datetime.utcnow()
        return skill

    async def delete_skill(self, skill_id: str) -> bool:
        skill = await self._session.get(Skill, skill_id)
        if not skill:
            return False
        await self._session.delete(skill)
        return True

    async def get_agent_targets(self, skill_id: str) -> list[str]:
        stmt = select(SkillAgentTarget.agent_name).where(
            SkillAgentTarget.skill_id == skill_id
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_versions(self, skill_id: str) -> list[SkillVersion]:
        stmt = (
            select(SkillVersion)
            .where(SkillVersion.skill_id == skill_id)
            .order_by(SkillVersion.version.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def rollback_skill(self, skill_id: str, version: int) -> Skill | None:
        sv_stmt = select(SkillVersion).where(
            SkillVersion.skill_id == skill_id,
            SkillVersion.version == version,
        )
        sv_result = await self._session.execute(sv_stmt)
        sv = sv_result.scalar_one_or_none()
        if not sv:
            return None

        skill = await self._session.get(Skill, skill_id)
        if not skill:
            return None

        skill.content_markdown = sv.content_markdown
        skill.version = version
        return skill

    async def assign_to_project(self, project_id: str, skill_id: str,
                                priority: int = 0) -> ProjectSkill:
        ps = ProjectSkill(project_id=project_id, skill_id=skill_id, priority=priority)
        self._session.add(ps)
        await self._session.flush()
        return ps

    async def remove_from_project(self, project_id: str, skill_id: str) -> bool:
        stmt = delete(ProjectSkill).where(
            ProjectSkill.project_id == project_id,
            ProjectSkill.skill_id == skill_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_project_skills(self, project_id: str,
                                 enabled_only: bool = True) -> list[dict[str, Any]]:
        stmt = (
            select(ProjectSkill, Skill.name, Skill.category)
            .join(Skill, ProjectSkill.skill_id == Skill.id)
            .where(ProjectSkill.project_id == project_id)
            .order_by(ProjectSkill.priority.desc())
        )
        if enabled_only:
            stmt = stmt.where(ProjectSkill.enabled.is_(True))
        result = await self._session.execute(stmt)
        rows = []
        for ps, name, category in result.all():
            rows.append({
                "id": ps.id,
                "project_id": ps.project_id,
                "skill_id": ps.skill_id,
                "skill_name": name,
                "skill_category": category,
                "priority": ps.priority,
                "enabled": ps.enabled,
            })
        return rows

    async def update_project_skill_priority(self, project_id: str, skill_id: str,
                                            priority: int) -> bool:
        stmt = (
            update(ProjectSkill)
            .where(
                ProjectSkill.project_id == project_id,
                ProjectSkill.skill_id == skill_id,
            )
            .values(priority=priority)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def set_project_skill_enabled(self, project_id: str, skill_id: str,
                                        enabled: bool) -> bool:
        stmt = (
            update(ProjectSkill)
            .where(
                ProjectSkill.project_id == project_id,
                ProjectSkill.skill_id == skill_id,
            )
            .values(enabled=enabled)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def log_conflict(self, workflow_execution_id: str | None,
                           skill_a: str, skill_b: str,
                           resolution: str | None = None) -> SkillConflict:
        conflict = SkillConflict(
            workflow_execution_id=workflow_execution_id,
            skill_a=skill_a,
            skill_b=skill_b,
            resolution=resolution,
        )
        self._session.add(conflict)
        await self._session.flush()
        return conflict

    async def get_conflicts(self, limit: int = 50) -> list[SkillConflict]:
        stmt = select(SkillConflict).order_by(SkillConflict.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_analytics(self, skill_id: str) -> SkillAnalytics | None:
        stmt = select(SkillAnalytics).where(SkillAnalytics.skill_id == skill_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def record_usage(self, skill_id: str, compliance_score: float | None = None,
                           rating: float | None = None) -> None:
        stmt = select(SkillAnalytics).where(SkillAnalytics.skill_id == skill_id)
        result = await self._session.execute(stmt)
        analytics = result.scalar_one_or_none()
        if analytics:
            old_total = analytics.average_compliance * analytics.usage_count
            analytics.usage_count += 1
            if compliance_score is not None:
                analytics.average_compliance = (
                    (old_total + compliance_score) / analytics.usage_count
                )
            if rating is not None:
                old_rating_total = analytics.average_rating * (analytics.usage_count - 1)
                analytics.average_rating = (old_rating_total + rating) / analytics.usage_count
            analytics.last_used = datetime.utcnow()

    async def list_templates(self, category: str | None = None) -> list[SkillTemplate]:
        stmt = select(SkillTemplate).order_by(SkillTemplate.downloads.desc())
        if category:
            stmt = stmt.where(SkillTemplate.category == category)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_template(self, name: str, category: str, content_markdown: str,
                              description: str | None = None,
                              author: str | None = None) -> SkillTemplate:
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        tpl = SkillTemplate(
            name=name, category=category, description=description,
            content_markdown=content_markdown, author=author,
        )
        self._session.add(tpl)
        await self._session.flush()
        return tpl

    async def clone_skill_to_template(self, skill_id: str) -> SkillTemplate | None:
        skill = await self._session.get(Skill, skill_id)
        if not skill:
            return None
        return await self.create_template(
            name=f"{skill.name} (Template)",
            category=skill.category,
            content_markdown=skill.content_markdown,
            description=skill.description,
        )
