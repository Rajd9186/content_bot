"""Migrate PostgreSQL enum labels to uppercase to match Python SAEnum member names

In SQLAlchemy 2.x, SAEnum(PythonEnum, name="x") maps PostgreSQL labels to
Python enum *member names*, not values. For reading to work, PostgreSQL
labels must match the Python enum member names (e.g., "PROFESSIONAL").

Skips rename if the enum type or the specific label doesn't exist.

Revision ID: 0014
Revises: 0012
Create Date: 2026-06-07
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0014"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_labels(enum_name: str, renames: list[tuple[str, str]]) -> None:
    for old, new in renames:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_type t
                    JOIN pg_enum e ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_name}' AND e.enumlabel = '{old}'
                ) THEN
                    ALTER TYPE {enum_name} RENAME VALUE '{old}' TO '{new}';
                END IF;
            END $$;
        """)


def upgrade() -> None:
    _rename_labels("content_tone", [
        ("professional", "PROFESSIONAL"),
        ("academic", "ACADEMIC"),
        ("conversational", "CONVERSATIONAL"),
        ("persuasive", "PERSUASIVE"),
        ("informative", "INFORMATIVE"),
    ])
    _rename_labels("content_type", [
        ("blog_post", "BLOG_POST"),
        ("article", "ARTICLE"),
        ("research_paper", "RESEARCH_PAPER"),
        ("report", "REPORT"),
        ("white_paper", "WHITE_PAPER"),
        ("case_study", "CASE_STUDY"),
    ])
    _rename_labels("project_status", [
        ("draft", "DRAFT"),
        ("planning", "PLANNING"),
        ("researching", "RESEARCHING"),
        ("verifying", "VERIFYING"),
        ("generating", "GENERATING"),
        ("self_verifying", "SELF_VERIFYING"),
        ("completed", "COMPLETED"),
        ("failed", "FAILED"),
    ])
    _rename_labels("workflow_status", [
        ("pending", "PENDING"),
        ("running", "RUNNING"),
        ("completed", "COMPLETED"),
        ("failed", "FAILED"),
        ("cancelled", "CANCELLED"),
        ("waiting_user", "WAITING_USER"),
    ])
    _rename_labels("content_version_status", [
        ("draft", "DRAFT"),
        ("reviewing", "REVIEWING"),
        ("revised", "REVISED"),
        ("final", "FINAL"),
        ("archived", "ARCHIVED"),
    ])
    _rename_labels("claim_status", [
        ("verified", "VERIFIED"),
        ("unverified", "UNVERIFIED"),
        ("contradicted", "CONTRADICTED"),
        ("unsupported", "UNSUPPORTED"),
    ])


def downgrade() -> None:
    _rename_labels("content_tone", [
        ("PROFESSIONAL", "professional"),
        ("ACADEMIC", "academic"),
        ("CONVERSATIONAL", "conversational"),
        ("PERSUASIVE", "persuasive"),
        ("INFORMATIVE", "informative"),
    ])
    _rename_labels("content_type", [
        ("BLOG_POST", "blog_post"),
        ("ARTICLE", "article"),
        ("RESEARCH_PAPER", "research_paper"),
        ("REPORT", "report"),
        ("WHITE_PAPER", "white_paper"),
        ("CASE_STUDY", "case_study"),
    ])
    _rename_labels("project_status", [
        ("DRAFT", "draft"),
        ("PLANNING", "planning"),
        ("RESEARCHING", "researching"),
        ("VERIFYING", "verifying"),
        ("GENERATING", "generating"),
        ("SELF_VERIFYING", "self_verifying"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
    ])
    _rename_labels("workflow_status", [
        ("PENDING", "pending"),
        ("RUNNING", "running"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
        ("CANCELLED", "cancelled"),
        ("WAITING_USER", "waiting_user"),
    ])
    _rename_labels("content_version_status", [
        ("DRAFT", "draft"),
        ("REVIEWING", "reviewing"),
        ("REVISED", "revised"),
        ("FINAL", "final"),
        ("ARCHIVED", "archived"),
    ])
    _rename_labels("claim_status", [
        ("VERIFIED", "verified"),
        ("UNVERIFIED", "unverified"),
        ("CONTRADICTED", "contradicted"),
        ("UNSUPPORTED", "unsupported"),
    ])
