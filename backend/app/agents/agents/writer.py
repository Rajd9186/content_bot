from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.contracts import (
    AgentContract,
    AgentInput,
    AgentOutput,
    RetryPolicy,
    TimeoutPolicy,
    ValidationResult,
)
from app.agents.prompt.builders import WritingPromptBuilder
from app.agents.prompt.engine import PromptContext
from app.agents.registry import agent_registry
from app.agents.validation.parser import ResponseParser


class WriterAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: str | None = None,
    ) -> None:
        contract = AgentContract(
            name="writer",
            description="Content generation and writing agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=300000),
            required_capabilities=["writing", "content_generation"],
            dependencies=["outliner", "synthesizer"],
        )
        super().__init__(contract, provider_name, model)
        self._parser = ResponseParser()

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        errors = []
        if not kwargs.get("title"):
            errors.append("Missing required: title")
        if not kwargs.get("outline") and not kwargs.get("research_synthesis"):
            errors.append("Missing required: outline or research_synthesis")
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    async def _build_prompt(self, agent_input: AgentInput) -> PromptContext:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        builder = WritingPromptBuilder()
        builder.with_title(kwargs.get("title", ""))
        builder.with_outline(kwargs.get("outline", ""))
        builder.with_research_synthesis(kwargs.get("research_synthesis", ""))
        template_kwargs = builder.build()

        return await self._prompt_engine.build(
            agent_type="writer",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> dict[str, Any] | None:
        md_content, md_error = self._parser.parse_markdown(content)
        if md_error:
            if "placeholder" in (md_error or ""):
                return None
            return None

        if self._parser._is_empty_content(md_content):
            return None

        title = agent_input.metadata.get("template_kwargs", {}).get("title", "")
        word_count = len(md_content.split())

        return {
            "content": md_content,
            "title": title or "Content Document",
            "word_count": word_count,
        }

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        content = data.get("content", "")
        if not content:
            errors.append("No content produced")
        else:
            word_count = len(content.split())
            if word_count < 50:
                errors.append(f"Content too short: {word_count} words")
            placeholder_checks = [
                "# Untitled", "[Content", "[Insert", "TODO", "lorem ipsum",
            ]
            for check in placeholder_checks:
                if check.lower() in content.lower():
                    errors.append(f"Content contains placeholder: {check}")
                    break
            content_lower = content.lower()
            if content_lower.startswith("# untitled"):
                errors.append("Title is 'Untitled'")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(WriterAgent)
