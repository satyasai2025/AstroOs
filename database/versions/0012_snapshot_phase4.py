"""Add provenance event and entity history tables for Snapshot Phase IV

Revision ID: 0012
Revises: 0011
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "provenance_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
    )

    op.create_index(
        "ix_provenance_events_actor",
        "provenance_events",
        ["actor"],
    )

    op.create_index(
        "ix_provenance_events_module",
        "provenance_events",
        ["module"],
    )

    op.create_table(
        "entity_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "provenance_events.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
    )

    op.create_index(
        "ix_entity_history_entity_type",
        "entity_history",
        ["entity_type"],
    )

    op.create_index(
        "ix_entity_history_entity_id",
        "entity_history",
        ["entity_id"],
    )


def downgrade() -> None:

    op.drop_index(
        "ix_entity_history_entity_id",
        table_name="entity_history",
    )

    op.drop_index(
        "ix_entity_history_entity_type",
        table_name="entity_history",
    )

    op.drop_table("entity_history")

    op.drop_index(
        "ix_provenance_events_module",
        table_name="provenance_events",
    )

    op.drop_index(
        "ix_provenance_events_actor",
        table_name="provenance_events",
    )

    op.drop_table("provenance_events")