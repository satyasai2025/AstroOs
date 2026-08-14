"""Add D5, D6, D8, D11 to the chart_type enum

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-15 00:00:00.000000

Panchamsha, Shashthamsha, Ashtamsha, and Rudramsha were added to
DivisionalEngine.SUPPORTED_VARGAS (apps/api/services/divisional_engine.py)
per sourced classical formulas. The chart_type Postgres enum backing
divisional_charts.chart_type must accept these codes so a saved chart
for one of these vargas doesn't fail its check constraint on insert.

ALTER TYPE ... ADD VALUE cannot run inside a transaction block in
Postgres < 12; alembic's autocommit_block() handles this safely, and
the added values cannot be removed in a downgrade (Postgres has no
DROP VALUE) — downgrade() is a documented no-op.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_VALUES = ("D5", "D6", "D8", "D11")


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for value in _NEW_VALUES:
            op.execute(f"ALTER TYPE chart_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value without rebuilding the type
    # and every column that uses it. Not implemented — the added values are
    # additive and harmless to leave in place.
    pass
