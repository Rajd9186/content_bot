from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.contracts import (
    AgentContract, AgentInput, AgentOutput, RetryPolicy, TimeoutPolicy, ValidationResult,
)
from app.agents.prompt.engine import PromptContext
from app.agents.registry import agent_registry


class SynthesisTheme(BaseModel):
    theme: str
    insight: str = Field(min_length=50)
    confidence: str


class SynthesisOutput(BaseModel):
    synthesis: str = Field(min_length=100)
    themes: list[SynthesisTheme]
    key_insights: list[str]
    gaps: Optional[list[str]] = None


class SynthesizerAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: Optional[str] = None,
    ) -> None:
        contract = AgentContract(
            name="synthesizer",
            description="Research synthesis and pattern identification agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=120000),
            required_capabilities=["synthesis", "analysis"],
            dependencies=["researcher"],
        )
        super().__init__(contract, provider_name, model)

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        if not kwargs.get("research_findings"):
            return ValidationResult(
                valid=False, errors=["Missing required: research_findings"],
            )
        return ValidationResult(valid=True)

    async def _build_prompt(self, agent_input: AgentInput) -> PromptContext:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        research = kwargs.get("research_findings", "")
        if isinstance(research, dict):
            research = self._format_research_for_prompt(research)
        elif isinstance(research, list):
            research = self._format_research_list(research)

        template_kwargs = {
            "research_findings": research,
            "content_plan": kwargs.get("content_plan", ""),
        }
        return await self._prompt_engine.build(
            agent_type="synthesizer",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    def _format_research_for_prompt(self, research: dict[str, Any]) -> str:
        parts = []
        findings = research.get("findings", [])
        for i, f in enumerate(findings, 1):
            parts.append(f"Finding {i}: {f.get('topic', 'Research topic')}")
            parts.append(f"  Detail: {f.get('finding', '')}")
            parts.append(f"  Analysis: {f.get('analysis', '')}")
            parts.append(f"  Source: {f.get('source', 'Unknown')}")
            parts.append("")
        return "\n".join(parts)

    def _format_research_list(self, findings: list) -> str:
        parts = []
        for i, f in enumerate(findings, 1):
            if isinstance(f, dict):
                parts.append(f"Finding {i}: {f.get('topic', f.get('finding', str(f)))}")
            else:
                parts.append(f"Finding {i}: {f}")
        return "\n".join(parts)

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> Optional[dict[str, Any]]:
        return self._parse_json_output(content)

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        if not data.get("synthesis"):
            errors.append("Missing synthesis text")
        if not data.get("themes"):
            errors.append("No themes identified")
        if not data.get("key_insights"):
            errors.append("No key insights provided")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(SynthesizerAgent)
