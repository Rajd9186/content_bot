from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import WorkflowEventRecord
from app.repositories.base import BaseRepository


class WorkflowEventRepository(BaseRepository[WorkflowEventRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkflowEventRecord)

    async def create_event(
        self,
        project_id: UUID,
        node_name: str,
        event_type: str,
        message: str,
        data: dict = None,
        workflow_id: UUID = None,
    ) -> WorkflowEventRecord:
        event = WorkflowEventRecord(
            project_id=project_id,
            agent_name=node_name,
            event_type=event_type,
            message=message,
            payload_json=data or {},
            workflow_id=workflow_id,
            status="running",
        )
        self.session.add(event)
        return event

    async def get_by_project(self, project_id: UUID, limit: int = 50) -> List[WorkflowEventRecord]:
        stmt = (
            select(WorkflowEventRecord)
            .where(WorkflowEventRecord.project_id == project_id)
            .order_by(WorkflowEventRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
