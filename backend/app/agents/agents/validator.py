from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.contracts import (
    AgentContract,
    AgentInput,
    AgentOutput,
    RetryPolicy,
    TimeoutPolicy,
    ValidationResult,
)
from app.agents.prompt.engine import PromptContext
from app.agents.registry import agent_registry


class ValidationIssue(BaseModel):
    severity: str
    location: str
    description: str
    recommendation: str


class ValidationOutput(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    passes: bool
    sections: list[dict[str, Any]]
    issues: list[ValidationIssue]


class ValidatorAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: str | None = None,
    ) -> None:
        contract = AgentContract(
            name="validator",
            description="Content quality validation agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=120000),
            required_capabilities=["validation", "quality_assurance"],
            dependencies=["writer"],
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
        template_kwargs = {
            "content": kwargs.get("content", ""),
            "brief": kwargs.get("brief", kwargs.get("content_plan", "")),
        }
        return await self._prompt_engine.build(
            agent_type="validator",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> dict[str, Any] | None:
        return self._parse_json_output(content)

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        if "overall_score" not in data:
            errors.append("Missing overall_score")
        if "passes" not in data:
            errors.append("Missing pass/fail determination")
        score = data.get("overall_score", 0)
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            errors.append(f"Invalid score: {score}")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(ValidatorAgent)
