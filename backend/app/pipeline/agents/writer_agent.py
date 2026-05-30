from __future__ import annotations

from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState


class WriterAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("writer")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_writer_output(output: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    content = output.get("content", "")
    metadata = {
        "title": output.get("title", ""),
        "word_count": output.get("word_count", 0),
        "sections_written": output.get("sections_written", []),
        "citations_used": output.get("citations_used", []),
    }
    return content, metadata
