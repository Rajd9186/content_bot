from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, utcnow


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    versions: Mapped[list[SkillVersion]] = relationship(
        "SkillVersion", back_populates="skill", cascade="all, delete-orphan",
        order_by="SkillVersion.version.desc()"
    )
    agent_targets: Mapped[list[SkillAgentTarget]] = relationship(
        "SkillAgentTarget", back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_skills_category", "category"),
        Index("idx_skills_active", "active"),
    )


class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    skill: Mapped[Skill] = relationship("Skill", back_populates="versions")

    __table_args__ = (
        Index("idx_sv_skill_version", "skill_id", "version"),
        UniqueConstraint("skill_id", "version", name="uq_sv_skill_version"),
    )


class ProjectSkill(Base):
    __tablename__ = "project_skills"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("idx_ps_project_skill", "project_id", "skill_id"),
        UniqueConstraint("project_id", "skill_id", name="uq_ps_project_skill"),
    )


class SkillAgentTarget(Base):
    __tablename__ = "skill_agent_targets"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)

    skill: Mapped[Skill] = relationship("Skill", back_populates="agent_targets")

    __table_args__ = (
        Index("idx_sat_skill_agent", "skill_id", "agent_name"),
    )


class SkillConflict(Base):
    __tablename__ = "skill_conflicts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workflow_execution_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skill_a: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_b: Mapped[str] = mapped_column(String(255), nullable=False)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class SkillAnalytics(Base):
    __tablename__ = "skill_analytics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    average_compliance: Mapped[float] = mapped_column(Float, default=0.0)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SkillTemplate(Base):
    __tablename__ = "skill_templates"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index("idx_st_category", "category"),
    )
