from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.contracts import (
    AgentContract, AgentInput, AgentOutput, RetryPolicy, TimeoutPolicy, ValidationResult,
)
from app.agents.prompt.engine import PromptContext
from app.agents.registry import agent_registry


class SEORecommendation(BaseModel):
    category: str
    current: str
    recommendation: str
    priority: str


class SEOOutput(BaseModel):
    meta_title: str
    meta_description: str
    keyword_analysis: dict[str, Any]
    readability_score: float
    recommendations: list[SEORecommendation]


class SEOAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: Optional[str] = None,
    ) -> None:
        contract = AgentContract(
            name="seo",
            description="SEO optimization and analysis agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=120000),
            required_capabilities=["seo", "optimization"],
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
            "keywords": kwargs.get("keywords", ""),
        }
        return await self._prompt_engine.build(
            agent_type="seo",
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
        if not data.get("meta_title") and not data.get("recommendations"):
            errors.append("No SEO output produced")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(SEOAgent)
