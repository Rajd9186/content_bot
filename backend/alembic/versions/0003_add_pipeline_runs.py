"""Add pipeline_runs table for Phase 7 persistence

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("current_node", sa.String(64), nullable=False, server_default="research"),
        sa.Column("topic", sa.Text(), nullable=False, server_default=""),
        sa.Column("audience", sa.String(128), nullable=False, server_default="general"),
        sa.Column("tone", sa.String(128), nullable=False, server_default="professional"),
        sa.Column("goals", sa.Text(), nullable=False, server_default=""),
        sa.Column("research_data", postgresql.JSONB(), nullable=True),
        sa.Column("plan", postgresql.JSONB(), nullable=True),
        sa.Column("outline", postgresql.JSONB(), nullable=True),
        sa.Column("draft_content", sa.Text(), nullable=True),
        sa.Column("seo_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("fact_check_results", postgresql.JSONB(), nullable=True),
        sa.Column("compliance_results", postgresql.JSONB(), nullable=True),
        sa.Column("final_content", sa.Text(), nullable=True),
        sa.Column("human_review", postgresql.JSONB(), nullable=True),
        sa.Column("node_results", postgresql.JSONB(), nullable=True),
        sa.Column("errors", postgresql.JSONB(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_pr_workflow", "pipeline_runs", ["workflow_id"])
    op.create_index("idx_pr_workspace_status", "pipeline_runs", ["workspace_id", "status"])
    op.create_index("idx_pr_status_heartbeat", "pipeline_runs", ["status", "heartbeat_at"])


def downgrade() -> None:
    op.drop_index("idx_pr_status_heartbeat", table_name="pipeline_runs")
    op.drop_index("idx_pr_workspace_status", table_name="pipeline_runs")
    op.drop_index("idx_pr_workflow", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
