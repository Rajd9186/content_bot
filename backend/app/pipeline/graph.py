from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from app.pipeline.agents.compliance_agent import ComplianceAgent, extract_compliance_output
from app.pipeline.agents.fact_checker_agent import FactCheckerAgent, extract_fact_check_output
from app.pipeline.agents.finalizer_agent import FinalizerAgent, extract_finalizer_output
from app.pipeline.agents.planner_agent import PlannerAgent, extract_plan
from app.pipeline.agents.research_agent import ResearchAgent, extract_research_data
from app.pipeline.agents.seo_agent import SEOAgent, extract_seo_output
from app.pipeline.agents.writer_agent import WriterAgent, extract_writer_output
from app.pipeline.state import NodeResult, NodeStatus, PipelineState

logger = logging.getLogger(__name__)

NodeHandler = Callable[[PipelineState], Coroutine[Any, Any, PipelineState]]


class WorkflowPipeline:
    def __init__(self) -> None:
        self._research_agent = ResearchAgent()
        self._planner_agent = PlannerAgent()
        self._writer_agent = WriterAgent()
        self._seo_agent = SEOAgent()
        self._fact_checker_agent = FactCheckerAgent()
        self._compliance_agent = ComplianceAgent()
        self._finalizer_agent = FinalizerAgent()
        self._progress_callbacks: list[Callable[[str, NodeResult], None]] = []

    def on_progress(self, callback: Callable[[str, NodeResult], None]) -> None:
        self._progress_callbacks.append(callback)

    async def _notify_progress(self, node: str, result: NodeResult) -> None:
        for cb in self._progress_callbacks:
            try:
                cb(node, result)
            except Exception as e:
                logger.warning("Progress callback error: %s", e)

    async def run_research(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running research agent")
        state.current_node = "research"
        result = await self._research_agent.execute(state)
        state.add_node_result("research", result)
        if result.status == NodeStatus.SUCCESS:
            state.research_data = extract_research_data(result.output)
        await self._notify_progress("research", result)
        return state

    async def run_planner(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running planner agent")
        state.current_node = "planner"
        result = await self._planner_agent.execute(state)
        state.add_node_result("planner", result)
        if result.status == NodeStatus.SUCCESS:
            state.plan = extract_plan(result.output)
        await self._notify_progress("planner", result)
        return state

    async def run_writer(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running writer agent")
        state.current_node = "writer"
        result = await self._writer_agent.execute(state)
        state.add_node_result("writer", result)
        if result.status == NodeStatus.SUCCESS:
            content, metadata = extract_writer_output(result.output)
            state.draft_content = content or metadata.get("content", "")
        await self._notify_progress("writer", result)
        return state

    async def run_seo(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running SEO agent")
        state.current_node = "seo"
        result = await self._seo_agent.execute(state)
        state.add_node_result("seo", result)
        if result.status == NodeStatus.SUCCESS:
            content, metadata = extract_seo_output(result.output)
            state.draft_content = content or state.draft_content
            state.seo_metadata = metadata
        await self._notify_progress("seo", result)
        return state

    async def run_fact_check(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running fact checker agent")
        state.current_node = "fact_checker"
        result = await self._fact_checker_agent.execute(state)
        state.add_node_result("fact_checker", result)
        if result.status == NodeStatus.SUCCESS:
            content, metadata = extract_fact_check_output(result.output)
            state.draft_content = content or state.draft_content
            state.fact_check_results = metadata
        await self._notify_progress("fact_checker", result)
        return state

    async def run_compliance(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running compliance agent")
        state.current_node = "compliance"
        result = await self._compliance_agent.execute(state)
        state.add_node_result("compliance", result)
        if result.status == NodeStatus.SUCCESS:
            content, metadata = extract_compliance_output(result.output)
            state.draft_content = content or state.draft_content
            state.compliance_results = metadata
        await self._notify_progress("compliance", result)
        return state

    async def run_human_review(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: awaiting human review")
        state.current_node = "human_review"
        result = NodeResult(
            node="human_review",
            status=NodeStatus.SUCCESS,
            output={
                "message": "Content ready for human review",
                "requires_review": True,
            },
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
        )
        state.add_node_result("human_review", result)
        await self._notify_progress("human_review", result)
        return state

    async def run_finalizer(self, state: PipelineState) -> PipelineState:
        logger.info("Pipeline: running finalizer agent")
        state.current_node = "finalizer"
        result = await self._finalizer_agent.execute(state)
        state.add_node_result("finalizer", result)
        if result.status == NodeStatus.SUCCESS:
            final = extract_finalizer_output(result.output)
            state.final_content = final.get("final_content", result.output.get("content", ""))
            if not state.final_content:
                state.final_content = state.draft_content
        await self._notify_progress("finalizer", result)
        return state

    async def execute(
        self,
        state: PipelineState,
        skip_human_review: bool = False,
    ) -> PipelineState:
        steps = [
            self.run_research,
            self.run_planner,
            self.run_writer,
            self.run_seo,
            self.run_fact_check,
            self.run_compliance,
        ]
        if not skip_human_review:
            steps.append(self.run_human_review)
        steps.append(self.run_finalizer)

        for step in steps:
            if state.has_failures():
                logger.warning(
                    "Pipeline stopping due to previous failures: %s",
                    state.errors,
                )
                break
            state = await step(state)

        return state


pipeline = WorkflowPipeline()


def create_pipeline() -> WorkflowPipeline:
    return pipeline
