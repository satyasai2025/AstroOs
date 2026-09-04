"""Add birth_charts.is_default (default chart per user)

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-05 00:00:00.000000

A user's first saved chart is automatically marked default
(BirthChartRepository.get_or_create); they can later designate a
different chart as default via POST /horoscope/charts/{id}/set-default.
The partial unique index enforces "at most one default per user" at the
database level — application code (BirthChartRepository.set_default)
unsets the previous default and sets the new one inside a single flush,
but the index is what actually prevents two rows both being default if
that invariant is ever violated by a bug or a concurrent write.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "birth_charts",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_birth_charts_one_default_per_user",
        "birth_charts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_birth_charts_one_default_per_user", table_name="birth_charts")
    op.drop_column("birth_charts", "is_default")
