"""
AstroOS — Knowledge/Research/Transit Audit Column Completeness Fix

Migration 0004 fixed the same "missing AstroBase audit column" gap for
planet_positions/houses/divisional_planet_positions/dashas/
divisional_charts, and explicitly flagged in its own docstring that
`books`, `verses` (deleted_at), `karakatvas`, `transits`, and
`research_snapshots` had the identical gap but were left unfixed
because "no repository writes to them yet ... fixing them is left for
whichever migration accompanies that engine."

The Knowledge, Research, and Transit engines (and their v2 Phase A HTTP
routers) now exist and are in active use — discovered via a live
end-to-end run of the Workflow Orchestrator against real PostgreSQL:
`UndefinedColumnError: column books.deleted_at does not exist`, raised
by KnowledgeRepository.search()'s `WHERE books.deleted_at IS NULL`
clause, which every AstroBase-derived model's repository queries
unconditionally include. This is that deferred migration.

  Table               | had                    | was missing
  --------------------|------------------------|---------------------------
  books                | created_at, updated_at | deleted_at
  verses                | created_at, updated_at | deleted_at
  karakatvas            | created_at             | updated_at, deleted_at
  transits               | created_at             | updated_at, deleted_at
  research_snapshots     | created_at             | updated_at, deleted_at

`rules` already had all three (added correctly by whatever migration
introduced it) — not touched here.

books/verses already have the `set_updated_at()` trigger attached (per
0004's own note — it was applied consistently across
birth_charts/divisional_charts/events/books/verses/rules/
research_projects back in 0001/0002), so only the `deleted_at` column is
added for those two. karakatvas/transits/research_snapshots are gaining
`updated_at` for the first time here, so they get the trigger attached
fresh, same as 0004's `_NEEDS_UPDATED_AND_DELETED` pattern.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables needing only deleted_at (created_at + updated_at + trigger already present)
_NEEDS_DELETED_ONLY = ["books", "verses"]

# Tables needing updated_at + deleted_at (created_at already present, no trigger yet)
_NEEDS_UPDATED_AND_DELETED = ["karakatvas", "transits", "research_snapshots"]


def _trigger(conn, table: str) -> None:
    conn.execute(sa.text(
        f"CREATE TRIGGER trg_{table}_updated_at "
        f"BEFORE UPDATE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))


def upgrade() -> None:
    conn = op.get_bind()

    for table in _NEEDS_DELETED_ONLY:
        op.add_column(table, sa.Column(
            "deleted_at", sa.DateTime(timezone=True), nullable=True,
        ))

    for table in _NEEDS_UPDATED_AND_DELETED:
        op.add_column(table, sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ))
        op.add_column(table, sa.Column(
            "deleted_at", sa.DateTime(timezone=True), nullable=True,
        ))
        _trigger(conn, table)


def downgrade() -> None:
    for table in _NEEDS_UPDATED_AND_DELETED:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}"))
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "updated_at")

    for table in _NEEDS_DELETED_ONLY:
        op.drop_column(table, "deleted_at")
