from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_uow
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(tags=["content"])


@router.get(
    "/items",
    summary="List content items for a workspace",
    operation_id="listContentItems",
)
async def list_items(
    workspace_id: str,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
):
    items = await uow.content.get_by_workspace(workspace_id, status, limit, offset)
    return [
        {
            "id": item.id,
            "title": item.title,
            "slug": item.slug,
            "status": item.status,
            "version": item.version,
        }
        for item in items
    ]
