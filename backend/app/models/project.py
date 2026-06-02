import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    RESEARCHING = "researching"
    VERIFYING = "verifying"
    GENERATING = "generating"
    SELF_VERIFYING = "self_verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentTone(str, enum.Enum):
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    CONVERSATIONAL = "conversational"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"


class ContentType(str, enum.Enum):
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    RESEARCH_PAPER = "research_paper"
    REPORT = "report"
    WHITE_PAPER = "white_paper"
    CASE_STUDY = "case_study"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    points_to_cover: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tone: Mapped[ContentTone] = mapped_column(
        SAEnum(ContentTone, name="content_tone", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContentTone.PROFESSIONAL,
    )
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContentType.ARTICLE,
    )
    target_audience: Mapped[str | None] = mapped_column(String(300), nullable=True)
    seo_keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProjectStatus.DRAFT,
    )
    outline: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contents: Mapped[list["GeneratedContent"]] = relationship(
        "GeneratedContent", back_populates="project", cascade="all, delete-orphan"
    )
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="project", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="project", cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(
        "Source", back_populates="project", cascade="all, delete-orphan"
    )
