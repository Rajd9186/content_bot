from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select, update

from app.infrastructure.models.pipeline import PipelineRun
from app.infrastructure.models.telemetry import Checkpoint
from app.infrastructure.repositories.base import BaseRepository
from app.pipeline.state import (
    HumanReview,
    NodeResult,
    NodeStatus,
    PipelineState,
    ReviewAction,
)


class PipelineRepository(BaseRepository[PipelineRun]):
    async def get_by_id(self, entity_id: str) -> PipelineRun | None:
        try:
            return await self.session.get(PipelineRun, entity_id)
        except Exception:
            return None

    async def get_by_workflow_id(self, workflow_id: str) -> PipelineRun | None:
        stmt = select(PipelineRun).where(PipelineRun.workflow_id == workflow_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PipelineRun]:
        stmt = select(PipelineRun).where(PipelineRun.workspace_id == workspace_id)
        if status:
            stmt = stmt.where(PipelineRun.status == status)
        stmt = stmt.order_by(PipelineRun.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        workflow_id: str,
        status: str,
        current_node: str | None = None,
        expected_version: int | None = None,
    ) -> bool:
        values: dict = {"status": status, "updated_at": datetime.now(UTC)}
        if current_node is not None:
            values["current_node"] = current_node
        stmt = (
            update(PipelineRun)
            .where(PipelineRun.workflow_id == workflow_id)
            .values(**values)
        )
        if expected_version is not None:
            stmt = stmt.where(PipelineRun.version == expected_version)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def heartbeat(self, workflow_id: str) -> bool:
        stmt = (
            update(PipelineRun)
            .where(PipelineRun.workflow_id == workflow_id)
            .values(heartbeat_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def get_active_pipelines(self, limit: int = 100) -> list[PipelineRun]:
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.status.in_(["pending", "running"]))
            .order_by(PipelineRun.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_zombie_pipelines(
        self,
        timeout_minutes: int = 5,
        limit: int = 50,
    ) -> list[PipelineRun]:

        cutoff = datetime.now(UTC) - __import__("datetime").timedelta(minutes=timeout_minutes)
        stmt = (
            select(PipelineRun)
            .where(
                and_(
                    PipelineRun.status.in_(["pending", "running"]),
                    PipelineRun.heartbeat_at < cutoff,
                )
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_pipeline_state(self, state: PipelineState) -> PipelineRun:
        existing = await self.get_by_workflow_id(state.workflow_id)
        node_results_data = {
            k: {
                "node": v.node,
                "status": v.status.value,
                "output": v.output,
                "actions": v.actions, # Persist actions
                "error": v.error,
                "retry_count": v.retry_count,
                "started_at": v.started_at,
                "completed_at": v.completed_at,
                "tokens_used": v.tokens_used,
                "latency_ms": v.latency_ms,
            }
            for k, v in state.node_results.items()
        }
        total_tokens = sum(v.tokens_used for v in state.node_results.values())
        total_latency = sum(v.latency_ms for v in state.node_results.values())

        if existing:
            existing.workspace_id = state.workspace_id
            existing.correlation_id = state.correlation_id
            existing.content_item_id = state.content_item_id
            existing.current_node = state.current_node
            existing.topic = state.topic
            existing.audience = state.audience
            existing.tone = state.tone
            existing.goals = state.goals
            existing.research_data = state.research_data or None
            existing.plan = state.plan or None
            existing.outline = state.outline or None
            existing.draft_content = state.draft_content or None
            existing.seo_metadata = state.seo_metadata or None
            existing.fact_check_results = state.fact_check_results or None
            existing.compliance_results = state.compliance_results or None
            existing.vlog_links = state.vlog_links or None # Persist vlog_links
            existing.final_content = state.final_content or None
            existing.human_review = state.human_review.model_dump() if state.human_review else None
            existing.node_results = node_results_data
            existing.errors = {"errors": state.errors} if state.errors else None
            existing.error_count = len(state.errors)
            existing.total_tokens_used = total_tokens
            existing.total_latency_ms = total_latency
            existing.metadata_ = state.metadata or None
            existing.version = (existing.version or 0) + 1
            existing.updated_at = datetime.now(UTC)
            if state.all_nodes_completed():
                existing.status = "completed"
                existing.completed_at = datetime.now(UTC)
            elif state.has_failures():
                existing.status = "failed"
                existing.completed_at = datetime.now(UTC)
            else:
                existing.status = "running"
            await self.session.flush()
            return existing
        else:
            run = PipelineRun(
                workflow_id=state.workflow_id,
                workspace_id=state.workspace_id,
                correlation_id=state.correlation_id,
                content_item_id=state.content_item_id,
                status="pending",
                current_node=state.current_node,
                topic=state.topic,
                audience=state.audience,
                tone=state.tone,
                goals=state.goals,
                research_data=state.research_data or None,
                plan=state.plan or None,
                outline=state.outline or None,
                draft_content=state.draft_content or None,
                seo_metadata=state.seo_metadata or None,
                fact_check_results=state.fact_check_results or None,
                compliance_results=state.compliance_results or None,
                vlog_links=state.vlog_links or None, # Persist vlog_links
                final_content=state.final_content or None,
                human_review=state.human_review.model_dump() if state.human_review else None,
                node_results=node_results_data,
                errors={"errors": state.errors} if state.errors else None,
                error_count=len(state.errors),
                total_tokens_used=total_tokens,
                total_latency_ms=total_latency,
                metadata_=state.metadata or None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            self.session.add(run)
            await self.session.flush()
            return run

    def to_pipeline_state(self, run: PipelineRun) -> PipelineState:
        node_results = {}
        for k, v in (run.node_results or {}).items():
            node_results[k] = NodeResult(
                node=v.get("node", k),
                status=NodeStatus(v.get("status", "pending")),
                output=v.get("output", {}),
                error=v.get("error"),
                retry_count=v.get("retry_count", 0),
                started_at=v.get("started_at"),
                completed_at=v.get("completed_at"),
                tokens_used=v.get("tokens_used", 0),
                latency_ms=v.get("latency_ms", 0.0),
                actions=v.get("actions", []), # Restore actions
            )

        human_review = None
        if run.human_review:
            hr = run.human_review
            human_review = HumanReview(
                reviewer_id=hr.get("reviewer_id"),
                action=ReviewAction(hr["action"]) if hr.get("action") else None,
                comments=hr.get("comments", ""),
                reviewed_at=hr.get("reviewed_at"),
            )

        errors = []
        if run.errors and isinstance(run.errors, dict):
            errors = run.errors.get("errors", [])

        return PipelineState(
            workflow_id=run.workflow_id,
            workspace_id=run.workspace_id,
            correlation_id=run.correlation_id,
            content_item_id=run.content_item_id,
            topic=run.topic or "",
            audience=run.audience or "general",
            tone=run.tone or "professional",
            goals=run.goals or "",
            research_data=run.research_data or {},
            plan=run.plan or {},
            outline=run.outline or {},
            draft_content=run.draft_content or "",
            seo_metadata=run.seo_metadata or {},
            fact_check_results=run.fact_check_results or {},
            compliance_results=run.compliance_results or {},
            vlog_links=run.vlog_links or [], # Restore vlog_links
            final_content=run.final_content or "",
            human_review=human_review,
            node_results=node_results,
            errors=errors,
            current_node=run.current_node or "research",
            metadata=run.metadata_ or {},
            created_at=run.created_at.isoformat() if run.created_at else "",
            updated_at=run.updated_at.isoformat() if run.updated_at else "",
        )


class CheckpointRepository(BaseRepository[Checkpoint]):
    async def get_by_id(self, entity_id: str) -> Checkpoint | None:
        return await self.session.get(Checkpoint, entity_id)

    async def get_by_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
        checkpoint_type: str | None = None,
        limit: int = 10,
    ) -> list[Checkpoint]:
        stmt = select(Checkpoint).where(
            and_(
                Checkpoint.aggregate_type == aggregate_type,
                Checkpoint.aggregate_id == aggregate_id,
            )
        )
        if checkpoint_type:
            stmt = stmt.where(Checkpoint.checkpoint_type == checkpoint_type)
        stmt = stmt.order_by(Checkpoint.version.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_checkpoint(
        self,
        aggregate_id: str,
        aggregate_type: str,
        checkpoint_type: str,
        state: dict,
        version: int = 1,
    ) -> Checkpoint:
        existing_stmt = select(Checkpoint).where(
            and_(
                Checkpoint.aggregate_type == aggregate_type,
                Checkpoint.aggregate_id == aggregate_id,
                Checkpoint.checkpoint_type == checkpoint_type,
            )
        )
        result = await self.session.execute(existing_stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.state = state
            existing.version = version
            existing.updated_at = datetime.now(UTC)
            await self.session.flush()
            return existing
        else:
            checkpoint = Checkpoint(
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                checkpoint_type=checkpoint_type,
                state=state,
                version=version,
            )
            self.session.add(checkpoint)
            await self.session.flush()
            return checkpoint

    async def get_latest_checkpoint(
        self,
        aggregate_type: str,
        aggregate_id: str,
        checkpoint_type: str,
    ) -> Checkpoint | None:
        stmt = (
            select(Checkpoint)
            .where(
                and_(
                    Checkpoint.aggregate_type == aggregate_type,
                    Checkpoint.aggregate_id == aggregate_id,
                    Checkpoint.checkpoint_type == checkpoint_type,
                )
            )
            .order_by(Checkpoint.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
