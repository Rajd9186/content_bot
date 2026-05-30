from __future__ import annotations

from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState


class FactCheckerAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("fact_checker")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_fact_check_output(output: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    content = output.get("content", "")
    metadata = {
        "verified_claims": output.get("verified_claims", []),
        "unverified_claims": output.get("unverified_claims", []),
        "disputed_claims": output.get("disputed_claims", []),
        "corrections": output.get("corrections", []),
        "overall_assessment": output.get("overall_assessment", ""),
        "confidence_score": output.get("confidence_score", 0.0),
    }
    return content, metadata
