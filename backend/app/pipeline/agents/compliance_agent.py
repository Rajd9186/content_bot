from __future__ import annotations

from typing import Any

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.state import NodeResult, PipelineState


class ComplianceAgent(PipelineAgent):
    def __init__(self) -> None:
        super().__init__("compliance")

    async def execute(
        self,
        state: PipelineState,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> NodeResult:
        result = await super().execute(state, provider_override, model_override)
        return result


def extract_compliance_output(output: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    content = output.get("content", "")
    metadata = {
        "compliance_status": output.get("compliance_status", ""),
        "issues": output.get("issues", []),
        "disclaimers_needed": output.get("disclaimers_needed", []),
        "brand_safety_score": output.get("brand_safety_score", 0),
        "regulatory_checks": output.get("regulatory_checks", []),
        "overall_verdict": output.get("overall_verdict", ""),
    }
    return content, metadata
