"""Data migration: uppercase existing enum values in projects table

Existing rows in the projects table have lowercase values for tone,
content_type, and status columns (e.g., 'professional', 'article', 'draft').
After migration 0014 renamed PostgreSQL enum labels to uppercase, and Python
enums now have uppercase values, reading these old lowercase values back
fails with LookupError because SAEnum._object_lookup only has uppercase keys.

This migration uppercase the stored values using native PostgreSQL enum
casting via UPPER(tone::text)::content_tone.

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-07
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update projects.tone from lowercase to uppercase
    op.execute("""
        UPDATE projects
        SET tone = CAST(UPPER(tone::text) AS content_tone)
        WHERE tone::text != UPPER(tone::text)
    """)
    # Update projects.content_type from lowercase to uppercase
    op.execute("""
        UPDATE projects
        SET content_type = CAST(UPPER(content_type::text) AS content_type)
        WHERE content_type::text != UPPER(content_type::text)
    """)
    # Update projects.status from lowercase to uppercase
    op.execute("""
        UPDATE projects
        SET status = CAST(UPPER(status::text) AS project_status)
        WHERE status::text != UPPER(status::text)
    """)


def downgrade() -> None:
    # Reverse: lowercase existing enum values
    op.execute("""
        UPDATE projects
        SET tone = CAST(LOWER(tone::text) AS content_tone)
        WHERE tone::text != LOWER(tone::text)
    """)
    op.execute("""
        UPDATE projects
        SET content_type = CAST(LOWER(content_type::text) AS content_type)
        WHERE content_type::text != LOWER(content_type::text)
    """)
    op.execute("""
        UPDATE projects
        SET status = CAST(LOWER(status::text) AS project_status)
        WHERE status::text != LOWER(status::text)
    """)
