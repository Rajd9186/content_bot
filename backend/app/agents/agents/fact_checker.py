from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.contracts import (
    AgentContract, AgentInput, AgentOutput, RetryPolicy, TimeoutPolicy, ValidationResult,
)
from app.agents.prompt.engine import PromptContext
from app.agents.registry import agent_registry


class ClaimResult(BaseModel):
    claim: str
    status: str
    evidence: str
    suggested_correction: Optional[str] = None
    confidence: str


class FactCheckSummary(BaseModel):
    total_claims: int
    verified: int
    unverified: int
    questionable: int
    false: int


class FactCheckOutput(BaseModel):
    claims: list[ClaimResult]
    summary: FactCheckSummary
    overall_assessment: str


class FactCheckerAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: Optional[str] = None,
    ) -> None:
        contract = AgentContract(
            name="fact_checker",
            description="Fact-checking and verification agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=180000),
            required_capabilities=["fact_checking", "verification"],
            dependencies=["writer", "researcher"],
        )
        super().__init__(contract, provider_name, model)

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        if not kwargs.get("content"):
            return ValidationResult(
                valid=False, errors=["Missing required: content"],
            )
        return ValidationResult(valid=True)

    async def _build_prompt(self, agent_input: AgentInput) -> PromptContext:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        research = kwargs.get("research_sources", "")
        if isinstance(research, list):
            research = "\n".join(f"- {r}" for r in research)
        elif isinstance(research, dict):
            parts = []
            for k, v in research.items():
                parts.append(f"- {k}: {v}")
            research = "\n".join(parts)

        template_kwargs = {
            "content": kwargs.get("content", ""),
            "research_sources": research or "No specific sources provided",
        }
        return await self._prompt_engine.build(
            agent_type="fact_checker",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> Optional[dict[str, Any]]:
        return self._parse_json_output(content)

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        if data.get("claims") is None:
            errors.append("Missing claims analysis")
        summary = data.get("summary")
        if summary is None:
            errors.append("Missing fact-check summary")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(FactCheckerAgent)
