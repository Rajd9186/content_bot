from __future__ import annotations

import logging
from typing import Any

from app.agents.contracts import AgentInput, AgentOutput
from app.agents.pipeline import ExecutionPipeline
from app.agents.registry import agent_registry

logger = logging.getLogger(__name__)


class OrchestrationAgentAdapter:
    def __init__(self) -> None:
        self._pipeline_cache: dict[str, ExecutionPipeline] = {}

    async def execute_agent(
        self,
        agent_name: str,
        correlation_id: str,
        workflow_id: str | None = None,
        workspace_id: str | None = None,
        content_item_id: str | None = None,
        template_kwargs: dict[str, Any] | None = None,
        provider_name: str = "openai",
        model: str | None = None,
    ) -> AgentOutput:
        agent = agent_registry.get_or_create(
            name=agent_name,
            provider_name=provider_name,
            model=model,
        )

        agent_input = AgentInput(
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            content_item_id=content_item_id,
            metadata={
                "template_kwargs": template_kwargs or {},
            },
        )

        pipeline_key = f"{agent_name}:{id(agent)}"
        if pipeline_key not in self._pipeline_cache:
            self._pipeline_cache[pipeline_key] = ExecutionPipeline(agent)

        pipeline = self._pipeline_cache[pipeline_key]
        return await pipeline.execute(agent_input)

    async def execute_stage(
        self,
        stage_name: str,
        context: dict[str, Any],
        correlation_id: str,
        workflow_id: str | None = None,
        provider_name: str = "openai",
        model: str | None = None,
    ) -> AgentOutput:
        agent_name = self._stage_to_agent(stage_name)
        return await self.execute_agent(
            agent_name=agent_name,
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            template_kwargs=context,
            provider_name=provider_name,
            model=model,
        )

    def _stage_to_agent(self, stage_name: str) -> str:
        mapping = {
            "PLANNING": "planner",
            "RESEARCH": "researcher",
            "SYNTHESIS": "synthesizer",
            "OUTLINING": "outliner",
            "WRITING": "writer",
            "VALIDATION": "validator",
            "SEO": "seo",
            "FACT_CHECK": "fact_checker",
            "FINALIZATION": "finalizer",
        }
        return mapping.get(stage_name, stage_name.lower().replace("_", "-"))


orchestration_adapter = OrchestrationAgentAdapter()
