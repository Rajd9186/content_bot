from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.skills.repository import SkillRepository
from app.services.skill_compliance import ComplianceEvaluator

logger = logging.getLogger(__name__)


class SkillTestingSandbox:
    async def run_comparison(
        self, prompt: str, skill_id: str, session: AsyncSession,
    ) -> dict[str, Any]:
        repo = SkillRepository(session)
        skill = await repo.get_skill(skill_id)
        if not skill:
            return {"error": f"Skill {skill_id} not found"}

        without_output = prompt
        with_output = f"{skill.content_markdown}\n\n{prompt}"

        evaluator = ComplianceEvaluator()
        compliance = await evaluator.evaluate(
            with_output, skill.content_markdown, skill.category,
        )

        readability_without = self._compute_readability(without_output)
        readability_with = self._compute_readability(with_output)
        seo_without = self._compute_seo_score(without_output)
        seo_with = self._compute_seo_score(with_output)
        style_without = self._compute_style_score(without_output)
        style_with = self._compute_style_score(with_output)

        return {
            "skill_id": skill_id,
            "skill_name": skill.name,
            "skill_category": skill.category,
            "without_skill": {
                "output": without_output,
                "readability": readability_without,
                "seo_score": seo_without,
                "style_score": style_without,
            },
            "with_skill": {
                "output": with_output,
                "readability": readability_with,
                "seo_score": seo_with,
                "style_score": style_with,
            },
            "differences": {
                "readability_diff": round(readability_with - readability_without, 2),
                "seo_diff": round(seo_with - seo_without, 2),
                "style_diff": round(style_with - style_without, 2),
            },
            "compliance": compliance,
        }

    def _compute_readability(self, text: str) -> float:
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.0
        total_words = sum(len(s.split()) for s in sentences)
        avg_sentence_length = total_words / len(sentences)
        score = max(0.0, 100.0 - (avg_sentence_length * 1.5))
        return round(score, 2)

    def _compute_seo_score(self, text: str) -> float:
        score = 0.0

        headings = len(re.findall(r"^#{1,3}\s", text, re.MULTILINE))
        if headings > 0:
            score += 30.0
        if headings >= 2:
            score += 10.0

        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0
        total = len(words)
        unique = len(set(words))
        keyword_density = unique / total if total > 0 else 0
        if 0.3 <= keyword_density <= 0.7:
            score += 30.0
        elif keyword_density > 0.1:
            score += 15.0

        if len(text) >= 300:
            score += 15.0
        if len(text) >= 1000:
            score += 15.0

        return round(min(score, 100.0), 2)

    def _compute_style_score(self, text: str) -> float:
        formal_markers = [
            r"\b(therefore|consequently|furthermore|nevertheless|accordingly)\b",
            r"\b(however|moreover|notably|specifically|particularly)\b",
            r"\b(demonstrate|indicate|establish|determine|conclude)\b",
        ]
        score = 0.0
        for pattern in formal_markers:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            score += min(matches * 10.0, 30.0)

        total_words = len(re.findall(r"\b\w+\b", text))
        avg_word_len = (
            sum(len(w) for w in re.findall(r"\b\w+\b", text)) / total_words
            if total_words > 0
            else 0
        )
        if avg_word_len >= 5:
            score += 20.0
        elif avg_word_len >= 4:
            score += 10.0

        return round(min(score, 100.0), 2)
