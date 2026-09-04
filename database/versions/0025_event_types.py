"""Add the open, hierarchical event_types tree and link it from life_events

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-24 00:00:00.000000

Adds a self-referencing adjacency-list tree (`event_types`, identical
shape to `event_categories`) for research life-event typing, replacing
the closed 22-value `_EventType` enum for the manual-entry / import path
only. `life_events.event_type` (the legacy enum column) is left as-is —
new tree-based writes store `'other'` there — and the pattern-discovery/
assistant endpoints in routers/research.py that key off the enum are
untouched. `event_type_label` mirrors `category`'s free-text-mirror
pattern; `event_type_id` mirrors `category_id`.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025"
down_revision: Union[str, None] = "0024"
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
        "event_types",
        *_audit_columns(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "parent_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("event_types.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("level", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("path", sa.String(600), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="import"),
    )
    op.create_index("ix_event_types_parent_id", "event_types", ["parent_id"])
    op.create_index("ix_event_types_path", "event_types", ["path"])

    op.add_column(
        "life_events",
        sa.Column(
            "event_type_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True,
        ),
    )
    op.create_index("ix_life_events_event_type_id", "life_events", ["event_type_id"])
    op.add_column(
        "life_events",
        sa.Column("event_type_label", sa.String(100), nullable=False, server_default="Other"),
    )


def downgrade() -> None:
    op.drop_column("life_events", "event_type_label")
    op.drop_index("ix_life_events_event_type_id", table_name="life_events")
    op.drop_column("life_events", "event_type_id")
    op.drop_index("ix_event_types_path", table_name="event_types")
    op.drop_index("ix_event_types_parent_id", table_name="event_types")
    op.drop_table("event_types")
