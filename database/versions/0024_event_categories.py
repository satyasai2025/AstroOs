"""Add the open, hierarchical event_categories tree and link it from life_events

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-24 00:00:00.000000

Adds a self-referencing adjacency-list tree (`event_categories`, same
`parent_id`/`level` pattern as `dashas`) for research-event
categorization, replacing the flat free-text `life_events.category`
column's lack of structure. Nodes are created on demand (open
vocabulary) — no fixed seed rows are inserted by this migration itself;
seeding happens via apps/api/services/event_category_seed.py.

`life_events.category` is kept as-is for backward compatibility; the new
`category_id` FK is nullable so existing rows are unaffected.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "event_categories",
        *_audit_columns(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "parent_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("event_categories.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("level", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("path", sa.String(600), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("house_number", sa.SmallInteger(), nullable=True),
        sa.Column("karaka_planet", sa.String(20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="import"),
        sa.Column("source_doc_count", sa.Integer(), nullable=True),
    )
    op.create_index("ix_event_categories_parent_id", "event_categories", ["parent_id"])
    op.create_index("ix_event_categories_path", "event_categories", ["path"])

    op.add_column(
        "life_events",
        sa.Column(
            "category_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("event_categories.id", ondelete="SET NULL"), nullable=True,
        ),
    )
    op.create_index("ix_life_events_category_id", "life_events", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_life_events_category_id", table_name="life_events")
    op.drop_column("life_events", "category_id")
    op.drop_index("ix_event_categories_path", table_name="event_categories")
    op.drop_index("ix_event_categories_parent_id", table_name="event_categories")
    op.drop_table("event_categories")
