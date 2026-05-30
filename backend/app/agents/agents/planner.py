from __future__ import annotations

from typing import Any

from pydantic import BaseModel

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


class PlanOutput(BaseModel):
    title: str
    goals: str
    audience: str
    themes: list[str]
    research_questions: list[str]
    suggested_structure: list[str]
    success_criteria: list[str] | None = None


class PlannerAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: str | None = None,
    ) -> None:
        contract = AgentContract(
            name="planner",
            description="Content planning and strategy agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=120000),
            required_capabilities=["planning", "strategy"],
        )
        super().__init__(contract, provider_name, model)

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        if not kwargs.get("topic"):
            return ValidationResult(
                valid=False, errors=["Missing required field: topic"],
            )
        return ValidationResult(valid=True)

    async def _build_prompt(self, agent_input: AgentInput) -> PromptContext:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        template_kwargs = {
            "topic": kwargs.get("topic", ""),
            "goals": kwargs.get("goals", "Create comprehensive content"),
            "audience": kwargs.get(
                "audience", "General professional audience"
            ),
            "context": kwargs.get("context", ""),
        }
        return await self._prompt_engine.build(
            agent_type="planner",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> dict[str, Any] | None:
        parsed = self._parse_json_output(content)
        if parsed is None:
            return None
        return parsed

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        if not data.get("title"):
            errors.append("Missing required field: title")
        if not data.get("goals"):
            errors.append("Missing required field: goals")
        if not data.get("themes"):
            errors.append("Missing required field: themes")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(PlannerAgent)
