"""Payment tax breakdown columns (Phase 8)

Revision ID: 0034
Revises: 0033
Create Date: 2026-08-27 00:00:00.000000

Adds tax breakdown columns to the payments table:
  - base_amount : Integer (in smallest currency unit, e.g. paise/cents)
  - tax_amount  : Integer (in smallest currency unit)
  - tax_rate    : Float (tax percentage applied, e.g. 18.0)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0034"
down_revision: Union[str, None] = "0033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("base_amount", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("tax_amount", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("tax_rate", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "tax_rate")
    op.drop_column("payments", "tax_amount")
    op.drop_column("payments", "base_amount")
