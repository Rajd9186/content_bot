from __future__ import annotations

import time
import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.planner.agent import PlannerAgent
from app.agents.research.agent import ResearchAgent
from app.agents.synthesizer import SynthesizerAgent
from app.agents.outline import OutlineAgent
from app.agents.writer.agent import WriterAgent
from app.agents.validator import ValidatorAgent
from app.agents.seo import SEOAgent
from app.agents.fact_checker import FactCheckerAgent
from app.agents.finalizer import FinalizerAgent
from app.schemas.agent_inputs.planner import PlannerInput
from app.schemas.agent_inputs.research import ResearchInput
from app.schemas.agent_inputs.synthesizer import SynthesizerInput
from app.schemas.agent_inputs.outline import OutlineInput
from app.schemas.agent_inputs.writer import WriterInput
from app.schemas.agent_inputs.validator import ValidatorInput
from app.schemas.agent_inputs.seo import SEOInput
from app.schemas.agent_inputs.fact_checker import FactCheckerInput
from app.schemas.agent_inputs.finalizer import FinalizerInput
from app.schemas.agent_outputs.planner import PlannerOutput
from app.schemas.agent_outputs.research import ResearchOutput
from app.schemas.agent_outputs.synthesizer import SynthesizerOutput
from app.schemas.agent_outputs.outline import OutlineOutput
from app.schemas.agent_outputs.writer import WriterOutput
from app.schemas.agent_outputs.validator import ValidatorOutput
from app.schemas.agent_outputs.seo import SEOOutput
from app.schemas.agent_outputs.fact_checker import FactCheckerOutput
from app.schemas.agent_outputs.finalizer import FinalizerOutput
from app.schemas.research_packet import ResearchPacket
from app.orchestration.workflow_engine.engine import WorkflowEngine, WorkflowState
from app.orchestration.state_machine.workflow_stage import (
    WorkflowStage, StageStatus,
)
from app.events.event_bus import event_bus
from app.telemetry.metrics import get_telemetry_collector
from app.validation import validate_draft
from app.log_config.logger import get_logger
from app.models.content import GeneratedContent
from app.models.content_version import ContentVersion, ContentVersionStatus
from app.models.workflow import WorkflowExecution, WorkflowStatus
from app.repositories.content import ContentRepository
from app.repositories.workflow import WorkflowExecutionRepository
from app.utils.datetime_utils import utc_now

logger = get_logger(__name__)


