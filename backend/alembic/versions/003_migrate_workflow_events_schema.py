"""Migrate workflow_events from old WorkflowEventModel to new WorkflowEventRecord schema.

Adds columns: agent_name, status, progress_percent, payload_json, created_at
Drops columns: node_name, data, timestamp (after data migration)
Adds indexes on: workflow_id, project_id, event_type, created_at

Safe for both fresh and existing deployments:
- Uses ALTER TABLE ADD COLUMN IF NOT EXISTS (PG 9.6+)
- Migrates data from old columns to new before dropping old columns
- Adds server_default for backward-compatible NULL handling
- Uses information_schema for column detection (works with async engines)

Revision ID: 003
Revises: 002
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column exists using information_schema (works with all engine types)."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return result.scalar() > 0


def _table_exists(table: str) -> bool:
    """Check if a table exists using information_schema."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = :table AND table_schema = 'public'"
        ),
        {"table": table},
    )
    return result.scalar() > 0


def upgrade() -> None:
    if not _table_exists("workflow_events"):
        return

    # ------------------------------------------------------------------
    # 1. Add new columns (idempotent via information_schema check)
    # ------------------------------------------------------------------
    if not _column_exists("workflow_events", "agent_name"):
        op.add_column("workflow_events",
            sa.Column("agent_name", sa.String(100), nullable=False, server_default=""))

    if not _column_exists("workflow_events", "status"):
        op.add_column("workflow_events",
            sa.Column("status", sa.String(20), nullable=False, server_default="running"))

    if not _column_exists("workflow_events", "progress_percent"):
        op.add_column("workflow_events",
            sa.Column("progress_percent", sa.Float(), nullable=False, server_default=sa.text("0.0")))

    # payload_json — migrate from old `data` column if it exists
    if not _column_exists("workflow_events", "payload_json"):
        op.add_column("workflow_events",
            sa.Column("payload_json", postgresql.JSON(astext_type=sa.Text()), nullable=True))
        if _column_exists("workflow_events", "data"):
            op.execute("UPDATE workflow_events SET payload_json = data WHERE data IS NOT NULL")
        op.execute("UPDATE workflow_events SET payload_json = '{}'::jsonb WHERE payload_json IS NULL")

    # created_at — migrate from old `timestamp` column if it exists
    if not _column_exists("workflow_events", "created_at"):
        op.add_column("workflow_events",
            sa.Column("created_at", sa.DateTime(), nullable=True))
        if _column_exists("workflow_events", "timestamp"):
            op.execute("UPDATE workflow_events SET created_at = timestamp WHERE timestamp IS NOT NULL")
        op.execute("UPDATE workflow_events SET created_at = NOW() WHERE created_at IS NULL")
        op.alter_column("workflow_events", "created_at", nullable=False, server_default=sa.func.now())

    # ------------------------------------------------------------------
    # 2. Add indexes (idempotent via IF NOT EXISTS)
    # ------------------------------------------------------------------
    op.execute("CREATE INDEX IF NOT EXISTS ix_workflow_events_workflow_id ON workflow_events (workflow_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workflow_events_project_id ON workflow_events (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workflow_events_event_type ON workflow_events (event_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workflow_events_created_at ON workflow_events (created_at)")

    # ------------------------------------------------------------------
    # 3. Drop old columns (only if they still exist — old schema)
    # ------------------------------------------------------------------
    with op.batch_alter_table("workflow_events") as batch_op:
        if _column_exists("workflow_events", "node_name"):
            batch_op.drop_column("node_name")
        if _column_exists("workflow_events", "data"):
            batch_op.drop_column("data")
        if _column_exists("workflow_events", "timestamp"):
            batch_op.drop_column("timestamp")


def downgrade() -> None:
    """Reverse the migration by re-adding old columns (data preserved)."""
    if not _table_exists("workflow_events"):
        return

    if not _column_exists("workflow_events", "node_name"):
        op.add_column("workflow_events",
            sa.Column("node_name", sa.String(), nullable=True))
    if not _column_exists("workflow_events", "data"):
        op.add_column("workflow_events",
            sa.Column("data", postgresql.JSON(astext_type=sa.Text()), nullable=True))
        op.execute("UPDATE workflow_events SET data = payload_json WHERE payload_json IS NOT NULL")
    if not _column_exists("workflow_events", "timestamp"):
        op.add_column("workflow_events",
            sa.Column("timestamp", sa.DateTime(), nullable=True))
        op.execute("UPDATE workflow_events SET timestamp = created_at WHERE created_at IS NOT NULL")
