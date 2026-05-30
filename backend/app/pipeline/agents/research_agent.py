from __future__ import annotations

import logging
from typing import Any, Optional

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState

logger = logging.getLogger(__name__)


class ResearchAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("research")

    async def execute(
        self,
        state: PipelineState,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_research_data(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": output.get("summary", "Research completed."),
        "key_points": output.get("key_points", []),
        "statistics": output.get("statistics", []),
        "citations": output.get("citations", []),
        "entities": output.get("entities", []),
        "risks": output.get("risks", []),
        "outline_suggestions": output.get("outline_suggestions", []),
        "gaps": output.get("gaps", []),
        "contradictions": output.get("contradictions", []),
    }
