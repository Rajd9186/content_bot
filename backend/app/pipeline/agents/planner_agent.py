from __future__ import annotations

from typing import Any, Optional

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState


class PlannerAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("planner")

    async def execute(
        self,
        state: PipelineState,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_plan(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": output.get("title", ""),
        "sections": output.get("sections", []),
        "goals": output.get("goals", ""),
        "target_audience": output.get("target_audience", ""),
        "key_themes": output.get("key_themes", []),
        "research_questions": output.get("research_questions", []),
        "success_criteria": output.get("success_criteria", []),
        "estimated_word_count": output.get("estimated_word_count", 0),
    }
