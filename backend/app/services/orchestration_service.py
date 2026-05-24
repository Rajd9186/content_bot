import uuid
import time
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


from app.database import async_session_factory


from app.repositories.chat import WorkflowEventRepository


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
            event_callback=self._emit_workflow_event
        )
        self.executor = WorkflowExecutor(self.graph)

    async def _emit_workflow_event(self, project_id: str, node_name: str, event_type: str, message: str, data: dict = None, workflow_id: str = None):
        """Callback for real-time workflow events for visualization"""
        if not project_id:
            return
            
        async with async_session_factory() as session:
            try:
                repo = WorkflowEventRepository(session)
                await repo.create_event(
                    project_id=project_id,
                    node_name=node_name,
                    event_type=event_type,
                    message=message,
                    data=data,
                    workflow_id=workflow_id
                )
                await session.commit()
            except Exception as e:
                self.logger.warning(f"Failed to emit workflow event: {e}")

    async def _update_workflow_status(self, project_id: str, node_name: str):
        """Callback for real-time node status updates"""
        if not project_id:
            return
            
        async with async_session_factory() as session:
            try:
                p_repo = ProjectRepository(session)
                w_repo = WorkflowExecutionRepository(session)
                
                # Update project status based on node
                status_map = {
                    "planner": "planning",
                    "research": "researching",
                    "claim_extraction": "verifying",
                    "contradiction_detection": "verifying",
                    "content_writer": "generating",
                    "critique": "generating",
                    "revision": "generating",
                    "self_verification": "self_verifying",
                    "hyperlink_validation": "verifying"
                }
                
                new_status = status_map.get(node_name)
                if new_status:
                    await p_repo.update_status(uuid.UUID(project_id), new_status)
                
                # Update workflow execution current node
                wf = await w_repo.get_latest_by_project(uuid.UUID(project_id))
                if wf:
                    wf.current_node = node_name
                    await session.commit()
            except Exception as e:
                self.logger.warning(f"Real-time status update failed: {e}")

    async def generate(self, project) -> dict:
        project_id = project.id
        workflow_id = str(uuid.uuid4())

        workflow = await self.workflow_repo.create(
            id=workflow_id,
            project_id=str(project_id),
            status=WorkflowStatus.running,
            current_node="planner",
        )

        await self.project_repo.update_status(project_id, "planning")

        try:
            final_state = await self.executor.execute(
                project_id=str(project_id),
                topic=project.topic,
                title=project.title,
                content_type=project.content_type,
                tone=project.tone,
                points_to_cover=project.points_to_cover,
                target_audience=project.target_audience or "",
                seo_keywords=project.seo_keywords,
                workflow_id=workflow_id,
            )

            await self._persist_workflow_results(workflow_id, final_state)
            await self._persist_content(project_id, final_state)

            await self._save_steps_to_db(workflow_id, final_state)

            telemetry = final_state.get("telemetry", {})
            workflow.telemetry = telemetry
            workflow.status = WorkflowStatus.completed
            workflow.completed_at = datetime.utcnow()
            await self.session.flush()

            await self.project_repo.update_status(project_id, "completed")

            return await self._build_response(project_id, final_state)

        except Exception as e:
            self.logger.error(f"Multi-agent workflow failed: {e}")
            workflow.status = WorkflowStatus.failed
            workflow.error = str(e)
            workflow.completed_at = datetime.utcnow()
            await self.session.flush()
            await self.project_repo.update_status(project_id, "failed")
            raise

    async def _persist_workflow_results(self, workflow_id: str, state: dict) -> None:
        for contradiction in state.get("contradictions", []):
            try:
                await self.contradiction_repo.create(
                    project_id=state["project_id"],
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
                    project_id=state["project_id"],
                    url=hl.get("url", ""),
                    label=hl.get("label", ""),
                    status=hl.get("status", "unknown"),
                    is_verified=hl.get("is_verified", False),
                    error_message=hl.get("error_message"),
                )
            except Exception as e:
                self.logger.warning(f"Failed to persist hyperlink: {e}")

    async def _persist_content(self, project_id, state: dict) -> None:
        final_content = state.get("final_content", state.get("content_draft", {}))
        if not final_content or not final_content.get("markdown"):
            self.logger.warning("No content to persist")
            return

        content = state.get("content_draft", {})
        citations = content.get("citations", [])
        seo = content.get("seo_metadata", {})
        word_count = content.get("word_count", 0)
        summary = content.get("summary", "")
        telemetry = state.get("telemetry", {})
        overall_confidence = telemetry.get("overall_quality_score", 0.7)

        await self.content_repo.create(
            project_id=project_id,
            markdown=final_content.get("markdown", ""),
            summary=summary,
            word_count=word_count,
            citations=citations,
            seo_metadata=seo,
            overall_confidence=overall_confidence,
        )

        await self.project_repo.update(project_id, outline=state.get("outline", {}))

        for claim_data in state.get("claims", []):
            try:
                await self.claim_repo.create(
                    project_id=project_id,
                    claim_text=claim_data.get("claim_text", ""),
                    confidence=claim_data.get("confidence"),
                    status=claim_data.get("status", "unverified"),
                    explanation=claim_data.get("explanation"),
                    category=claim_data.get("category"),
                )
            except Exception:
                pass

        for source in state.get("all_sources", []):
            try:
                url = source.get("url", "")
                domain = url.split("/")[2] if "://" in url else ""
                await self.source_repo.create(
                    project_id=project_id,
                    url=url,
                    domain=domain,
                    title=source.get("title", ""),
                    snippet=(source.get("content", "") or source.get("snippet", "") or "")[:500],
                )
            except Exception:
                pass

    async def _save_steps_to_db(self, workflow_id: str, state: dict) -> None:
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

    async def _build_response(self, project_id, state: dict) -> dict:
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
                {
                    "id": str(c.id),
                    "claim_text": c.claim_text,
                    "confidence": c.confidence,
                    "status": c.status,
                }
                for c in claims
            ],
            "contradictions": [
                {
                    "id": c.id,
                    "claim_text": c.claim_text,
                    "severity": c.severity,
                    "explanation": c.explanation,
                }
                for c in contradictions
            ],
            "hyperlinks": [
                {
                    "id": h.id,
                    "url": h.url,
                    "status": h.status,
                    "is_verified": h.is_verified,
                }
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
            "workflow_id": state.get("workflow_id", ""),
        }
