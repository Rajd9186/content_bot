import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, func, JSON, Uuid, Boolean, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base
from app.utils.datetime_utils import utc_now


class ContentVersionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEWING = "REVIEWING"
    REVISED = "REVISED"
    FINAL = "FINAL"
    ARCHIVED = "ARCHIVED"


class ContentVersion(Base):
    """Immutable content version record. Each agent creates a new version.

    Only the Writer agent creates DRAFT versions.
    Revision agent creates REVISED versions.
    No agent ever modifies an existing version.
    """

    __tablename__ = "content_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "version_number", name="uq_project_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ContentVersionStatus] = mapped_column(
        SAEnum(ContentVersionStatus, name="content_version_status"),
        default=ContentVersionStatus.DRAFT,
    )
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    seo_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("content_versions.id", ondelete="SET NULL"), nullable=True
    )
    change_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped["Project"] = relationship("Project", backref="content_versions")


class ContentLock(Base):
    """Ensures only one agent can write content at a time."""

    __tablename__ = "content_locks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    locked_by: Mapped[str] = mapped_column(String(100), nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EnhancementJob(Base):
    """Tracks enhancement agent execution (critique, revision, verification, etc.).

    Enhancement agents do NOT auto-run. They are triggered by the user via API.
    Each job runs once and produces a result.
    """

    __tablename__ = "enhancement_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    result_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
