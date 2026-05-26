"""Staged, event-driven workflow orchestrator with SSE streaming.

Pipeline:
  STAGE 1: Planning (planner agent → outline + research queries)
  STAGE 2: Research (bounded concurrent research agents → sources)
  STAGE 3: Writing (writer agent → draft content)
  STAGE 4: Draft Ready → WAITING_FOR_USER (frontend shows draft, user decides)
  STAGE 5+: Enhancement agents (user-triggered: critique, revision, verification, etc.)

Each stage publishes typed events to the WorkflowEventBus for SSE streaming.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.log_config.logger import get_logger
from app.config import settings
from app.utils.datetime_utils import utc_now
from app.models.workflow import WorkflowStatus
from app.models.content_version import ContentVersion, ContentVersionStatus, ContentLock, EnhancementJob
from app.engine.workflow_state import (
    WorkflowStage,
    validate_transition,
    IllegalTransitionError,
    stage_display_name,
    can_transition_to,
)
from app.services.event_bus import event_bus
from app.repositories.project import ProjectRepository
from app.repositories.workflow import WorkflowExecutionRepository, WorkflowStepRepository
from app.repositories.content import ContentRepository
from app.repositories.source import SourceRepository
from app.repositories.claim import ClaimRepository
from app.repositories.contradiction import ContradictionRepository
from app.repositories.hyperlink import HyperlinkValidationRepository

from app.agents.task_planner import TaskPlannerAgent
from app.agents.content_writer import ContentWriterAgent
from app.agents.verifier import VerificationAgent
from app.agents.self_verifier import SelfVerificationAgent
from app.agents.contradiction_detector import ContradictionDetectionAgent
from app.agents.critique import CritiqueAgent
from app.agents.revision import RevisionAgent
from app.agents.hyperlink_validator import HyperlinkValidationAgent
from app.services.research_service import ResearchService
from app.memory.agent_memory import AgentMemoryService
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import LocalVectorStore

logger = get_logger(__name__)

_research_semaphore = asyncio.Semaphore(settings.research_concurrency)


def _calc_stage_weight(stage: WorkflowStage) -> float:
    """Return cumulative progress percentage after completing this stage."""
    weights = settings.stage_weights
    cumulative = 0.0
    for s, w in weights.items():
        cumulative += w
        if s == stage.value:
            break
    return cumulative


def _calc_sub_progress(stage: WorkflowStage, sub_pct: float) -> float:
    """Calculate overall progress given a stage and sub-progress (0-100)."""
    weights = settings.stage_weights
    before = 0.0
    for s, w in weights.items():
        if s == stage.value:
            break
        before += w
    stage_weight = weights.get(stage.value, 0.0)
    return before + (stage_weight * sub_pct / 100.0)


class StageOrchestrator:
    """Orchestrates the staged workflow pipeline with SSE event streaming."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(self.__class__.__name__)
        self.project_repo = ProjectRepository(session)
        self.content_repo = ContentRepository(session)
        self.workflow_repo = WorkflowExecutionRepository(session)
        self.workflow_step_repo = WorkflowStepRepository(session)
        self.claim_repo = ClaimRepository(session)
        self.source_repo = SourceRepository(session)
        self.contradiction_repo = ContradictionRepository(session)
        self.hyperlink_repo = HyperlinkValidationRepository(session)

        self.planner = TaskPlannerAgent()
        self.writer = ContentWriterAgent()
        self.research_service = ResearchService()
        self.memory_service = AgentMemoryService(None)
        self.embedding_service = EmbeddingService()
        self.vector_store = LocalVectorStore(self.embedding_service)
        self.verifier = VerificationAgent()
        self.self_verifier = SelfVerificationAgent()
        self.contradiction_detector = ContradictionDetectionAgent()
        self.critique = CritiqueAgent()
        self.revision = RevisionAgent()
        self.hyperlink_validator = HyperlinkValidationAgent()

        self._workflow_id: Optional[UUID] = None
        self._project_id: Optional[UUID] = None
        self._current_stage: Optional[WorkflowStage] = None

    # ──────────────────────────────────────────────
    # Public API: full auto pipeline
    # ──────────────────────────────────────────────

    async def run_auto_pipeline(self, project) -> dict:
        """Run stages 1-4 then pause in WAITING_FOR_USER."""
        project_id = project.id
        self._project_id = project_id
        workflow_id = uuid.uuid4()
        self._workflow_id = workflow_id

        self.logger.info("Starting auto pipeline", extra={"project_id": str(project_id), "workflow_id": str(workflow_id)})

        workflow = await self.workflow_repo.create(
            id=workflow_id,
            project_id=project_id,
            status=WorkflowStatus.running,
            current_node="planner",
        )

        await self._publish_and_transition(WorkflowStage.CREATED, workflow, "workflow_started", "orchestrator")
        workflow_state = {}

        try:
            await self._publish_and_transition(WorkflowStage.PLANNING, workflow, "agent_started", "planner")
            workflow_state = await self._run_planning(project, workflow_id)
            self.logger.info("Stage 1 complete", extra={"project_id": str(project_id)})

            await self._publish_and_transition(WorkflowStage.RESEARCHING, workflow, "agent_started", "research")
            workflow_state = await self._run_research(project, workflow_id, workflow_state)
            self.logger.info("Stage 2 complete", extra={"project_id": str(project_id)})

            await self._publish_and_transition(WorkflowStage.WRITING, workflow, "agent_started", "writer")
            workflow_state = await self._run_writing(project, workflow_id, workflow_state)
            self.logger.info("Stage 3 complete", extra={"project_id": str(project_id)})

            await self._publish_draft(project_id, workflow_id, workflow_state)
            self.logger.info("Stage 4 complete — awaiting user", extra={"project_id": str(project_id)})

            # Pause for human input
            workflow.current_node = WorkflowStage.WAITING_FOR_USER.value
            await self.session.flush()
            await event_bus.publish(
                workflow_id, "waiting_for_user", agent_name="orchestrator", status="waiting",
                message="Draft ready — awaiting user decision (approve, regenerate, or run enhancement agents)",
                progress_percent=_calc_stage_weight(WorkflowStage.DRAFT_READY),
                payload={"project_id": str(project_id), "stage": "WAITING_FOR_USER"},
            )

            return workflow_state

        except Exception as e:
            self.logger.error(f"Pipeline failed at stage {self._current_stage}: {e}", exc_info=True)
            await self._publish_and_transition(WorkflowStage.FAILED, workflow, "workflow_failed", "orchestrator", error=str(e))
            raise

    # ──────────────────────────────────────────────
    # Stage implementations
    # ──────────────────────────────────────────────

    async def _run_planning(self, project, workflow_id: UUID) -> dict:
        await event_bus.publish(
            workflow_id, "agent_progress", agent_name="planner", status="running",
            message="Planning content outline and research strategy",
            progress_percent=_calc_sub_progress(WorkflowStage.PLANNING, 10),
            payload={"project_id": str(project.id)},
        )
        outline = await self.planner.run(
            topic=project.topic, title=project.title,
            content_type=project.content_type, tone=project.tone,
            target_audience=project.target_audience,
            points_to_cover=project.points_to_cover,
            seo_keywords=project.seo_keywords,
        )
        sections = outline.get("sections", [])
        research_tasks = []
        for s in sections:
            research_tasks.extend(s.get("research_queries", []))
        if not research_tasks:
            research_tasks = [f"{project.topic} current state research", f"{project.topic} statistics", f"{project.topic} trusted sources"]

        await self.project_repo.update(project.id, outline=outline)

        await event_bus.publish(
            workflow_id, "agent_completed", agent_name="planner", status="completed",
            message=f"Planned {len(sections)} sections with {len(research_tasks)} research queries",
            progress_percent=_calc_stage_weight(WorkflowStage.PLANNING),
            payload={"project_id": str(project.id), "sections": len(sections), "research_tasks": len(research_tasks)},
        )
        return {"outline": outline, "research_tasks": research_tasks, "sections": sections}

    async def _run_research(self, project, workflow_id: UUID, state: dict) -> dict:
        tasks = state.get("research_tasks", [])
        if not tasks:
            await event_bus.publish(workflow_id, "agent_completed", agent_name="research", status="completed",
                message="No research tasks to execute",
                progress_percent=_calc_stage_weight(WorkflowStage.RESEARCHING),
                payload={"project_id": str(project.id)})
            return {**state, "all_sources": [], "research_summary": ""}

        await event_bus.publish(workflow_id, "agent_progress", agent_name="research", status="running",
            message=f"Starting research for {len(tasks)} queries",
            progress_percent=_calc_sub_progress(WorkflowStage.RESEARCHING, 10),
            payload={"project_id": str(project.id), "total_queries": len(tasks)})

        async def bounded_search(query: str, idx: int) -> list[dict]:
            async with _research_semaphore:
                results = await self.research_service.search(query, max_results=5)
                pct = round((idx + 1) / len(tasks) * 90) + 10  # 10% to 100% sub-progress
                await event_bus.publish(workflow_id, "agent_progress", agent_name="research", status="running",
                    message=f"Researched: {query[:60]}... ({len(results)} sources)",
                    progress_percent=_calc_sub_progress(WorkflowStage.RESEARCHING, pct),
                    payload={"query": query, "sources_found": len(results)})
                return results

        coros = [bounded_search(q, i) for i, q in enumerate(tasks)]
        all_results = await asyncio.gather(*coros, return_exceptions=True)

        all_sources = []
        for result in all_results:
            if isinstance(result, Exception):
                self.logger.warning(f"Research task failed: {result}")
                continue
            all_sources.extend(result)

        for src in all_sources:
            try:
                url = src.get("url", "")
                domain = url.split("/")[2] if "://" in url else ""
                await self.source_repo.create(
                    project_id=project.id, url=url, domain=domain,
                    title=src.get("title", ""),
                    snippet=(src.get("content", "") or src.get("snippet", "") or "")[:500],
                )
            except Exception:
                pass

        await event_bus.publish(workflow_id, "agent_completed", agent_name="research", status="completed",
            message=f"Collected {len(all_sources)} sources from {len(tasks)} queries",
            progress_percent=_calc_stage_weight(WorkflowStage.RESEARCHING),
            payload={"project_id": str(project.id), "total_sources": len(all_sources), "total_queries": len(tasks)})

        return {**state, "all_sources": all_sources, "research_summary": f"Collected {len(all_sources)} sources"}

    async def _run_writing(self, project, workflow_id: UUID, state: dict) -> dict:
        await event_bus.publish(workflow_id, "agent_progress", agent_name="writer", status="running",
            message="Writer agent generating content draft",
            progress_percent=_calc_sub_progress(WorkflowStage.WRITING, 10),
            payload={"project_id": str(project.id)})

        from sqlalchemy import select
        lock_stmt = select(ContentLock).where(ContentLock.project_id == project.id)
        lock_result = await self.session.execute(lock_stmt)
        existing_lock = lock_result.scalar_one_or_none()
        if existing_lock:
            raise RuntimeError(f"Content lock held by {existing_lock.locked_by}")
        lock = ContentLock(project_id=project.id, locked_by="writer")
        self.session.add(lock)
        await self.session.flush()

        try:
            content = await self.writer.run(
                title=project.title, outline=state.get("outline", {}),
                verified_claims=[], tone=project.tone,
                target_audience=project.target_audience,
                content_type=project.content_type,
                seo_keywords=project.seo_keywords,
                research_summary=state.get("research_summary", ""), rag_context="",
            )

            markdown = content.get("markdown", "")
            word_count = content.get("word_count", 0) or len(markdown.split())
            citations = content.get("citations", [])
            summary = content.get("summary", "")

            max_ver = await self._get_max_version_number(project.id)
            version = ContentVersion(
                project_id=project.id, version_number=max_ver + 1, agent_name="writer",
                status=ContentVersionStatus.DRAFT, markdown=markdown,
                summary=summary, word_count=word_count, citations=citations,
                seo_metadata=content.get("seo_metadata", {}), overall_confidence=0.7,
                change_description="Initial draft from writer agent",
            )
            self.session.add(version)
            await self.session.flush()

            existing_content = await self.content_repo.get_latest_by_project(project.id)
            if existing_content:
                existing_content.markdown = markdown
                existing_content.summary = summary
                existing_content.word_count = word_count
                existing_content.citations = citations
                existing_content.seo_metadata = content.get("seo_metadata", {})
            else:
                from app.models.content import GeneratedContent
                gc = GeneratedContent(
                    project_id=project.id, markdown=markdown, summary=summary,
                    word_count=word_count, citations=citations,
                    seo_metadata=content.get("seo_metadata", {}), overall_confidence=0.7,
                )
                self.session.add(gc)

            await self.session.flush()
            await event_bus.publish(workflow_id, "draft_ready", agent_name="writer", status="completed",
                message=f"Written {word_count} words with {len(citations)} citations",
                progress_percent=_calc_stage_weight(WorkflowStage.WRITING),
                payload={"project_id": str(project.id), "word_count": word_count, "citations": len(citations)})

        finally:
            await self.session.delete(lock)
            await self.session.flush()

        return {**state, "content_draft": content, "final_content": content}

    async def _publish_draft(self, project_id: UUID, workflow_id: UUID, state: dict) -> Optional[ContentVersion]:
        from sqlalchemy import select
        stmt = (select(ContentVersion).where(ContentVersion.project_id == project_id)
                .order_by(ContentVersion.version_number.desc()).limit(1))
        result = await self.session.execute(stmt)
        version = result.scalar_one_or_none()
        if version:
            version.status = ContentVersionStatus.FINAL

        await event_bus.publish(workflow_id, "stage_completed", agent_name="orchestrator", status="completed",
            message="Draft published and available",
            progress_percent=_calc_stage_weight(WorkflowStage.DRAFT_READY),
            payload={"project_id": str(project_id), "version_id": str(version.id) if version else ""})
        return version

    # ──────────────────────────────────────────────
    # Enhancement agents (user-triggered)
    # ──────────────────────────────────────────────

    async def run_critique(self, project_id: UUID, workflow_id: UUID) -> dict:
        workflow = await self.workflow_repo.get(workflow_id)
        if workflow:
            self._current_stage = WorkflowStage.REVIEW_PENDING
            workflow.current_node = WorkflowStage.REVIEW_PENDING.value
        await self.session.flush()
        await event_bus.publish(workflow_id, "agent_started", agent_name="critique", status="running",
            message="Critique agent analyzing content",
            progress_percent=_calc_sub_progress(WorkflowStage.REVIEW_PENDING, 10),
            payload={"project_id": str(project_id)})
        try:
            content_version = await self._get_latest_version(project_id)
            result = await self.critique.run(
                content={"markdown": content_version.markdown, "citations": content_version.citations} if content_version else {},
                claims=[], outline={},
            )
            needs_revision = result.get("needs_revision", False)
            await event_bus.publish(workflow_id, "agent_completed", agent_name="critique", status="completed",
                message=f"Critique: {'needs revision' if needs_revision else 'looks good'}",
                progress_percent=_calc_stage_weight(WorkflowStage.REVIEW_PENDING),
                payload={"project_id": str(project_id), "needs_revision": needs_revision, **result})
            return result
        except Exception as e:
            await event_bus.publish(workflow_id, "agent_failed", agent_name="critique", status="failed",
                message=f"Critique failed: {str(e)[:200]}",
                payload={"project_id": str(project_id), "error": str(e)})
            raise

    async def run_revision(self, project_id: UUID, workflow_id: UUID) -> dict:
        workflow = await self.workflow_repo.get(workflow_id)
        prev_stage = self._current_stage
        self._current_stage = WorkflowStage.REVISING
        if workflow:
            workflow.current_node = WorkflowStage.REVISING.value
        await self.session.flush()
        await event_bus.publish(workflow_id, "agent_started", agent_name="revision", status="running",
            message="Revision agent incorporating feedback",
            progress_percent=_calc_sub_progress(WorkflowStage.REVISING, 10),
            payload={"project_id": str(project_id)})
        try:
            content_version = await self._get_latest_version(project_id)
            result = await self.revision.run(
                content={"markdown": content_version.markdown, "citations": content_version.citations} if content_version else {},
                critique={}, revision_number=1,
            )
            revised = result.get("content", {})
            markdown = revised.get("markdown", "") or result.get("markdown", "")
            max_ver = await self._get_max_version_number(project_id)
            new_version = ContentVersion(
                project_id=project_id, version_number=max_ver + 1,
                agent_name="revision", status=ContentVersionStatus.REVISED,
                markdown=markdown,
                parent_version_id=content_version.id if content_version else None,
                change_description="Revised by revision agent",
            )
            self.session.add(new_version)
            await self.session.flush()

            self._current_stage = WorkflowStage.DRAFT_READY
            if workflow:
                workflow.current_node = WorkflowStage.DRAFT_READY.value
            await self.session.flush()

            await event_bus.publish(workflow_id, "agent_completed", agent_name="revision", status="completed",
                message=f"Revision complete, new version #{max_ver + 1}",
                progress_percent=_calc_stage_weight(WorkflowStage.REVISING),
                payload={"project_id": str(project_id), "version_number": max_ver + 1})
            return result
        except Exception as e:
            await event_bus.publish(workflow_id, "agent_failed", agent_name="revision", status="failed",
                message=f"Revision failed: {str(e)[:200]}",
                payload={"project_id": str(project_id), "error": str(e)})
            raise

    async def run_verification(self, project_id: UUID, workflow_id: UUID) -> dict:
        workflow = await self.workflow_repo.get(workflow_id)
        self._current_stage = WorkflowStage.VERIFYING
        if workflow:
            workflow.current_node = WorkflowStage.VERIFYING.value
        await self.session.flush()
        await event_bus.publish(workflow_id, "agent_started", agent_name="verification", status="running",
            message="Verification agent checking facts",
            progress_percent=_calc_sub_progress(WorkflowStage.VERIFYING, 10),
            payload={"project_id": str(project_id)})
        try:
            claims_result = await self.verifier.run(research_data="", evidence_sources=[])
            await event_bus.publish(workflow_id, "agent_completed", agent_name="verification", status="completed",
                message="Verification complete",
                progress_percent=_calc_stage_weight(WorkflowStage.VERIFYING),
                payload={"project_id": str(project_id), **claims_result})
            return claims_result
        except Exception as e:
            await event_bus.publish(workflow_id, "agent_failed", agent_name="verification", status="failed",
                message=f"Verification failed: {str(e)[:200]}",
                payload={"project_id": str(project_id), "error": str(e)})
            raise

    async def run_contradiction_detection(self, project_id: UUID, workflow_id: UUID) -> dict:
        await event_bus.publish(workflow_id, "agent_started", agent_name="contradiction_detector", status="running",
            message="Checking for contradictions in claims",
            progress_percent=_calc_sub_progress(WorkflowStage.VERIFYING, 10),
            payload={"project_id": str(project_id)})
        try:
            content_version = await self._get_latest_version(project_id)
            content = {"markdown": content_version.markdown, "citations": content_version.citations} if content_version else {}
            claims = content.get("citations", [])
            result = await self.contradiction_detector.run(
                claims=[{"claim_text": c.get("text", ""), "claim_id": c.get("id", "")} for c in claims],
                sources=[],
            )
            for c in result.get("contradictions", []):
                await self.contradiction_repo.create(
                    project_id=project_id, workflow_id=workflow_id,
                    claim_text=c.get("claim", ""), severity=c.get("severity", "medium"),
                    conflicting_sources=c.get("conflicting_sources", []), explanation=c.get("explanation", ""),
                )
            await self.session.flush()
            await event_bus.publish(workflow_id, "agent_completed", agent_name="contradiction_detector", status="completed",
                message=f"Found {len(result.get('contradictions', []))} contradictions",
                progress_percent=_calc_stage_weight(WorkflowStage.VERIFYING),
                payload={"project_id": str(project_id), "count": len(result.get("contradictions", []))})
            return result
        except Exception as e:
            await event_bus.publish(workflow_id, "agent_failed", agent_name="contradiction_detector", status="failed",
                message=f"Contradiction detection failed: {str(e)[:200]}",
                payload={"project_id": str(project_id), "error": str(e)})
            raise

    async def run_hyperlink_validation(self, project_id: UUID, workflow_id: UUID) -> dict:
        await event_bus.publish(workflow_id, "agent_started", agent_name="hyperlink_validator", status="running",
            message="Validating hyperlinks in content",
            progress_percent=_calc_sub_progress(WorkflowStage.VERIFYING, 10),
            payload={"project_id": str(project_id)})
        try:
            content_version = await self._get_latest_version(project_id)
            content = {"markdown": content_version.markdown, "citations": content_version.citations} if content_version else {}
            result = await self.hyperlink_validator.run(citations=content.get("citations", []), markdown=content.get("markdown", ""))
            for hl in result.get("results", []):
                await self.hyperlink_repo.create(
                    project_id=project_id, url=hl.get("url", ""),
                    label=hl.get("label", ""), status=hl.get("status", "unknown"),
                    is_verified=hl.get("is_verified", False), error_message=hl.get("error_message"),
                )
            await self.session.flush()
            await event_bus.publish(workflow_id, "agent_completed", agent_name="hyperlink_validator", status="completed",
                message=f"Checked {len(result.get('results', []))} hyperlinks",
                progress_percent=_calc_stage_weight(WorkflowStage.VERIFYING),
                payload={"project_id": str(project_id), "count": len(result.get("results", []))})
            return result
        except Exception as e:
            await event_bus.publish(workflow_id, "agent_failed", agent_name="hyperlink_validator", status="failed",
                message=f"Hyperlink validation failed: {str(e)[:200]}",
                payload={"project_id": str(project_id), "error": str(e)})
            raise

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    async def _publish_and_transition(self, stage: WorkflowStage, workflow, event_type: str, agent: str, error: str = None):
        if self._current_stage:
            validate_transition(self._current_stage, stage)
        self._current_stage = stage
        workflow.current_node = stage.value

        if stage in WorkflowStage.terminal():
            workflow.status = WorkflowStatus.completed if stage == WorkflowStage.COMPLETED else (
                WorkflowStatus.failed if stage == WorkflowStage.FAILED else WorkflowStatus.cancelled
            )
            if error:
                workflow.error = error
            workflow.completed_at = utc_now()

        await self.session.flush()
        progress = _calc_stage_weight(stage)
        await event_bus.publish(
            workflow.id, event_type, agent_name=agent, status="completed",
            message=f"Stage: {stage_display_name(stage)}",
            progress_percent=progress,
            payload={"stage": stage.value, "error": error} if error else {"stage": stage.value},
        )
        self.logger.info("Stage transition: %s (%.0f%%)", stage_display_name(stage), progress)

    async def _get_latest_version(self, project_id: UUID) -> Optional[ContentVersion]:
        from sqlalchemy import select
        stmt = (select(ContentVersion).where(ContentVersion.project_id == project_id)
                .order_by(ContentVersion.version_number.desc()).limit(1))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_max_version_number(self, project_id: UUID) -> int:
        from sqlalchemy import select, func
        stmt = select(func.coalesce(func.max(ContentVersion.version_number), 0)).where(
            ContentVersion.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
