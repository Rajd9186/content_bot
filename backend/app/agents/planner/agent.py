from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_inputs.planner import PlannerInput
from app.schemas.agent_outputs.planner import PlannerOutput
from app.prompts.builders.planner_prompts import build_planner_system_prompt, build_planner_user_prompt
from app.log_config.logger import get_logger

logger = get_logger(__name__)


class PlannerAgent(BaseAgent[PlannerInput, PlannerOutput]):
    def system_prompt(self) -> str:
        return build_planner_system_prompt()

    def user_prompt(self, input_data: PlannerInput) -> str:
        return build_planner_user_prompt(input_data)

    def parse_response(self, response: str, input_data: PlannerInput) -> PlannerOutput:
        try:
            result = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Planner LLM response not valid JSON, using fallback")
            return self._fallback(input_data)

        sections = result.get("outline", {}).get("sections", [])
        if not sections:
            logger.warning("Planner returned no sections, using fallback")
            return self._fallback(input_data)

        research_tasks = []
        for s in sections:
            research_tasks.extend(s.get("research_queries", []))
        if not research_tasks:
            research_tasks = [
                f"{input_data.topic} current state",
                f"{input_data.topic} statistics and data",
                f"{input_data.topic} trusted sources",
            ]

        return PlannerOutput(
            outline=result.get("outline", {}),
            sections=sections,
            research_tasks=research_tasks,
            target_keywords=result.get("target_keywords", input_data.seo_keywords),
            suggested_sources=result.get("suggested_sources", []),
        )

    def _fallback(self, input_data: PlannerInput) -> PlannerOutput:
        topic = input_data.topic
        section = {
            "heading": f"Introduction to {topic}",
            "key_points": [f"Overview of {topic}", f"Current landscape", f"Key developments"],
            "research_queries": [
                f"{topic} overview",
                f"{topic} latest research",
                f"{topic} key trends 2026",
            ],
            "word_count_target": 400,
        }
        return PlannerOutput(
            outline={"sections": [section], "estimated_total_words": 1500},
            sections=[section],
            research_tasks=[
                f"{topic} overview",
                f"{topic} latest research",
                f"{topic} key trends 2026",
            ],
            target_keywords=input_data.seo_keywords or [topic],
            suggested_sources=["academic sources", "industry reports", "news articles"],
        )

    async def run(self, input_data: PlannerInput) -> PlannerOutput:
        system = self.system_prompt()
        user = self.user_prompt(input_data)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            llm_response = await self.call_llm(messages)
            return self.parse_response(llm_response.content, input_data)
        except Exception as e:
            logger.warning("Planner LLM call failed, using fallback", extra={"error": str(e)[:200]})
            return self._fallback(input_data)
