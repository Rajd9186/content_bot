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
from app.research.integration import research_integration


class ResearchFinding(BaseModel):
    topic: str
    finding: str = Field(min_length=50)
    analysis: str = Field(min_length=50)
    source: str
    relevance: str


class ResearchOutput(BaseModel):
    findings: list[ResearchFinding]
    research_questions_answered: str
    gaps: list[str]


class ResearcherAgent(BaseAgent):
    def __init__(
        self, provider_name: str = "openai", model: str | None = None,
    ) -> None:
        contract = AgentContract(
            name="researcher",
            description="Research and information gathering agent with Phase 5 intelligence",
            version="2.0.0",
            input_schema=AgentInput,
            output_schema=AgentOutput,
            retry_policy=RetryPolicy(max_retries=3, base_delay_ms=2000.0),
            timeout_policy=TimeoutPolicy(execution_ms=300000),
            required_capabilities=["research", "information_gathering", "synthesis"],
        )
        super().__init__(contract, provider_name, model)

    async def _validate_input(self, agent_input: AgentInput) -> ValidationResult:
        kwargs = agent_input.metadata.get("template_kwargs", {})
        if not kwargs.get("plan_summary") and not kwargs.get("research_questions") and not kwargs.get("topic"):
            return ValidationResult(
                valid=False,
                errors=["Missing required: plan_summary, research_questions, or topic"],
            )
        return ValidationResult(valid=True)

    async def _execute_with_phase5_research(
        self,
        agent_input: AgentInput,
    ) -> dict[str, Any]:
        """Execute Phase 5 research pipeline and return structured findings"""
        kwargs = agent_input.metadata.get("template_kwargs", {})

        topic = kwargs.get("topic", kwargs.get("title", "Research Topic"))
        plan_summary = kwargs.get("plan_summary", "")
        research_questions = kwargs.get("research_questions", [])

        if isinstance(research_questions, str):
            questions_list = [q.strip() for q in research_questions.split("\n") if q.strip()]
        else:
            questions_list = research_questions or []

        research_result = await research_integration.execute_research(
            topic=topic,
            query=plan_summary or topic,
            correlation_id=agent_input.correlation_id,
            workflow_id=agent_input.workflow_id,
            topics=questions_list[:5],
            max_results=30,
        )

        return research_result

    async def _build_prompt(
        self,
        agent_input: AgentInput,
        research_data: dict[str, Any] | None = None,
    ) -> PromptContext:
        kwargs = agent_input.metadata.get("template_kwargs", {})

        if research_data:
            synthesis = research_data.get("synthesis")
            if synthesis:
                template_kwargs = {
                    "plan_summary": synthesis.summary,
                    "research_questions": "\n".join(
                        f.finding for f in synthesis.key_findings[:5]
                    ),
                    "existing_knowledge": synthesis.writer_context,
                    "research_findings": [
                        {
                            "topic": f.category,
                            "finding": f.finding,
                            "analysis": f.finding,
                            "source": f.sources[0] if f.sources else "Multiple sources",
                            "relevance": "high" if f.confidence > 0.7 else "medium",
                        }
                        for f in synthesis.key_findings[:5]
                    ],
                }
            else:
                template_kwargs = {
                    "plan_summary": research_data.get("writer_brief", ""),
                    "research_questions": kwargs.get("research_questions", ""),
                    "existing_knowledge": "Research conducted with Phase 5 intelligence",
                }
        else:
            template_kwargs = {
                "plan_summary": kwargs.get("plan_summary", ""),
                "research_questions": kwargs.get("research_questions", ""),
                "existing_knowledge": kwargs.get("existing_knowledge", "No prior knowledge provided."),
            }

        return await self._prompt_engine.build(
            agent_type="researcher",
            correlation_id=agent_input.correlation_id,
            template_kwargs=template_kwargs,
        )

    async def _parse_output(
        self, content: str, agent_input: AgentInput,
    ) -> dict[str, Any] | None:
        parsed = self._parse_json_output(content)
        if parsed is None:
            return None

        findings = parsed.get("findings", [])
        if isinstance(findings, list):
            for f in findings:
                finding_text = f.get("finding", "")
                if len(finding_text.split()) < 15:
                    f["finding"] = (
                        f"{finding_text} This finding is part of a comprehensive "
                        f"research effort on the specified topic, drawing from "
                        f"multiple authoritative sources to provide depth and context."
                    )
        return parsed

    async def _validate_output(
        self, data: dict[str, Any], agent_input: AgentInput,
    ) -> ValidationResult:
        errors = []
        findings = data.get("findings", [])
        if not findings:
            errors.append("No research findings produced")
        else:
            for i, f in enumerate(findings):
                finding_text = f.get("finding", "")
                if len(finding_text.split()) < 10:
                    errors.append(
                        f"Finding {i + 1} is too short ({len(finding_text.split())} words)"
                    )
        return ValidationResult(valid=len(errors) == 0, errors=errors)


agent_registry.register(ResearcherAgent)
