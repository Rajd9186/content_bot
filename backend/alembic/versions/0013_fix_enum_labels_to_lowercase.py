"""Rename content_tone, content_type, project_status enum labels to lowercase

PostgreSQL stores enum labels as-is. The Python enums use lowercase values
(e.g., ContentTone.PROFESSIONAL.value = "professional"), and SAEnum sends
the Python value to PostgreSQL. For PostgreSQL to accept these values,
its enum labels must be lowercase.

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for enum_name, renames in [
        (
            "content_tone",
            [("PROFESSIONAL", "professional"), ("ACADEMIC", "academic"),
             ("CONVERSATIONAL", "conversational"), ("PERSUASIVE", "persuasive"),
             ("INFORMATIVE", "informative")],
        ),
        (
            "content_type",
            [("BLOG_POST", "blog_post"), ("ARTICLE", "article"),
             ("RESEARCH_PAPER", "research_paper"), ("REPORT", "report"),
             ("WHITE_PAPER", "white_paper"), ("CASE_STUDY", "case_study")],
        ),
        (
            "project_status",
            [("DRAFT", "draft"), ("PLANNING", "planning"),
             ("RESEARCHING", "researching"), ("VERIFYING", "verifying"),
             ("GENERATING", "generating"), ("SELF_VERIFYING", "self_verifying"),
             ("COMPLETED", "completed"), ("FAILED", "failed")],
        ),
    ]:
        for old_label, new_label in renames:
            op.execute(
                f"ALTER TYPE {enum_name} RENAME VALUE '{old_label}' TO '{new_label}'"
            )


def downgrade() -> None:
    for enum_name, renames in [
        (
            "content_tone",
            [("professional", "PROFESSIONAL"), ("academic", "ACADEMIC"),
             ("conversational", "CONVERSATIONAL"), ("persuasive", "PERSUASIVE"),
             ("informative", "INFORMATIVE")],
        ),
        (
            "content_type",
            [("blog_post", "BLOG_POST"), ("article", "ARTICLE"),
             ("research_paper", "RESEARCH_PAPER"), ("report", "REPORT"),
             ("white_paper", "WHITE_PAPER"), ("case_study", "CASE_STUDY")],
        ),
        (
            "project_status",
            [("draft", "DRAFT"), ("planning", "PLANNING"),
             ("researching", "RESEARCHING"), ("verifying", "VERIFYING"),
             ("generating", "GENERATING"), ("self_verifying", "SELF_VERIFYING"),
             ("completed", "COMPLETED"), ("failed", "FAILED")],
        ),
    ]:
        for old_label, new_label in renames:
            op.execute(
                f"ALTER TYPE {enum_name} RENAME VALUE '{old_label}' TO '{new_label}'"
            )