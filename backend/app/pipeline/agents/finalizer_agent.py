from __future__ import annotations

from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState


class FinalizerAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("finalizer")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_finalizer_output(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "final_content": output.get("final_content", ""),
        "title": output.get("title", ""),
        "excerpt": output.get("excerpt", ""),
        "word_count": output.get("word_count", 0),
        "reading_time_minutes": output.get("reading_time_minutes", 0),
        "metadata": output.get("metadata", {}),
        "citations_list": output.get("citations_list", []),
        "change_log": output.get("change_log", []),
    }
