"""Add project schema columns from model alignment

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_column_if_not_exists(table: str, column: str, column_def: str) -> None:
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column}'
            ) THEN
                ALTER TABLE {table} ADD COLUMN {column_def};
            END IF;
        END $$;
    """)


def upgrade() -> None:
    # Create enum types if they don't exist
    for enum_name, values in [
        ("content_tone", ("'professional'", "'academic'", "'conversational'", "'persuasive'", "'informative'")),
        ("content_type", ("'blog_post'", "'article'", "'research_paper'", "'report'", "'white_paper'", "'case_study'")),
        ("project_status", ("'draft'", "'planning'", "'researching'", "'verifying'", "'generating'", "'self_verifying'", "'completed'", "'failed'")),
    ]:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                    CREATE TYPE {enum_name} AS ENUM ({','.join(values)});
                END IF;
            END $$;
        """)

    # Add columns to projects table
    _add_column_if_not_exists("projects", "topic", "topic VARCHAR(500) NOT NULL DEFAULT ''")
    _add_column_if_not_exists("projects", "title", "title VARCHAR(500) NOT NULL DEFAULT ''")
    _add_column_if_not_exists("projects", "points_to_cover", "points_to_cover JSON NOT NULL DEFAULT '[]'::json")
    _add_column_if_not_exists(
        "projects", "tone",
        "tone content_tone NOT NULL DEFAULT 'professional'::content_tone"
    )
    _add_column_if_not_exists(
        "projects", "content_type",
        "content_type content_type NOT NULL DEFAULT 'article'::content_type"
    )
    _add_column_if_not_exists("projects", "target_audience", "target_audience VARCHAR(300)")
    _add_column_if_not_exists(
        "projects", "seo_keywords",
        "seo_keywords JSON NOT NULL DEFAULT '[]'::json"
    )
    _add_column_if_not_exists(
        "projects", "status",
        "status project_status NOT NULL DEFAULT 'draft'::project_status"
    )
    _add_column_if_not_exists("projects", "outline", "outline JSON")


def downgrade() -> None:
    # Remove added columns
    for col in [
        "topic", "title", "points_to_cover", "tone", "content_type",
        "target_audience", "seo_keywords", "status", "outline",
    ]:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'projects' AND column_name = '{col}'
                ) THEN
                    ALTER TABLE projects DROP COLUMN {col};
                END IF;
            END $$;
        """)
