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


class OutlineSection(BaseModel):
    title: str
    key_points: list[str]
    subsections: list[str] | None = None


class OutlineOutput(BaseModel):
    title: str
    sections: list[OutlineSection]


class OutlinerAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: str | None = None,
    ) -> None:
        contract = AgentContract(
            name="outliner",
            description="Content outline generation agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=120000),
            required_capabilities=["outlining", "structuring"],
            dependencies=["synthesizer"],
        )
        super().__init__(contract, provider_name, model)

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        if not kwargs.get("research_synthesis") and not kwargs.get("content_plan"):
            return ValidationResult(
                valid=False,
                errors=["Missing required: research_synthesis or content_plan"],
            )
        return ValidationResult(valid=True)

    async def _build_prompt(self, agent_input: AgentInput) -> PromptContext:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        template_kwargs = {
            "research_synthesis": kwargs.get("research_synthesis", ""),
            "content_plan": kwargs.get("content_plan", ""),
        }
        return await self._prompt_engine.build(
            agent_type="outliner",
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
        if not data.get("title"):
            errors.append("Missing outline title")
        sections = data.get("sections", [])
        if not sections:
            errors.append("No sections defined in outline")
        else:
            for i, sec in enumerate(sections):
                if not sec.get("title"):
                    errors.append(f"Section {i + 1} missing title")
                if not sec.get("key_points"):
                    errors.append(f"Section {sec.get('title', i + 1)} has no key points")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(OutlinerAgent)
