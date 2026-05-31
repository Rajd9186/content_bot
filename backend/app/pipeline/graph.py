from __future__ import annotations

import logging
import time
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from app.infrastructure.metrics.collector import metrics_collector
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

    async def _run_step(
        self,
        name: str,
        agent: PipelineAgent,
        state: PipelineState,
        on_success,
    ) -> PipelineState:
        logger.info("Pipeline: running %s agent", name)
        state.current_node = name
        result = await agent.execute(state)
        state.add_node_result(name, result)
        if result.status == NodeStatus.FAILED:
            state.errors.append(f"{name}: {result.error or 'Unknown error'}")
        elif result.status == NodeStatus.SUCCESS:
            on_success(result)
        
        # Enhanced progress notification with SSE broadcast for actions
        await self._notify_progress(name, result)
        
        from app.infrastructure.sse.manager import sse_manager
        await sse_manager.broadcast_pipeline_event(
            state.workflow_id,
            "node_progress",
            node=name,
            status=result.status,
            actions=result.actions,
            tokens_used=result.tokens_used,
            latency_ms=result.latency_ms
        )
        return state

    async def run_research(self, state: PipelineState) -> PipelineState:
        return await self._run_step(
            "research", self._research_agent, state,
            lambda r: setattr(state, "research_data", extract_research_data(r.output)),
        )

    async def run_planner(self, state: PipelineState) -> PipelineState:
        return await self._run_step(
            "planner", self._planner_agent, state,
            lambda r: setattr(state, "plan", extract_plan(r.output)),
        )

    async def run_writer(self, state: PipelineState) -> PipelineState:
        def _on_success(r):
            content, metadata = extract_writer_output(r.output)
            state.draft_content = content or metadata.get("content", "")
        return await self._run_step(
            "writer", self._writer_agent, state, _on_success,
        )

    async def run_seo(self, state: PipelineState) -> PipelineState:
        def _on_success(r):
            content, metadata = extract_seo_output(r.output)
            state.draft_content = content or state.draft_content
            state.seo_metadata = metadata
        return await self._run_step(
            "seo", self._seo_agent, state, _on_success,
        )

    async def run_fact_check(self, state: PipelineState) -> PipelineState:
        def _on_success(r):
            content, metadata = extract_fact_check_output(r.output)
            state.draft_content = content or state.draft_content
            state.fact_check_results = metadata
        return await self._run_step(
            "fact_checker", self._fact_checker_agent, state, _on_success,
        )

    async def run_compliance(self, state: PipelineState) -> PipelineState:
        def _on_success(r):
            content, metadata = extract_compliance_output(r.output)
            state.draft_content = content or state.draft_content
            state.compliance_results = metadata
        return await self._run_step(
            "compliance", self._compliance_agent, state, _on_success,
        )

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
        def _on_success(r):
            final = extract_finalizer_output(r.output)
            state.final_content = final.get("final_content", r.output.get("content", ""))
            if not state.final_content:
                state.final_content = state.draft_content
        return await self._run_step(
            "finalizer", self._finalizer_agent, state, _on_success,
        )

    async def run_memory_retrieval(self, state: PipelineState) -> PipelineState:
        from app.infrastructure.database import async_session_factory
        from app.pipeline.agents.memory_retrieval_agent import run_memory_retrieval

        return await run_memory_retrieval(state, async_session_factory)

    async def execute(
        self,
        state: PipelineState,
        skip_human_review: bool = False,
    ) -> PipelineState:
        start_time = time.monotonic()
        steps = [
            self.run_memory_retrieval,
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

        duration_ms = (time.monotonic() - start_time) * 1000
        workflow_status = "failed" if state.has_failures() else "completed"
        metrics_collector.record_workflow_duration(duration_ms, workflow_status)

        return state


pipeline = WorkflowPipeline()


def create_pipeline() -> WorkflowPipeline:
    return pipeline
