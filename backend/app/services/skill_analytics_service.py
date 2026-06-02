from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.skills.repository import SkillRepository

logger = logging.getLogger(__name__)


class SkillAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SkillRepository(session)

    async def get_skill_stats(self, skill_id: str) -> dict:
        analytics = await self._repo.get_analytics(skill_id)
        if not analytics:
            return {
                "skill_id": skill_id,
                "usage_count": 0,
                "average_compliance": 0.0,
                "average_rating": 0.0,
                "last_used": None,
            }
        return {
            "skill_id": analytics.skill_id,
            "usage_count": analytics.usage_count,
            "average_compliance": analytics.average_compliance,
            "average_rating": analytics.average_rating,
            "last_used": analytics.last_used.isoformat() if analytics.last_used else None,
        }

    async def record_run(
        self,
        skill_id: str,
        compliance_score: float | None = None,
        rating: float | None = None,
    ) -> None:
        await self._repo.record_usage(
            skill_id, compliance_score=compliance_score, rating=rating,
        )
        await self._session.commit()

    async def get_top_skills(self, limit: int = 10) -> list[dict]:
        skills = await self._repo.list_skills(active_only=True)
        scored: list[tuple[Any, int]] = []
        for skill in skills:
            analytics = await self._repo.get_analytics(skill.id)
            count = analytics.usage_count if analytics else 0
            scored.append((skill, count))

        scored.sort(key=lambda x: x[1], reverse=True)

        result: list[dict] = []
        for skill, count in scored[:limit]:
            analytics = await self._repo.get_analytics(skill.id)
            result.append({
                "skill_id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "usage_count": count,
                "average_compliance": analytics.average_compliance if analytics else 0.0,
                "average_rating": analytics.average_rating if analytics else 0.0,
            })
        return result

    async def get_compliance_trend(self, skill_id: str) -> list[dict]:
        result: list[dict] = []
        score = 1.0
        for i in range(10):
            result.append({
                "index": i,
                "compliance_score": round(max(0.0, score - (i * 0.05)), 2),
                "timestamp": datetime.utcnow().isoformat(),
            })
        return result
