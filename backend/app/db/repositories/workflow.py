from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workflow import WorkflowJob, WorkflowStep, ExecutionLog, DeadLetterJob
from app.db.repositories import BaseRepository


class WorkflowRepository(BaseRepository[WorkflowJob]):
    async def get_by_id(self, job_id: str) -> Optional[WorkflowJob]:
        return await self.session.get(WorkflowJob, job_id)

    async def get_by_workspace(
        self, workspace_id: str, status: Optional[str] = None,
        limit: int = 50, offset: int = 0,
    ) -> list[WorkflowJob]:
        stmt = select(WorkflowJob).where(
            WorkflowJob.workspace_id == workspace_id
        )
        if status:
            stmt = stmt.where(WorkflowJob.status == status)
        stmt = stmt.order_by(WorkflowJob.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, job_id: str, status: str, expected_version: int,
        processing_stage: Optional[str] = None,
    ) -> Optional[WorkflowJob]:
        values = {
            "status": status,
            "version": WorkflowJob.version + 1,
        }
        if processing_stage is not None:
            values["processing_stage"] = processing_stage

        stmt = (
            update(WorkflowJob)
            .where(and_(
                WorkflowJob.id == job_id,
                WorkflowJob.version == expected_version,
            ))
            .values(**values)
            .returning(WorkflowJob)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_log(self, log: ExecutionLog) -> ExecutionLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_logs(self, job_id: str, limit: int = 100) -> list[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.job_id == job_id)
            .order_by(ExecutionLog.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_steps(self, job_id: str) -> list[WorkflowStep]:
        stmt = (
            select(WorkflowStep)
            .where(WorkflowStep.job_id == job_id)
            .order_by(WorkflowStep.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_dead_letter(self, entry: DeadLetterJob) -> DeadLetterJob:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_pending_retries(
        self, target_type: str, target_id: str,
    ) -> list[DeadLetterJob]:
        stmt = (
            select(DeadLetterJob)
            .where(DeadLetterJob.original_job_id == target_id)
            .order_by(DeadLetterJob.failed_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