class ContentOrchestrator:
    PIPELINE_PROGRESS = {
        "PLANNING": 10.0,
        "RESEARCH": 25.0,
        "SYNTHESIS": 35.0,
        "OUTLINING": 45.0,
        "WRITING": 55.0,
        "VALIDATION": 65.0,
        "SEO": 75.0,
        "FACT_CHECK": 85.0,
        "FINALIZATION": 95.0,
        "PUBLISHED": 100.0,
    }

    def __init__(self, session: AsyncSession | None = None):
        self.planner = PlannerAgent()
        self.researcher = ResearchAgent()
        self.synthesizer = SynthesizerAgent()
        self.outliner = OutlineAgent()
        self.writer = WriterAgent()
        self.validator = ValidatorAgent()
        self.seo = SEOAgent()
        self.fact_checker = FactCheckerAgent()
        self.finalizer = FinalizerAgent()
        self.workflow_engine = WorkflowEngine()
        self.telemetry = get_telemetry_collector()
        self._session = session

    async def run_full_pipeline(
        self,
        project_id: str,
        topic: str,
        title: str = "",
        content_type: str = "ARTICLE",
        tone: str = "PROFESSIONAL",
        target_audience: str = "general",
        points_to_cover: list[str] | None = None,
        seo_keywords: list[str] | None = None,
    ) -> FinalizerOutput:
        from app.database import async_session_factory

        if self._session is None:
            async with async_session_factory() as session:
                self._session = session
                return await self._run_pipeline_internal(
                    session, project_id, topic, title, content_type, tone,
                    target_audience, points_to_cover, seo_keywords,
                )
        return await self._run_pipeline_internal(
            self._session, project_id, topic, title, content_type, tone,
            target_audience, points_to_cover, seo_keywords,
        )

    async def _run_pipeline_internal(
        self,
        session: AsyncSession,
        project_id: str,
        topic: str,
        title: str = "",
        content_type: str = "ARTICLE",
        tone: str = "PROFESSIONAL",
        target_audience: str = "general",
        points_to_cover: list[str] | None = None,
        seo_keywords: list[str] | None = None,
    ) -> FinalizerOutput:
        workflow = self.workflow_engine.create_workflow(project_id)
        wf_id = workflow.workflow_id
        self.telemetry.create(wf_id, project_id)

        wf = WorkflowExecution(
            id=UUID(wf_id),
            project_id=UUID(project_id),
            status=WorkflowStatus.RUNNING,
            current_node=WorkflowStage.INIT.value,
        )
        session.add(wf)
        await session.commit()

        await self._emit(wf_id, "workflow_started", "orchestrator", "started",
                         f"Starting 9-stage pipeline for '{topic}'", 0.0,
                         {"project_id": project_id})

        try:
            # Stage 1: Planning
            planner_out = await self._run_stage(
                wf_id, WorkflowStage.PLANNING, "planner",
                lambda: self.planner.run(PlannerInput(
                    topic=topic, title=title, content_type=content_type,
                    tone=tone, target_audience=target_audience,
                    points_to_cover=points_to_cover or [],
                    seo_keywords=seo_keywords or [],
                )),
            )

            # Stage 2: Research
            research_out = await self._run_stage(
                wf_id, WorkflowStage.RESEARCH, "researcher",
                lambda: self.researcher.run(ResearchInput(
                    topic=topic,
                    queries=planner_out.research_tasks,
                    max_sources_per_query=5,
                )),
            )

            # Stage 3: Synthesis
            synthesis_out = await self._run_stage(
                wf_id, WorkflowStage.SYNTHESIS, "synthesizer",
                lambda: self.synthesizer.run(SynthesizerInput(
                    topic=topic,
                    research_packet=research_out.research_packet,
                    planner_outline=planner_out.outline,
                    target_keywords=planner_out.target_keywords,
                )),
            )

            # Stage 4: Outlining
            outline_out = await self._run_stage(
                wf_id, WorkflowStage.OUTLINING, "outliner",
                lambda: self.outliner.run(OutlineInput(
                    topic=topic,
                    research_packet=research_out.research_packet.model_dump() if research_out.research_packet else {},
                    planner_outline=planner_out.outline,
                    content_type=content_type,
                )),
            )

            # Stage 5: Writing
            writer_out = await self._run_stage(
                wf_id, WorkflowStage.WRITING, "writer",
                lambda: self.writer.run(WriterInput(
                    title=title or topic,
                    topic=topic,
                    outline=planner_out.outline,
                    research_packet=research_out.research_packet,
                    verified_claims=[],
                    tone=tone,
                    target_audience=target_audience,
                    content_type=content_type,
                    seo_keywords=seo_keywords or [],
                )),
            )

            # Stage 6: Validation
            validator_out = await self._run_stage(
                wf_id, WorkflowStage.VALIDATION, "validator",
                lambda: self.validator.run(ValidatorInput(
                    markdown=writer_out.markdown,
                    title=title or topic,
                    citations=writer_out.citations,
                    min_word_count=300,
                    required_sections=[s.get("heading", "") for s in outline_out.sections],
                )),
            )

            # Stage 7: SEO
            seo_out = await self._run_stage(
                wf_id, WorkflowStage.SEO, "seo",
                lambda: self.seo.run(SEOInput(
                    markdown=writer_out.markdown,
                    title=title or topic,
                    seo_keywords=seo_keywords or planner_out.target_keywords,
                    content_type=content_type,
                )),
            )

            # Stage 8: Fact Check
            fact_check_out = await self._run_stage(
                wf_id, WorkflowStage.FACT_CHECK, "fact_checker",
                lambda: self.fact_checker.run(FactCheckerInput(
                    markdown=seo_out.optimized_markdown or writer_out.markdown,
                    citations=writer_out.citations,
                    verified_claims=[],
                    research_packet=research_out.research_packet.model_dump() if research_out.research_packet else {},
                )),
            )

            # Stage 9: Finalization
            markdown_for_final = fact_check_out.corrected_markdown or seo_out.optimized_markdown or writer_out.markdown
            finalizer_out = await self._run_stage(
                wf_id, WorkflowStage.FINALIZATION, "finalizer",
                lambda: self.finalizer.run(FinalizerInput(
                    markdown=markdown_for_final,
                    title=title or topic,
                    meta_title=seo_out.meta_title,
                    meta_description=seo_out.meta_description,
                    focus_keywords=seo_out.focus_keywords,
                    citations=writer_out.citations,
                    quality_score=validator_out.quality_score,
                    seo_score=seo_out.seo_score,
                    fact_check_passed=fact_check_out.is_pass,
                )),
            )

            # Transition to PUBLISHED
            self.workflow_engine.transition_to(
                wf_id, WorkflowStage.PUBLISHED, StageStatus.COMPLETED,
            )

            overall_quality = finalizer_out.overall_quality
            if overall_quality > 0:
                self.telemetry.set_final_quality(wf_id, overall_quality)
            self.telemetry.set_completed(wf_id)

            gc = GeneratedContent(
                project_id=UUID(project_id),
                markdown=finalizer_out.final_markdown,
                summary=finalizer_out.meta_description,
                word_count=finalizer_out.word_count,
                citations=finalizer_out.citations,
                overall_confidence=overall_quality,
            )
            session.add(gc)

            cv = ContentVersion(
                project_id=UUID(project_id),
                version_number=1,
                agent_name="orchestrator",
                status=ContentVersionStatus.DRAFT,
                markdown=finalizer_out.final_markdown,
                summary=finalizer_out.meta_description,
                word_count=finalizer_out.word_count,
                citations=finalizer_out.citations,
                overall_confidence=overall_quality,
                change_description="Generated by v3 9-stage content orchestrator",
            )
            session.add(cv)

            wf.current_node = WorkflowStage.PUBLISHED.value
            wf.status = WorkflowStatus.COMPLETED
            wf.completed_at = utc_now()
            await session.commit()

            await self._emit(wf_id, "workflow_completed", "orchestrator", "completed",
                             f"Pipeline complete: {finalizer_out.word_count} words, "
                             f"{len(finalizer_out.citations)} citations",
                             100.0,
                             {"word_count": finalizer_out.word_count,
                              "citations": len(finalizer_out.citations),
                              "quality_score": overall_quality})

            return finalizer_out

        except Exception as e:
            logger.error("Pipeline failed at stage", extra={"error": str(e)[:500]})
            self.workflow_engine.transition_to(
                wf_id, WorkflowStage.FAILED, StageStatus.FAILED, error=str(e),
            )
            wf.current_node = WorkflowStage.FAILED.value
            wf.status = WorkflowStatus.FAILED
            wf.error = str(e)[:2000]
            await session.commit()

            await self._emit(wf_id, "workflow_failed", "orchestrator", "failed",
                             f"Pipeline failed: {str(e)[:200]}", 0.0,
                             {"error": str(e)[:500]})
            raise

    async def _run_stage(self, wf_id: str, stage: WorkflowStage, agent_name: str, fn):
        start = time.time()
        self.workflow_engine.transition_to(wf_id, stage, StageStatus.STARTED)
        progress = self.PIPELINE_PROGRESS.get(stage.value, 0.0)

        await self._emit(wf_id, "agent_started", agent_name, "running",
                         f"{agent_name} started", progress)

        try:
            result = await fn()
            elapsed = (time.time() - start) * 1000.0
            self.workflow_engine.transition_to(wf_id, stage, StageStatus.COMPLETED)
            self.workflow_engine.mark_stage_duration(wf_id, stage, elapsed)
            self.telemetry.add_stage(wf_id, stage.value, agent_name, duration_ms=elapsed)

            await self._emit(wf_id, "agent_completed", agent_name, "completed",
                             f"{agent_name} completed", progress + 5.0)
            return result
        except Exception as e:
            elapsed = (time.time() - start) * 1000.0
            self.workflow_engine.transition_to(wf_id, stage, StageStatus.FAILED, error=str(e))
            self.telemetry.add_stage(wf_id, stage.value, agent_name, duration_ms=elapsed, error=str(e)[:200], success=False)
            raise

    async def _emit(self, wf_id: str, event_type: str, agent_name: str,
                    status: str, message: str, progress: float,
                    payload: dict | None = None):
        await event_bus.publish_event(
            wf_id, event_type,
            agent_name=agent_name,
            status=status,
            message=message,
            progress_percent=progress,
            payload=payload or {},
        )
