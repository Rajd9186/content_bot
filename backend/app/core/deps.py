from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Optional

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.unit_of_work import UnitOfWork
from app.domains.workflow.service import WorkflowService
from app.orchestration.orchestrator import Orchestrator, orchestrator


async def get_uow(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UnitOfWork, Any]:
    yield UnitOfWork(db)


async def get_workflow_service(
    uow: UnitOfWork = Depends(get_uow),
) -> AsyncGenerator[WorkflowService, Any]:
    yield WorkflowService(uow)


async def get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "")


async def get_current_user_id(request: Request) -> Optional[str]:
    return getattr(request.state, "user_id", None)


async def get_orchestrator() -> Orchestrator:
    return orchestrator
