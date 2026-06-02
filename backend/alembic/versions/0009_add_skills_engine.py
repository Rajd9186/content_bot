"""Add Skills Engine tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("idx_skills_category", "skills", ["category"])
    op.create_index("idx_skills_active", "skills", ["active"])

    op.create_table(
        "skill_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "skill_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(255), nullable=True),
    )
    op.create_index("idx_sv_skill_version", "skill_versions", ["skill_id", "version"])
    op.create_unique_constraint("uq_sv_skill_version", "skill_versions", ["skill_id", "version"])

    op.create_table(
        "project_skills",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "skill_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("idx_ps_project_skill", "project_skills", ["project_id", "skill_id"])
    op.create_unique_constraint("uq_ps_project_skill", "project_skills", ["project_id", "skill_id"])

    op.create_table(
        "skill_agent_targets",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "skill_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("agent_name", sa.String(100), nullable=False),
    )
    op.create_index("idx_sat_skill_agent", "skill_agent_targets", ["skill_id", "agent_name"])

    op.create_table(
        "skill_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workflow_execution_id", sa.String(255), nullable=True),
        sa.Column("skill_a", sa.String(255), nullable=False),
        sa.Column("skill_b", sa.String(255), nullable=False),
        sa.Column("resolution", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "skill_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "skill_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_compliance", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("average_rating", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "skill_templates",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("downloads", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_st_category", "skill_templates", ["category"])


def downgrade() -> None:
    op.drop_table("skill_templates")
    op.drop_table("skill_analytics")
    op.drop_table("skill_conflicts")
    op.drop_table("skill_agent_targets")
    op.drop_table("project_skills")
    op.drop_table("skill_versions")
    op.drop_table("skills")
