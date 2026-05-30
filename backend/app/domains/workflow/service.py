from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from app.domains.workflow.models import (
    ExecutionLog,
    WorkflowJob,
    WorkflowStep,
)
from app.domains.workflow.retry_service import retry_service
from app.domains.workflow.state_machine import (
    WorkflowStatus,
    workflow_state_machine,
)
from app.events.event_bus import event_bus
from app.events.event_types import (
    JobCanceledEvent,
    JobCompletedEvent,
    JobFailedEvent,
    JobRetriedEvent,
    JobStageChangedEvent,
    JobStartedEvent,
)
from app.infrastructure.unit_of_work import UnitOfWork
from app.infrastructure.websocket.broadcaster import event_broadcaster

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
        self.repo = uow.workflows

    async def create_job(
        self,
        workspace_id: str,
        created_by: str,
        correlation_id: str,
        content_item_id: str | None = None,
    ) -> WorkflowJob:
        job = WorkflowJob(
            id=str(uuid4()),
            workspace_id=workspace_id,
            content_item_id=content_item_id,
            created_by=created_by,
            correlation_id=correlation_id,
            status=WorkflowStatus.DRAFT.value,
        )
        created = await self.repo.add(job)

        await self._log_transition(created.id, None, WorkflowStatus.DRAFT.value,
                                   "create", created_by, correlation_id)

        event = JobStartedEvent(
            correlation_id=correlation_id,
            subject=created.id,
            data={"workspace_id": workspace_id, "content_item_id": content_item_id},
        )
        await event_bus.store_atomic(self.uow, event)
        await event_broadcaster.broadcast_event(event, workspace_id=workspace_id)

        return created

    async def transition_job(
        self,
        job_id: str,
        to_status: str,
        workspace_id: str,
        triggered_by: str,
        correlation_id: str,
        context: dict[str, Any] | None = None,
    ) -> WorkflowJob:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        from_status = job.status
        await workflow_state_machine.transition(
            from_status, to_status, job_id, workspace_id, context or {},
        )

        updated = await self.repo.update_status(
            job_id, to_status, job.version,
        )
        if not updated:
            raise ValueError(
                f"Optimistic lock conflict on job {job_id}: "
                f"expected version {job.version}"
            )

        await self._log_transition(job_id, from_status, to_status,
                                   f"{from_status}->{to_status}",
                                   triggered_by, correlation_id)

        if to_status == WorkflowStatus.COMPLETED.value:
            event = JobCompletedEvent(
                correlation_id=correlation_id,
                subject=job_id,
                data={"workspace_id": workspace_id},
            )
            await event_bus.store_atomic(self.uow, event)
            await event_broadcaster.broadcast_job_completed(
                job_id, to_status, correlation_id, workspace_id,
            )

        elif to_status == WorkflowStatus.FAILED.value:
            event = JobFailedEvent(
                correlation_id=correlation_id,
                subject=job_id,
                data={
                    "workspace_id": workspace_id,
                    "error_code": (context or {}).get("error_code", "UNKNOWN"),
                    "error_message": (context or {}).get("error_message", ""),
                },
            )
            await event_bus.store_atomic(self.uow, event)

        elif to_status == WorkflowStatus.CANCELED.value:
            event = JobCanceledEvent(
                correlation_id=correlation_id,
                subject=job_id,
                data={"workspace_id": workspace_id},
            )
            await event_bus.store_atomic(self.uow, event)

        elif to_status == WorkflowStatus.RETRYING.value:
            event = JobRetriedEvent(
                correlation_id=correlation_id,
                subject=job_id,
                data={
                    "attempt": (job.retry_count or 0) + 1,
                    "max_retries": job.max_retries or 3,
                },
            )
            await event_bus.store_atomic(self.uow, event)

        else:
            event = JobStageChangedEvent(
                correlation_id=correlation_id,
                subject=job_id,
                data={
                    "from_stage": from_status,
                    "to_stage": to_status,
                    "workspace_id": workspace_id,
                },
            )
            await event_bus.store_atomic(self.uow, event)
            await event_broadcaster.broadcast_stage_change(
                job_id, from_status, to_status, correlation_id, workspace_id,
            )

        return updated

    async def fail_with_retry(
        self,
        job_id: str,
        workspace_id: str,
        triggered_by: str,
        correlation_id: str,
        error_code: str,
        error_message: str,
        max_retries: int = 3,
    ) -> WorkflowJob:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        current_retry = job.retry_count or 0
        if current_retry < max_retries:
            retry_service.session = self.uow._session
            await retry_service.record_attempt(
                self.uow, "workflow_job", job_id,
                attempt_number=current_retry + 1,
                max_retries=max_retries,
                error_code=error_code,
                error_message=error_message,
            )
            return await self.transition_job(
                job_id, WorkflowStatus.RETRYING.value,
                workspace_id, triggered_by, correlation_id,
                context={"error_code": error_code, "error_message": error_message},
            )

        retry_service.session = self.uow._session
        await retry_service.record_dead_letter(
            self.uow, job_id, error_code, error_message,
            retry_attempts=current_retry,
        )
        return await self.transition_job(
            job_id, WorkflowStatus.FAILED.value,
            workspace_id, triggered_by, correlation_id,
            context={"error_code": error_code, "error_message": error_message},
        )

    async def submit_job(self, job_id: str, workspace_id: str,
                         triggered_by: str, correlation_id: str) -> WorkflowJob:
        return await self.transition_job(
            job_id, WorkflowStatus.QUEUED.value,
            workspace_id, triggered_by, correlation_id,
        )

    async def validate_job(self, job_id: str, workspace_id: str,
                           triggered_by: str, correlation_id: str) -> WorkflowJob:
        return await self.transition_job(
            job_id, WorkflowStatus.VALIDATING.value,
            workspace_id, triggered_by, correlation_id,
        )

    async def process_job(self, job_id: str, workspace_id: str,
                          triggered_by: str, correlation_id: str) -> WorkflowJob:
        return await self.transition_job(
            job_id, WorkflowStatus.PROCESSING.value,
            workspace_id, triggered_by, correlation_id,
        )

    async def complete_job(self, job_id: str, workspace_id: str,
                           triggered_by: str, correlation_id: str) -> WorkflowJob:
        return await self.transition_job(
            job_id, WorkflowStatus.COMPLETED.value,
            workspace_id, triggered_by, correlation_id,
        )

    async def cancel_job(self, job_id: str, workspace_id: str,
                         triggered_by: str, correlation_id: str) -> WorkflowJob:
        return await self.transition_job(
            job_id, WorkflowStatus.CANCELED.value,
            workspace_id, triggered_by, correlation_id,
        )

    async def add_step(self, job_id: str, step_type: str,
                       triggered_by: str) -> WorkflowStep:
        step = WorkflowStep(
            id=str(uuid4()),
            job_id=job_id,
            step_type=step_type,
        )
        return await self.repo.add(step)

    async def _log_transition(
        self, job_id: str, from_status: str | None, to_status: str,
        transition: str, triggered_by: str, correlation_id: str,
    ) -> ExecutionLog:
        log = ExecutionLog(
            id=str(uuid4()),
            job_id=job_id,
            from_status=from_status,
            to_status=to_status,
            transition=transition,
            triggered_by=triggered_by,
            correlation_id=correlation_id,
        )
        return await self.repo.add_log(log)
