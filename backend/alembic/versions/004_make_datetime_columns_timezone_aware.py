"""Make all datetime columns timezone-aware.

Previously many columns used DateTime() without timezone=True but received
timezone-aware values (datetime.now(timezone.utc)). This mismatch caused
asyncpg DataError on comparison operations.

This migration converts all TIMESTAMP WITHOUT TIME ZONE columns to
TIMESTAMP WITH TIME ZONE, treating existing naive timestamps as UTC.

Affected tables and columns (11 tables, 17 columns):
  chat_sessions: created_at, updated_at
  chat_messages: created_at
  workflow_events: created_at
  workflow_executions: started_at, completed_at
  workflow_steps: started_at, completed_at
  content_locks: locked_at, expires_at
  enhancement_jobs: started_at, completed_at
  contradictions: created_at
  agent_memory: created_at, last_accessed_at
  hyperlink_validations: checked_at, created_at

Revision ID: 004
Revises: 003
Create Date: 2026-05-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column) pairs that need timezone-aware conversion
_COLUMNS_TO_CONVERT: list[tuple[str, str]] = [
    ("chat_sessions", "created_at"),
    ("chat_sessions", "updated_at"),
    ("chat_messages", "created_at"),
    ("workflow_events", "created_at"),
    ("workflow_executions", "started_at"),
    ("workflow_executions", "completed_at"),
    ("workflow_steps", "started_at"),
    ("workflow_steps", "completed_at"),
    ("content_locks", "locked_at"),
    ("content_locks", "expires_at"),
    ("enhancement_jobs", "started_at"),
    ("enhancement_jobs", "completed_at"),
    ("contradictions", "created_at"),
    ("agent_memory", "created_at"),
    ("agent_memory", "last_accessed_at"),
    ("hyperlink_validations", "checked_at"),
    ("hyperlink_validations", "created_at"),
]


def _column_exists(table: str, column: str) -> bool:
    """Check if a column exists using information_schema."""
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


def _get_datatype(table: str, column: str) -> str | None:
    """Get the full data type of a column (e.g. 'timestamp without time zone')."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return result.scalar()


def upgrade() -> None:
    # Set session timezone to UTC so naive timestamps are treated as UTC
    op.execute("SET timezone = 'UTC'")

    for table, column in _COLUMNS_TO_CONVERT:
        if not _table_exists(table):
            continue
        if not _column_exists(table, column):
            continue

        current_type = _get_datatype(table, column)
        if current_type and "timestamp with time zone" in current_type:
            # Already timezone-aware — skip
            continue

        # Cast naive TIMESTAMP to TIMESTAMP WITH TIME ZONE, treating values as UTC
        op.execute(
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" '
            f'TYPE TIMESTAMP WITH TIME ZONE '
            f'USING "{column}" AT TIME ZONE \'UTC\''
        )


def downgrade() -> None:
    op.execute("SET timezone = 'UTC'")

    for table, column in _COLUMNS_TO_CONVERT:
        if not _table_exists(table):
            continue
        if not _column_exists(table, column):
            continue

        current_type = _get_datatype(table, column)
        if current_type and "timestamp without time zone" in current_type:
            continue

        # Cast TIMESTAMP WITH TIME ZONE back to TIMESTAMP WITHOUT TIME ZONE,
        # dropping the timezone info (the values remain as-is in UTC)
        op.execute(
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" '
            f'TYPE TIMESTAMP WITHOUT TIME ZONE'
        )
