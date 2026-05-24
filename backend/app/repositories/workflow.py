from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.repositories.base import BaseRepository
from app.models.workflow import WorkflowExecution, WorkflowStep


class WorkflowExecutionRepository(BaseRepository[WorkflowExecution]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkflowExecution)

    async def get_by_project(self, project_id: UUID) -> list[WorkflowExecution]:
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.project_id == str(project_id))
            .order_by(WorkflowExecution.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_by_project(self, project_id: UUID) -> WorkflowExecution | None:
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.project_id == str(project_id))
            .order_by(WorkflowExecution.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_node(self, workflow_id: str, node: str) -> None:
        await self.session.execute(
            update(WorkflowExecution)
            .where(WorkflowExecution.id == workflow_id)
            .values(current_node=node)
        )
        await self.session.flush()


class WorkflowStepRepository(BaseRepository[WorkflowStep]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkflowStep)

    async def get_by_workflow(self, workflow_id: str) -> list[WorkflowStep]:
        result = await self.session.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.started_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_node(self, workflow_id: str, node_name: str) -> WorkflowStep | None:
        result = await self.session.execute(
            select(WorkflowStep)
            .where(
                WorkflowStep.workflow_id == workflow_id,
                WorkflowStep.node_name == node_name,
            )
            .order_by(WorkflowStep.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
