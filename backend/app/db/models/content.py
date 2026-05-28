import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base, JSONBColumn, utcnow


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        "workspace_id", UUID(as_uuid=False), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(250), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column("source_url", String(2048), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    raw_body: Mapped[Optional[str]] = mapped_column("raw_body", Text, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONBColumn, nullable=True, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    correlation_id: Mapped[Optional[str]] = mapped_column(
        "correlation_id", UUID(as_uuid=False), nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        "created_by", UUID(as_uuid=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("idx_ci_workspace_status", "workspace_id", "status"),
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content_item_id: Mapped[str] = mapped_column(
        "content_item_id", UUID(as_uuid=False),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_body: Mapped[Optional[str]] = mapped_column("raw_body", Text, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONBColumn, nullable=True, default=dict)
    created_by: Mapped[str] = mapped_column(
        "created_by", UUID(as_uuid=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )


class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content_item_id: Mapped[str] = mapped_column(
        "content_item_id", UUID(as_uuid=False),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    job_id: Mapped[Optional[str]] = mapped_column(
        "job_id", UUID(as_uuid=False), nullable=True, index=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column("agent_id", String(64), nullable=True)
    content_type: Mapped[str] = mapped_column("content_type", String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONBColumn, nullable=True, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )
