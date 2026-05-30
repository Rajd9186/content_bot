from __future__ import annotations

from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState


class SEOAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("seo")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_seo_output(output: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    content = output.get("content", "")
    metadata = {
        "title": output.get("title", ""),
        "meta_description": output.get("meta_description", ""),
        "url_slug": output.get("url_slug", ""),
        "primary_keywords": output.get("primary_keywords", []),
        "secondary_keywords": output.get("secondary_keywords", []),
        "heading_suggestions": output.get("heading_suggestions", []),
        "internal_links": output.get("internal_links", []),
        "external_links": output.get("external_links", []),
        "readability_score": output.get("readability_score", 0),
        "word_count_target": output.get("word_count_target", 0),
    }
    return content, metadata
