"""Add facts_json column to event_snapshots for unified canonical Fact storage

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-24 00:00:00.000000

Adds a nullable facts_json column (Text) to event_snapshots table to store
the serialized list of Fact dictionaries produced by FactBuilder. Existing
legacy columns are left untouched, ensuring backward compatibility.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: Union[str, None] = "0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "event_snapshots",
        sa.Column(
            "facts_json",
            sa.Text(),
            nullable=True,
            comment="JSON serialized list of Fact dictionaries",
        ),
    )


def downgrade() -> None:
    op.drop_column("event_snapshots", "facts_json")
