"""Add versioning columns to knowledge tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-18 00:00:00.000000

Tables modified:
  books       — version, version_comment, superseded_by
  verses      — version, version_comment, superseded_by
  rules       — version, version_comment, superseded_by
  karakatvas  — version, version_comment, superseded_by

The versioning scheme is soft-append: updates create new rows with
incremented version rather than in-place column changes. The original row
and every prior version remain in the table. superseded_by points to the
replacing row's id (or NULL for the current/latest version).

Each table gets a composite index on (id, version) for efficient
versioned-lookup queries.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All four knowledge tables get the same three columns.
_TABLES = ["books", "verses", "rules", "karakatvas"]


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        )
        op.add_column(
            table,
            sa.Column("version_comment", sa.String(500), nullable=True),
        )
        op.add_column(
            table,
            sa.Column(
                "superseded_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey(f"{table}.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index(
            f"ix_{table}_id_version",
            table,
            ["id", "version"],
            unique=False,
        )


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_id_version", table_name=table)
        op.drop_column(table, "superseded_by")
        op.drop_column(table, "version_comment")
        op.drop_column(table, "version")
