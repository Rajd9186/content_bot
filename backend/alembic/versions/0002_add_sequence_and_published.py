"""Add sequence_number and published to stored_events

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stored_events",
        sa.Column("sequence_number", sa.BigInteger(), nullable=True, unique=True),
    )
    op.add_column(
        "stored_events",
        sa.Column("published", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
    )
    op.create_index("idx_se_sequence", "stored_events", ["sequence_number"])

    conn = op.get_bind()
    if conn.engine.dialect.name == "postgresql":
        op.execute("CREATE SEQUENCE IF NOT EXISTS stored_events_seq")
        op.execute(
            "UPDATE stored_events SET sequence_number = nextval('stored_events_seq')"
            " WHERE sequence_number IS NULL"
        )
        op.execute(
            "ALTER TABLE stored_events ALTER COLUMN sequence_number"
            " SET DEFAULT nextval('stored_events_seq')"
        )
        op.execute(
            "ALTER TABLE stored_events ALTER COLUMN sequence_number SET NOT NULL"
        )


def downgrade() -> None:
    op.drop_index("idx_se_sequence", table_name="stored_events")
    op.drop_column("stored_events", "published")
    op.drop_column("stored_events", "sequence_number")

    conn = op.get_bind()
    if conn.engine.dialect.name == "postgresql":
        op.execute("DROP SEQUENCE IF EXISTS stored_events_seq")
