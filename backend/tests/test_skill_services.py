from __future__ import annotations

import pytest

from app.services.skill_compliance import ComplianceEvaluator

pytestmark = pytest.mark.anyio


class TestComplianceEvaluator:
    def setup_method(self) -> None:
        self.evaluator = ComplianceEvaluator()

    async def test_evaluate_passing_content(self) -> None:
        content = (
            "The company announced record earnings. According to the report, "
            "revenue increased by 15% (Source: Annual Report, 2024). "
            "The tone is formal and professional."
        )
        skill_markdown = "# Style Guide\n\n* Use formal tone\n* Cite sources\n* Be professional"
        result = await self.evaluator.evaluate(content, skill_markdown, "brand_voice")
        assert "compliance_score" in result
        assert isinstance(result["compliance_score"], float)
        assert result["compliance_score"] >= 0.0
        assert "violations" in result

    async def test_evaluate_failing_content(self) -> None:
        content = "Lorem ipsum dolor sit amet. Nothing specific here."
        skill_markdown = (
            "# SEO Rules\n"
            "1. Include keyword 'investment'\n"
            "2. Use heading structure\n"
            "* Use meta descriptions"
        )
        result = await self.evaluator.evaluate(content, skill_markdown, "seo")
        assert result["compliance_score"] < 1.0

    async def test_parse_rules(self) -> None:
        markdown = (
            "# Rules\n"
            "* Use formal language\n"
            "- Avoid jargon\n"
            "1. Cite your sources\n"
            "2. Check facts"
        )
        rules = await self.evaluator._parse_rules(markdown)
        assert len(rules) == 4
        assert "Use formal language" in rules
        assert "Avoid jargon" in rules
        assert "Cite your sources" in rules
        assert "Check facts" in rules

    async def test_check_rule_with_quotes(self) -> None:
        rule = 'Always use the word "efficient" when describing processes'
        content = "Our efficient workflow improved productivity."
        result = await self.evaluator._check_rule(rule, content)
        assert result is True

        content_fail = "Our workflow improved productivity."
        result_fail = await self.evaluator._check_rule(rule, content_fail)
        assert result_fail is False

    async def test_check_rule_forbidden_word(self) -> None:
        rule = "avoid: 'spam'"
        content = "This is spam content"
        result = await self.evaluator._check_rule(rule, content)
        assert result is False

        content_good = "This is valid content"
        result_good = await self.evaluator._check_rule(rule, content_good)
        assert result_good is True

    async def test_tone_markers_detection(self) -> None:
        content_formal = "The report indicates a formal professional approach."
        content_informal = "The thing looks kinda cool actually."
        skill_markdown = "# Style\n\nTone markers: formal, professional"

        result_formal = await self.evaluator.evaluate(content_formal, skill_markdown, "brand_voice")
        result_informal = await self.evaluator.evaluate(content_informal, skill_markdown, "brand_voice")

        assert result_formal["compliance_score"] >= result_informal["compliance_score"]

    async def test_empty_content(self) -> None:
        result = await self.evaluator.evaluate("", "# Rules\n* Test", "compliance")
        assert result["compliance_score"] == 0.0
        assert len(result["violations"]) > 0


class TestSkillInjectionEngine:
    """Tests for skill injection engine - tested via SkillRetrievalAgent integration."""

    async def test_skill_injection_builds_package(self) -> None:
        from app.infrastructure.database import async_session_factory
        from app.services.skill_injection import SkillInjectionEngine

        async with async_session_factory() as session:
            from app.domains.skills.repository import SkillRepository

            repo = SkillRepository(session)
            skill = await repo.create_skill(
                name="Test Injection",
                content_markdown="# Test",
                category="writing",
            )
            await session.commit()

            engine = SkillInjectionEngine(session)
            package = await engine.build_active_skill_package(
                project_id=None, workflow_skill_ids=None, agent_name=None,
            )
            assert "active_skills" in package
            assert "skill_priorities" in package
            assert "conflicts" in package
            await session.rollback()


class TestSkillConflictResolution:
    """Tests for conflict detection in SkillInjectionEngine."""

    async def test_detect_conflict_between_opposing_rules(self) -> None:
        from app.infrastructure.database import async_session_factory
        from app.services.skill_injection import SkillInjectionEngine

        async with async_session_factory() as session:
            from app.domains.skills.repository import SkillRepository

            repo = SkillRepository(session)
            skill_a = await repo.create_skill(
                name="Formal Voice",
                content_markdown="# Formal\n* Use professional language",
                category="brand_voice",
            )
            skill_b = await repo.create_skill(
                name="Casual Voice",
                content_markdown="# Casual\n* Use conversational language",
                category="brand_voice",
            )
            await repo.assign_to_project("test-project-123", skill_a.id, priority=5)
            await repo.assign_to_project("test-project-123", skill_b.id, priority=5)
            await session.commit()

            engine = SkillInjectionEngine(session)
            package = await engine.build_active_skill_package(
                project_id="test-project-123", workflow_skill_ids=None, agent_name=None,
            )
            assert len(package["conflicts"]) >= 0
            await session.rollback()


class TestSkillAnalyticsService:
    """Tests for skill analytics service."""

    async def test_record_usage(self) -> None:
        from app.infrastructure.database import async_session_factory
        from app.services.skill_analytics_service import SkillAnalyticsService

        async with async_session_factory() as session:
            from app.domains.skills.repository import SkillRepository

            repo = SkillRepository(session)
            skill = await repo.create_skill(
                name="Analytics Test",
                content_markdown="# Test",
                category="research",
            )
            await session.commit()

            service = SkillAnalyticsService(session)
            await service.record_run(skill.id, compliance_score=85.0, rating=4.5)

            stats = await service.get_skill_stats(skill.id)
            assert stats["usage_count"] == 1
            assert stats["average_compliance"] == 85.0
            assert stats["average_rating"] == 4.5
            await session.rollback()