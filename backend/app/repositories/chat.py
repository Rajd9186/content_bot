from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import WorkflowEventModel
from app.repositories.base import BaseRepository

class WorkflowEventRepository(BaseRepository[WorkflowEventModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkflowEventModel)

    async def create_event(
        self,
        project_id: str,
        node_name: str,
        event_type: str,
        message: str,
        data: dict = None,
        workflow_id: str = None
    ) -> WorkflowEventModel:
        event = WorkflowEventModel(
            project_id=project_id,
            node_name=node_name,
            event_type=event_type,
            message=message,
            data=data,
            workflow_id=workflow_id
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_project(self, project_id: str, limit: int = 50) -> List[WorkflowEventModel]:
        stmt = (
            select(WorkflowEventModel)
            .where(WorkflowEventModel.project_id == project_id)
            .order_by(WorkflowEventModel.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
