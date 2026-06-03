from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.project.repository import ProjectRepository

logger = logging.getLogger(__name__)


class SourceGovernanceEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)

    async def apply_governance(
        self, project_id: str, sources: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Filters and ranks sources based on project governance policies.
        Returns: (filtered_sources, governance_report)
        """
        policy = await self._repo.get_source_policy(project_id)
        if not policy or not policy.enabled:
            return sources, {"status": "disabled"}

        prefs = await self._repo.get_research_preferences(project_id)
        if not prefs:
            prefs = {"freshness_mode": "evergreen", "trust_threshold": 0, "latest_only": False}
        else:
            # Convert model to dict for easier access
            prefs = {
                "freshness_mode": prefs.freshness_mode,
                "trust_threshold": prefs.trust_threshold,
                "latest_only": prefs.latest_only,
                "allow_competitor_content": prefs.allow_competitor_content,
            }

        allowed = await self._repo.get_allowed_sources(project_id)
        blocked = await self._repo.get_blocked_sources(project_id)

        allowed_domains = {s.source_domain.lower() for s in allowed if s.source_domain}
        blocked_domains = {s.source_domain.lower() for s in blocked if s.source_domain}
        blocked_names = {s.source_name.lower() for s in blocked}

        filtered_sources = []
        report = {
            "allowed_sources_used": [],
            "blocked_sources_removed": [],
            "freshness_mode": prefs["freshness_mode"],
            "trust_threshold": prefs["trust_threshold"],
        }

        for source in sources:
            name = source.get("name", "").lower()
            domain = source.get("domain", "").lower()
            trust_score = source.get("trust_score", 100)
            published_at = source.get("published_at")

            # 1. Blocked Sources Filter
            if name in blocked_names or domain in blocked_domains:
                report["blocked_sources_removed"].append(source.get("name", "Unknown"))
                continue

            # 2. Allowed Sources Priority (if list is not empty, we prioritize them)
            is_allowed = name in {s.source_name.lower() for s in allowed} or domain in allowed_domains
            if is_allowed:
                report["allowed_sources_used"].append(source.get("name", "Unknown"))

            # 3. Trust Threshold Filter
            if trust_score < prefs["trust_threshold"]:
                continue

            # 4. Freshness Filter
            if published_at:
                pub_date = datetime.fromisoformat(published_at) if isinstance(published_at, str) else published_at
                if not self._is_fresh(pub_date, prefs["freshness_mode"], prefs["latest_only"]):
                    continue

            filtered_sources.append(source)

        # Final Ranking: prioritize allowed sources and newer ones
        def ranking_key(s):
            score = 0
            # Prioritize allowed sources
            if s.get("name", "").lower() in {asource.source_name.lower() for asource in allowed}:
                score += 1000
            # Prioritize freshness
            if s.get("published_at"):
                pub_date = datetime.fromisoformat(s["published_at"]) if isinstance(s["published_at"], str) else s["published_at"]
                score += int(pub_date.timestamp() / 1000000)
            return score

        filtered_sources.sort(key=ranking_key, reverse=True)

        return filtered_sources, report

    def _is_fresh(self, pub_date: datetime, mode: str, latest_only: bool) -> bool:
        now = datetime.now(UTC)
        delta = now - pub_date

        if latest_only:
            # Simplified: latest_only means we prioritize newest, but usually means a strict cutoff
            # For this engine, we'll consider it "Fresh" if it's within 30 days
            return delta.days <= 30

        if mode == "latest_only":
            return delta.days <= 7
        elif mode == "7_days":
            return delta.days <= 7
        elif mode == "30_days":
            return delta.days <= 30
        elif mode == "90_days":
            return delta.days <= 90
        elif mode == "evergreen":
            return True
        
        return True
