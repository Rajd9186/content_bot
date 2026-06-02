from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.skills.models import Skill
from app.domains.skills.repository import SkillRepository

logger = logging.getLogger(__name__)


class SkillInjectionEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SkillRepository(session)

    async def build_active_skill_package(
        self,
        project_id: str | None = None,
        workflow_skill_ids: list[str] | None = None,
        agent_name: str | None = None,
    ) -> dict:
        active_skills: list[dict[str, Any]] = []
        priorities: dict[str, int] = {}
        seen: set[str] = set()

        if project_id:
            project_skills = await self._repo.get_project_skills(project_id, enabled_only=True)
            for ps in project_skills:
                sid = ps["skill_id"]
                if sid not in seen:
                    seen.add(sid)
                    skill = await self._repo.get_skill(sid)
                    if skill and skill.active:
                        active_skills.append({
                            "id": skill.id,
                            "name": skill.name,
                            "category": skill.category,
                            "content_markdown": skill.content_markdown,
                        })
                        priorities[sid] = ps["priority"]

        if workflow_skill_ids:
            for sid in workflow_skill_ids:
                if sid not in seen:
                    seen.add(sid)
                    skill = await self._repo.get_skill(sid)
                    if skill and skill.active:
                        active_skills.append({
                            "id": skill.id,
                            "name": skill.name,
                            "category": skill.category,
                            "content_markdown": skill.content_markdown,
                        })
                        priorities[sid] = 0

        global_skills = await self._repo.list_skills(active_only=True)
        for skill in global_skills:
            if skill.id not in seen:
                seen.add(skill.id)
                active_skills.append({
                    "id": skill.id,
                    "name": skill.name,
                    "category": skill.category,
                    "content_markdown": skill.content_markdown,
                })
                priorities[skill.id] = -1

        if agent_name:
            filtered: list[dict[str, Any]] = []
            for entry in active_skills:
                targets = await self._repo.get_agent_targets(entry["id"])
                if not targets or agent_name in targets:
                    filtered.append(entry)
            active_skills = filtered

        conflicts = await self._resolve_conflicts(
            [
                Skill(
                    id=s["id"],
                    name=s["name"],
                    category=s["category"],
                    content_markdown=s["content_markdown"],
                )
                for s in active_skills
            ],
            priorities,
        )

        return {
            "active_skills": active_skills,
            "skill_priorities": priorities,
            "conflicts": conflicts,
        }

    async def _resolve_conflicts(
        self, skills: list[Skill], priorities: dict[str, int]
    ) -> list[dict]:
        conflicts: list[dict] = []
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                a, b = skills[i], skills[j]
                targets_a = await self._repo.get_agent_targets(a.id)
                targets_b = await self._repo.get_agent_targets(b.id)
                overlapping = set(targets_a) & set(targets_b)
                if overlapping or (not targets_a and not targets_b):
                    pa = priorities.get(a.id, 0)
                    pb = priorities.get(b.id, 0)
                    if pa == pb:
                        winner = a.id if a.id < b.id else b.id
                        resolution = f"Priority tie ({pa}). Selected skill {winner} by deterministic tie-break."
                    else:
                        winner = a.id if pa > pb else b.id
                        resolution = f"Skill {winner} wins with priority {max(pa, pb)}."
                    await self._repo.log_conflict(
                        workflow_execution_id=None,
                        skill_a=a.id,
                        skill_b=b.id,
                        resolution=resolution,
                    )
                    conflicts.append({
                        "skill_a": a.id,
                        "skill_b": b.id,
                        "resolution": resolution,
                    })
        return conflicts

    async def inject_skills_into_prompt(
        self, system_prompt: str, active_package: dict, agent_name: str
    ) -> str:
        skill_blocks: list[str] = [system_prompt]
        for entry in active_package.get("active_skills", []):
            targets = await self._repo.get_agent_targets(entry["id"])
            if targets and agent_name not in targets:
                continue
            skill_blocks.append(
                f"=== Skill: {entry['name']} ({entry['category']}) ===\n{entry['content_markdown']}"
            )
        return "\n\n".join(skill_blocks)

    async def get_skills_for_agent(
        self, project_id: str | None, agent_name: str
    ) -> list[dict]:
        package = await self.build_active_skill_package(
            project_id=project_id, agent_name=agent_name,
        )
        result: list[dict] = []
        for entry in package["active_skills"]:
            targets = await self._repo.get_agent_targets(entry["id"])
            if not targets or agent_name in targets:
                result.append({
                    "name": entry["name"],
                    "category": entry["category"],
                    "content_markdown": entry["content_markdown"],
                })
        return result
