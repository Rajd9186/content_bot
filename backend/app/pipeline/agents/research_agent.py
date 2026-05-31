from __future__ import annotations

import logging
from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState

logger = logging.getLogger(__name__)


class ResearchAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("research")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        if result.status == NodeStatus.SUCCESS:
            vlog_links = result.output.get("vlog_links", [])
            if isinstance(vlog_links, list):
                state.vlog_links = vlog_links
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
