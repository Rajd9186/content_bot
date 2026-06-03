"""Add Project Intelligence Extensions
 
Revision ID: 0010
Revises: 0009
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Project Instructions
    op.create_table(
        "project_instructions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("instruction_content", sa.Text, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_pi_project", "project_instructions", ["project_id"])
    op.create_index("idx_pi_priority", "project_instructions", ["project_id", "priority"])

    # Project Chat Sessions
    op.create_table(
        "project_chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_pcs_project", "project_chat_sessions", ["project_id"])
    op.create_index("idx_pcs_created", "project_chat_sessions", ["created_at"])

    # Project Chat Messages
    op.create_table(
        "project_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "session_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("project_chat_sessions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_pcm_session", "project_chat_messages", ["session_id"])
    op.create_index("idx_pcm_created", "project_chat_messages", ["created_at"])

    # Project Source Policies
    op.create_table(
        "project_source_policies",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("policy_name", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_psp_project", "project_source_policies", ["project_id"])
    op.create_index("idx_psp_project", "project_source_policies", ["project_id"])

    # Project Allowed Sources
    op.create_table(
        "project_allowed_sources",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_domain", sa.String(255), nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("idx_pas_project", "project_allowed_sources", ["project_id"])
    op.create_index("idx_pas_domain", "project_allowed_sources", ["source_domain"])

    # Project Blocked Sources
    op.create_table(
        "project_blocked_sources",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_domain", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
    )
    op.create_index("idx_pbs_project", "project_blocked_sources", ["project_id"])
    op.create_index("idx_pbs_domain", "project_blocked_sources", ["source_domain"])

    # Project Research Preferences
    op.create_table(
        "project_research_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("freshness_mode", sa.String(64), nullable=False, server_default="evergreen"),
        sa.Column("trust_threshold", sa.Integer, nullable=False, server_default="0"),
        sa.Column("allow_competitor_content", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("latest_only", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_unique_constraint("uq_prp_project", "project_research_preferences", ["project_id"])
    op.create_index("idx_prp_project", "project_research_preferences", ["project_id"])


def downgrade() -> None:
    op.drop_table("project_research_preferences")
    op.drop_table("project_blocked_sources")
    op.drop_table("project_allowed_sources")
    op.drop_table("project_source_policies")
    op.drop_table("project_chat_messages")
    op.drop_table("project_chat_sessions")
    op.drop_table("project_instructions")
