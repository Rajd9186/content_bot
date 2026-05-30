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
from app.agents.prompt.engine import PromptContext
from app.agents.registry import agent_registry
from app.agents.validation.parser import ResponseParser


class FinalizerAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: str | None = None,
    ) -> None:
        contract = AgentContract(
            name="finalizer",
            description="Content finalization and polish agent",
            version="1.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=300000),
            required_capabilities=["finalization", "polish"],
            dependencies=["writer", "validator", "seo", "fact_checker"],
        )
        super().__init__(contract, provider_name, model)
        self._parser = ResponseParser()

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
            "validation_feedback": kwargs.get("validation_feedback", ""),
            "seo_feedback": kwargs.get("seo_feedback", ""),
            "fact_check_report": kwargs.get("fact_check_report", ""),
        }
        return await self._prompt_engine.build(
            agent_type="finalizer",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> dict[str, Any] | None:
        md_content, md_error = self._parser.parse_markdown(content)
        if md_error:
            if self._parser._is_empty_content(md_content):
                return None
            return None

        title = agent_input.metadata.get("template_kwargs", {}).get("title", "")
        word_count = len(md_content.split())

        return {
            "content": md_content,
            "title": title or "Finalized Content",
            "word_count": word_count,
            "changes_applied": agent_input.metadata.get(
                "template_kwargs", {}
            ).get("validation_feedback", ""),
        }

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        content = data.get("content", "")
        if not content:
            errors.append("No finalized content produced")
        else:
            word_count = len(content.split())
            if word_count < 50:
                errors.append(f"Final content too short: {word_count} words")
            if "# Untitled" in content:
                errors.append("Title is 'Untitled'")
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(FinalizerAgent)
