import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.content_version import ContentVersion, EnhancementJob
from app.schemas.enhance import (
    EnhancementJobResponse,
    ContentVersionResponse,
)
from app.log_config.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_id}/enhance", tags=["Enhancement"])


@router.get("/jobs", response_model=list[EnhancementJobResponse])
async def list_enhancement_jobs(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(EnhancementJob)
        .where(EnhancementJob.project_id == project_id)
        .order_by(EnhancementJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [EnhancementJobResponse.model_validate(j) for j in jobs]


@router.get("/versions", response_model=list[ContentVersionResponse])
async def list_content_versions(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ContentVersion)
        .where(ContentVersion.project_id == project_id)
        .order_by(ContentVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return [ContentVersionResponse.model_validate(v) for v in versions]


@router.get("/versions/{version_id}", response_model=ContentVersionResponse)
async def get_content_version(
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ContentVersion).where(
            ContentVersion.id == version_id,
            ContentVersion.project_id == project_id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Content version not found")
    return ContentVersionResponse.model_validate(version)
