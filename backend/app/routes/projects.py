import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.log_config.logger import logger

from app.database import get_session
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectQuickCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


def _auto_generate_fields(topic: str) -> dict:
    words = topic.split()
    topic_lower = topic.lower()

    tones_by_topic = {
        "ai": "informative",
        "technology": "informative",
        "science": "academic",
        "research": "academic",
        "health": "professional",
        "business": "professional",
        "finance": "professional",
        "marketing": "persuasive",
        "education": "informative",
        "policy": "professional",
        "climate": "informative",
        "security": "professional",
    }
    tone = "professional"
    for key, val in tones_by_topic.items():
        if key in topic_lower:
            tone = val
            break

    content_type = "article"
    type_keywords = {
        "research_paper": ["research", "study", "analysis", "survey", "investigation"],
        "report": ["report", "quarterly", "annual", "review", "summary"],
        "white_paper": ["whitepaper", "technical", "architecture", "framework", "guide"],
        "case_study": ["case study", "example", "implementation", "real-world"],
        "blog_post": ["opinion", "perspective", "thoughts", "introduction", "beginners"],
    }
    for ctype, keywords in type_keywords.items():
        if any(kw in topic_lower for kw in keywords):
            content_type = ctype
            break

    audience_map = {
        "ai": "Technology professionals, developers, and business leaders",
        "technology": "IT professionals, engineers, and technology enthusiasts",
        "health": "Healthcare professionals, clinicians, and medical researchers",
        "business": "Business executives, entrepreneurs, and managers",
        "finance": "Financial analysts, investors, and finance professionals",
        "science": "Researchers, academics, and science professionals",
        "education": "Educators, administrators, and education professionals",
        "marketing": "Marketers, content strategists, and brand managers",
        "security": "Security professionals, IT administrators, and compliance officers",
        "climate": "Environmental scientists, policy makers, and sustainability professionals",
    }
    target_audience = "Professionals and decision-makers"
    for key, val in audience_map.items():
        if key in topic_lower:
            target_audience = val
            break

    title = topic.strip()
    if not title.endswith((".", "!", "?")):
        title = title.strip().rstrip(".,!?")

    points = []
    title_lower = title.lower()

    generic_points = [
        f"Current state and overview of {title_lower}",
        f"Key developments and recent trends in {title_lower}",
        f"Evidence-based analysis of {title_lower} impact and outcomes",
        f"Real-world applications and case studies of {title_lower}",
        f"Future outlook and emerging trends for {title_lower}",
    ]
    points = generic_points

    seo_keywords = [title_lower]
    for word in words:
        word_clean = word.lower().strip(".,!?()[]")
        if len(word_clean) > 3 and word_clean not in seo_keywords:
            seo_keywords.append(word_clean)
    seo_keywords = seo_keywords[:5]

    return {
        "title": title,
        "points_to_cover": points,
        "tone": tone,
        "content_type": content_type,
        "target_audience": target_audience,
        "seo_keywords": seo_keywords,
    }


@router.post("/quick", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def quick_create_project(
    payload: ProjectQuickCreate,
    session: AsyncSession = Depends(get_session),
):
    fields = _auto_generate_fields(payload.topic)
    repo = ProjectRepository(session)
    project = await repo.create(
        topic=payload.topic,
        title=fields["title"],
        points_to_cover=fields["points_to_cover"],
        tone=fields["tone"],
        content_type=fields["content_type"],
        target_audience=fields["target_audience"],
        seo_keywords=fields["seo_keywords"],
    )
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
):
    repo = ProjectRepository(session)
    title = payload.title or payload.topic
    project = await repo.create(
        topic=payload.topic,
        title=title,
        points_to_cover=payload.points_to_cover,
        tone=payload.tone,
        content_type=payload.content_type,
        target_audience=payload.target_audience,
        seo_keywords=payload.seo_keywords,
    )
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    repo = ProjectRepository(session)
    return await repo.list(skip=skip, limit=limit)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = ProjectRepository(session)
    project = await repo.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = ProjectRepository(session)
    deleted = await repo.delete(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
