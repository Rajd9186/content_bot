import uuid
import time
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.log_config.logger import get_logger
from app.repositories.project import ProjectRepository
from app.repositories.content import ContentRepository
from app.repositories.claim import ClaimRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.source import SourceRepository
from app.repositories.workflow import WorkflowExecutionRepository, WorkflowStepRepository
from app.repositories.contradiction import ContradictionRepository
from app.repositories.hyperlink import HyperlinkValidationRepository
from app.repositories.chat import WorkflowEventRepository

from app.agents.task_planner import TaskPlannerAgent
from app.agents.verifier import VerificationAgent
from app.agents.content_writer import ContentWriterAgent
from app.agents.self_verifier import SelfVerificationAgent
from app.agents.contradiction_detector import ContradictionDetectionAgent
from app.agents.critique import CritiqueAgent
from app.agents.revision import RevisionAgent
from app.agents.hyperlink_validator import HyperlinkValidationAgent

from app.services.research_service import ResearchService
from app.memory.agent_memory import AgentMemoryService
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import LocalVectorStore
from app.engine import build_workflow_graph, WorkflowExecutor
from app.models.workflow import WorkflowStatus
from app.models.content import GeneratedContent

from app.config import settings
from app.database import async_session_factory


class MultiAgentOrchestrator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(self.__class__.__name__)

        self.project_repo = ProjectRepository(session)
        self.content_repo = ContentRepository(session)
        self.claim_repo = ClaimRepository(session)
        self.evidence_repo = EvidenceRepository(session)
        self.source_repo = SourceRepository(session)
        self.workflow_repo = WorkflowExecutionRepository(session)
        self.workflow_step_repo = WorkflowStepRepository(session)
        self.contradiction_repo = ContradictionRepository(session)
        self.hyperlink_repo = HyperlinkValidationRepository(session)
        self.event_repo = WorkflowEventRepository(session)

        self.research_service = ResearchService()
        self.memory_service = AgentMemoryService(None)
        self.embedding_service = EmbeddingService()
        self.vector_store = LocalVectorStore(self.embedding_service)

        self.planner = TaskPlannerAgent()
        self.verifier = VerificationAgent()
        self.writer = ContentWriterAgent()
        self.self_verifier = SelfVerificationAgent()
        self.contradiction_detector = ContradictionDetectionAgent()
        self.critique = CritiqueAgent()
        self.revision = RevisionAgent()
        self.hyperlink_validator = HyperlinkValidationAgent()

        self.logger.info("Building workflow graph with all agents")
        self.graph = build_workflow_graph(
            planner_agent=self.planner,
            research_service=self.research_service,
            memory_service=self.memory_service,
            verifier_agent=self.verifier,
            contradiction_agent=self.contradiction_detector,
            writer_agent=self.writer,
            critique_agent=self.critique,
            revision_agent=self.revision,
            self_verifier_agent=self.self_verifier,
            hyperlink_agent=self.hyperlink_validator,
            vector_store=self.vector_store,
            status_callback=self._update_workflow_status,
            event_callback=self._buffer_workflow_event,
        )
        self.executor = WorkflowExecutor(self.graph)

        # Event batching
        self._event_buffer: list[dict] = []
        self._event_flush_task: asyncio.Task | None = None
        self._flush_lock = asyncio.Lock()

    async def _start_event_flusher(self):
        interval = settings.workflow_event_flush_interval
        while True:
            await asyncio.sleep(interval)
            await self._flush_events()

    async def _flush_events(self):
        if not self._event_buffer:
            return
        async with self._flush_lock:
            batch = self._event_buffer[:]
            self._event_buffer.clear()
        if not batch:
            return
        try:
            for event_data in batch:
                self.event_repo.session.add(
                    __import__("app.models.chat", fromlist=["WorkflowEventModel"]).WorkflowEventModel(
                        project_id=event_data["project_id"],
                        node_name=event_data["node_name"],
                        event_type=event_data["event_type"],
                        message=event_data["message"],
                        data=event_data.get("data") or {},
                        workflow_id=event_data.get("workflow_id"),
                    )
                )
            await self.session.flush()
            self.logger.debug(f"Flushed {len(batch)} workflow events to DB")
        except Exception as e:
            self.logger.warning(f"Failed to flush {len(batch)} workflow events: {e}")

    async def _buffer_workflow_event(
        self, project_id: str, node_name: str, event_type: str,
        message: str, data: dict = None, workflow_id: str = None,
    ):
        self._event_buffer.append({
            "project_id": uuid.UUID(project_id) if isinstance(project_id, str) else project_id,
            "node_name": node_name,
            "event_type": event_type,
            "message": message,
            "data": data or {},
            "workflow_id": uuid.UUID(workflow_id) if (workflow_id and isinstance(workflow_id, str)) else workflow_id,
        })
        if len(self._event_buffer) >= settings.workflow_event_buffer_size:
            await self._flush_events()

    async def _update_workflow_status(self, project_id: str, node_name: str):
        if not project_id:
            return
        try:
            pid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
            status_map = {
                "planner": "planning",
                "research": "researching",
                "claim_extraction": "verifying",
                "contradiction_detection": "verifying",
                "content_writer": "generating",
                "critique": "generating",
                "revision": "generating",
                "self_verification": "self_verifying",
                "hyperlink_validation": "verifying",
            }
            new_status = status_map.get(node_name)
            if new_status:
                await self.project_repo.update_status(pid, new_status)

            wf = await self.workflow_repo.get_latest_by_project(pid)
            if wf:
                wf.current_node = node_name
            self.logger.info(f"Workflow status update: node={node_name}, project_status={new_status}")
        except Exception as e:
            self.logger.warning(f"Status update failed for node {node_name}: {e}")

    async def generate(self, project) -> dict:
        project_id = project.id
        workflow_id = uuid.uuid4()

        self._event_flush_task = asyncio.create_task(self._start_event_flusher())

        self.logger.info(
            "Creating workflow execution record",
            extra={"project_id": str(project_id), "workflow_id": str(workflow_id)},
        )
        workflow = await self.workflow_repo.create(
            id=workflow_id,
            project_id=project_id,
            status=WorkflowStatus.running,
            current_node="planner",
        )
        await self.project_repo.update_status(project_id, "planning")
        await self.session.flush()

        try:
            self.logger.info(
                "Starting LangGraph workflow execution",
                extra={"project_id": str(project_id), "workflow_id": str(workflow_id)},
            )
            final_state = await self.executor.execute(
                project_id=str(project_id),
                topic=project.topic,
                title=project.title,
                content_type=project.content_type,
                tone=project.tone,
                points_to_cover=project.points_to_cover,
                target_audience=project.target_audience or "",
                seo_keywords=project.seo_keywords,
                workflow_id=str(workflow_id),
            )

            self.logger.info(
                "LangGraph execution completed, persisting results",
                extra={
                    "project_id": str(project_id),
                    "steps_completed": len(final_state.get("steps_completed", [])),
                    "has_content": bool(final_state.get("final_content") or final_state.get("content_draft")),
                },
            )

            await self._flush_events()
            await self._persist_workflow_results(workflow_id, final_state)

            # Persist content with its own dedicated commit for durability
            content_persisted = await self._persist_content(project_id, final_state)

            await self._save_steps_to_db(workflow_id, final_state)

            telemetry = final_state.get("telemetry", {})
            workflow.telemetry = telemetry
            workflow.status = WorkflowStatus.completed
            workflow.completed_at = datetime.utcnow()

            await self.project_repo.update_status(project_id, "completed")
            await self.session.flush()

            self.logger.info(
                "Workflow completed successfully",
                extra={
                    "project_id": str(project_id),
                    "workflow_id": str(workflow_id),
                    "content_persisted": content_persisted,
                    "telemetry": telemetry,
                },
            )

            return await self._build_response(project_id, final_state)

        except Exception as e:
            self.logger.error(f"Multi-agent workflow failed: {e}", exc_info=True)
            try:
                await self._flush_events()
            except Exception:
                pass
            workflow.status = WorkflowStatus.failed
            workflow.error = str(e)
            workflow.completed_at = datetime.utcnow()
            await self.project_repo.update_status(project_id, "failed")
            await self.session.flush()
            raise
        finally:
            if self._event_flush_task and not self._event_flush_task.done():
                self._event_flush_task.cancel()
                try:
                    await self._event_flush_task
                except asyncio.CancelledError:
                    pass

    async def _persist_content(self, project_id: uuid.UUID, state: dict) -> bool:
        """Persist generated content to the database with its own commit.

        Returns True if content was persisted, False otherwise.
        """
        final_content = state.get("final_content", state.get("content_draft", {}))
        if not final_content or not final_content.get("markdown"):
            self.logger.warning(
                "No content to persist — final_content or markdown is empty",
                extra={
                    "has_final_content": "final_content" in state,
                    "has_content_draft": "content_draft" in state,
                    "final_content_keys": list(final_content.keys()) if final_content else [],
                },
            )
            return False

        content = state.get("content_draft", {})
        citations = content.get("citations", [])
        seo = content.get("seo_metadata", {})
        word_count = content.get("word_count", 0)
        summary = content.get("summary", "")
        telemetry = state.get("telemetry", {})
        overall_confidence = telemetry.get("overall_quality_score", 0.7)

        markdown_len = len(final_content.get("markdown", ""))
        self.logger.info(
            "Persisting generated content",
            extra={
                "project_id": str(project_id),
                "markdown_length": markdown_len,
                "citations_count": len(citations),
                "word_count": word_count,
            },
        )

        try:
            content_entry = GeneratedContent(
                project_id=project_id,
                markdown=final_content.get("markdown", ""),
                summary=summary,
                word_count=word_count,
                citations=citations,
                seo_metadata=seo,
                overall_confidence=overall_confidence,
            )
            self.session.add(content_entry)
            await self.session.flush()
            self.logger.info(
                "Content persisted with ID: %s",
                str(content_entry.id),
                extra={"content_id": str(content_entry.id)},
            )
            return True
        except Exception as e:
            self.logger.error(
                "Failed to persist content: %s",
                str(e),
                exc_info=True,
            )
            raise

    async def _persist_workflow_results(self, workflow_id: uuid.UUID, state: dict) -> None:
        for contradiction in state.get("contradictions", []):
            try:
                await self.contradiction_repo.create(
                    project_id=uuid.UUID(state["project_id"]),
                    workflow_id=workflow_id,
                    claim_text=contradiction.get("claim", ""),
                    severity=contradiction.get("severity", "medium"),
                    conflicting_sources=contradiction.get("conflicting_sources", []),
                    explanation=contradiction.get("explanation", ""),
                )
            except Exception as e:
                self.logger.warning(f"Failed to persist contradiction: {e}")

        for hl in state.get("hyperlink_results", []):
            try:
                await self.hyperlink_repo.create(
                    project_id=uuid.UUID(state["project_id"]),
                    url=hl.get("url", ""),
                    label=hl.get("label", ""),
                    status=hl.get("status", "unknown"),
                    is_verified=hl.get("is_verified", False),
                    error_message=hl.get("error_message"),
                )
            except Exception as e:
                self.logger.warning(f"Failed to persist hyperlink: {e}")

    async def _save_steps_to_db(self, workflow_id: uuid.UUID, state: dict) -> None:
        steps = state.get("steps_completed", [])
        node_durations = state.get("telemetry", {}).get("node_durations", {})
        for step_name in steps:
            try:
                await self.workflow_step_repo.create(
                    workflow_id=workflow_id,
                    node_name=step_name.replace("_failed", ""),
                    status="failed" if step_name.endswith("_failed") else "completed",
                    duration_ms=node_durations.get(step_name.replace("_failed", "")),
                    completed_at=datetime.utcnow(),
                )
            except Exception:
                pass

    async def _build_response(self, project_id: uuid.UUID, state: dict) -> dict:
        claims = await self.claim_repo.get_by_project(project_id)
        content_list = await self.content_repo.get_by_project(project_id)
        latest_content = content_list[0] if content_list else None
        contradictions = await self.contradiction_repo.get_by_project(project_id)
        hyperlinks = await self.hyperlink_repo.get_by_project(project_id)
        telemetry = state.get("telemetry", {})

        return {
            "project_id": str(project_id),
            "content_id": str(latest_content.id) if latest_content else "",
            "markdown": latest_content.markdown if latest_content else "",
            "summary": latest_content.summary if latest_content else "",
            "word_count": latest_content.word_count if latest_content else 0,
            "citations": latest_content.citations if latest_content else [],
            "seo_metadata": latest_content.seo_metadata or {},
            "overall_confidence": telemetry.get("overall_quality_score", 0.0),
            "claims": [
                {"id": str(c.id), "claim_text": c.claim_text,
                 "confidence": c.confidence, "status": c.status}
                for c in claims
            ],
            "contradictions": [
                {"id": str(c.id), "claim_text": c.claim_text,
                 "severity": c.severity, "explanation": c.explanation}
                for c in contradictions
            ],
            "hyperlinks": [
                {"id": str(h.id), "url": h.url,
                 "status": h.status, "is_verified": h.is_verified}
                for h in hyperlinks
            ],
            "telemetry": {
                "total_duration_ms": telemetry.get("total_duration_ms", 0),
                "node_durations": telemetry.get("node_durations", {}),
                "total_sources": telemetry.get("total_sources", 0),
                "total_claims": telemetry.get("total_claims", 0),
                "total_contradictions": len(contradictions),
                "revision_count": telemetry.get("revision_count", 0),
                "overall_quality_score": telemetry.get("overall_quality_score", 0.0),
            },
            "steps_completed": state.get("steps_completed", []),
            "workflow_id": str(state.get("workflow_id", "")),
        }
