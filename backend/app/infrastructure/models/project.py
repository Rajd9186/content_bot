from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pgvector.sqlalchemy import Vector

from app.infrastructure.models.base import Base, JSONBColumn, utcnow


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[str] = mapped_column(
        "owner_id", String(255), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    conversations: Mapped[list[ProjectConversation]] = relationship(
        "ProjectConversation", back_populates="project", cascade="all, delete-orphan"
    )
    outputs: Mapped[list[ProjectOutput]] = relationship(
        "ProjectOutput", back_populates="project", cascade="all, delete-orphan"
    )
    memories: Mapped[list[ProjectMemory]] = relationship(
        "ProjectMemory", back_populates="project", cascade="all, delete-orphan"
    )
    pinned_memories: Mapped[list[PinnedProjectMemory]] = relationship(
        "PinnedProjectMemory", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_projects_owner", "owner_id"),
        Index("idx_projects_archived", "archived"),
    )


class ProjectConversation(Base):
    __tablename__ = "project_conversations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        "project_id", UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_metadata: Mapped[dict | None] = mapped_column(JSONBColumn, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utcnow
    )

    project: Mapped[Project] = relationship("Project", back_populates="conversations")

    __table_args__ = (
        Index("idx_pc_project", "project_id"),
        Index("idx_pc_created", "created_at"),
    )


class ProjectOutput(Base):
    __tablename__ = "project_outputs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        "project_id", UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    workflow_execution_id: Mapped[str | None] = mapped_column(
        "workflow_execution_id", UUID(as_uuid=False), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(
        "content_type", String(64), nullable=False, default="article"
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utcnow
    )

    project: Mapped[Project] = relationship("Project", back_populates="outputs")

    __table_args__ = (
        Index("idx_po_project", "project_id"),
        Index("idx_po_type", "project_id", "content_type"),
        Index("idx_po_created", "created_at"),
    )


class ProjectMemory(Base):
    __tablename__ = "project_memories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        "project_id", UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    memory_type: Mapped[str] = mapped_column(
        "memory_type", String(64), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utcnow
    )

    project: Mapped[Project] = relationship("Project", back_populates="memories")
    pinned: Mapped[list[PinnedProjectMemory]] = relationship(
        "PinnedProjectMemory", back_populates="memory", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_pm_project_type", "project_id", "memory_type"),
        Index("idx_pm_created", "created_at"),
        Index(
            "idx_pm_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 200},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class PinnedProjectMemory(Base):
    __tablename__ = "pinned_project_memories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        "project_id", UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    memory_id: Mapped[str] = mapped_column(
        "memory_id", UUID(as_uuid=False),
        ForeignKey("project_memories.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utcnow
    )

    project: Mapped[Project] = relationship("Project", back_populates="pinned_memories")
    memory: Mapped[ProjectMemory] = relationship("ProjectMemory", back_populates="pinned")

    __table_args__ = (
        Index("idx_ppm_project", "project_id"),
        Index("idx_ppm_priority", "project_id", "priority"),
    )
