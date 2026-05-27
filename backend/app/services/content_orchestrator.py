from __future__ import annotations

import time
import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.planner.agent import PlannerAgent
from app.agents.research.agent import ResearchAgent
from app.agents.writer.agent import WriterAgent
from app.schemas.agent_inputs.planner import PlannerInput
from app.schemas.agent_inputs.research import ResearchInput
from app.schemas.agent_inputs.writer import WriterInput
from app.schemas.agent_outputs.planner import PlannerOutput
from app.schemas.agent_outputs.research import ResearchOutput
from app.schemas.agent_outputs.writer import WriterOutput
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
    def __init__(self, session: AsyncSession | None = None):
        self.planner = PlannerAgent()
        self.researcher = ResearchAgent()
        self.writer = WriterAgent()
        self.workflow_engine = WorkflowEngine()
        self.telemetry = get_telemetry_collector()
        self._session = session

    async def run_full_pipeline(
        self,
        project_id: str,
        topic: str,
        title: str = "",
        content_type: str = "article",
        tone: str = "professional",
        target_audience: str = "general",
        points_to_cover: list[str] | None = None,
        seo_keywords: list[str] | None = None,
    ) -> WriterOutput:
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
        content_type: str = "article",
        tone: str = "professional",
        target_audience: str = "general",
        points_to_cover: list[str] | None = None,
        seo_keywords: list[str] | None = None,
    ) -> WriterOutput:
        workflow = self.workflow_engine.create_workflow(project_id)
        wf_id = workflow.workflow_id
        self.telemetry.create(wf_id, project_id)

        wf = WorkflowExecution(
            id=UUID(wf_id),
            project_id=UUID(project_id),
            status=WorkflowStatus.running,
            current_node=WorkflowStage.INIT.value,
        )
        session.add(wf)
        await session.commit()

        await event_bus.publish_event(
            wf_id, "workflow_started", agent_name="orchestrator",
            status="started", message=f"Starting pipeline for '{topic}'",
        )

        planner_out = await self._run_planning(
            wf_id, project_id, topic, title,
            content_type, tone, target_audience,
            points_to_cover or [], seo_keywords or [],
        )

        research_out = await self._run_research(
            wf_id, project_id, topic, planner_out,
        )

        writer_out = await self._run_writing(
            wf_id, project_id, title or topic,
            planner_out, research_out, tone,
            target_audience, content_type, seo_keywords or [],
        )

        self.workflow_engine.transition_to(
            wf_id, WorkflowStage.PUBLISHED, StageStatus.COMPLETED,
        )

        if writer_out.quality_score > 0:
            self.telemetry.set_final_quality(wf_id, writer_out.quality_score)
        self.telemetry.set_completed(wf_id)

        gc = GeneratedContent(
            project_id=UUID(project_id),
            markdown=writer_out.markdown,
            summary=writer_out.summary,
            word_count=writer_out.word_count,
            citations=writer_out.citations,
            overall_confidence=writer_out.quality_score,
        )
        session.add(gc)

        cv = ContentVersion(
            project_id=UUID(project_id),
            version_number=1,
            agent_name="orchestrator",
            status=ContentVersionStatus.DRAFT,
            markdown=writer_out.markdown,
            summary=writer_out.summary,
            word_count=writer_out.word_count,
            citations=writer_out.citations,
            overall_confidence=writer_out.quality_score,
            change_description="Generated by v3 content orchestrator",
        )
        session.add(cv)

        wf.current_node = WorkflowStage.PUBLISHED.value
        wf.status = WorkflowStatus.completed
        wf.completed_at = utc_now()
        await session.commit()

        await event_bus.publish_event(
            wf_id, "workflow_completed", agent_name="orchestrator",
            status="completed",
            message=f"Pipeline complete: {writer_out.word_count} words, {len(writer_out.citations)} citations",
            payload={
                "word_count": writer_out.word_count,
                "citations": len(writer_out.citations),
                "quality_score": writer_out.quality_score,
            },
        )

        return writer_out