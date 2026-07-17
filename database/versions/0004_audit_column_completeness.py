"""
AstroOS — Audit Column Completeness Fix

Discovered during a live end-to-end smoke test against real PostgreSQL
(not the SQLite test fixture, which builds its schema from the Python ORM
models directly via Base.metadata.create_all() and therefore never
exposed this gap): migration 0002 defined every table's columns by hand
rather than from the ORM models, and several tables derived from
AstroBase — which declares id, created_at, updated_at, and deleted_at on
every subclass — ended up missing one or more of them:

  Table                          | had              | was missing
  --------------------------------|------------------|------------------
  planet_positions                | (none)           | created_at, updated_at, deleted_at
  houses                          | (none)           | created_at, updated_at, deleted_at
  divisional_planet_positions     | (none)           | created_at, updated_at, deleted_at
  dashas                          | created_at       | updated_at, deleted_at
  divisional_charts               | created_at, updated_at | deleted_at

The first INSERT ever attempted against planet_positions or houses (via
this persistence pass) failed at the database with
`UndefinedColumnError: column "created_at" of relation "houses" does not
exist` — this migration is that fix, not a schema redesign. Column
defaults and the `set_updated_at()` trigger (already created in 0001,
already used by birth_charts/divisional_charts/events/books/verses/rules/
research_projects) are applied consistently with those existing tables.

Scope note: `transits`, `books` (deleted_at), `verses` (deleted_at),
`karakatvas`, and `research_snapshots` have the identical gap but are not
touched here — no repository writes to them yet (Transit/Research/
Knowledge Engines don't exist), so fixing them is left for whichever
migration accompanies that engine, per this pass's "stop after
persistence integration" scope.

A second, unrelated bug surfaced in the same smoke test right after the
column fix above: `planet_positions.combustion_orb_deg` was
`NUMERIC(6,4)` (2 integer digits, max 99.9999), but
`EphemerisWrapper.is_combust()` returns the true angular distance between
a planet and the Sun — 0-180° — regardless of whether that distance is
within the combustion threshold; it's the *distance*, not "the orb by
which it is combust." A real chart produced a value of 150.03°, which is
completely correct output (that planet just isn't combust), but exceeded
what the column could store. Widened to `NUMERIC(9,6)` here as well.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables needing created_at + updated_at + deleted_at, all three missing
_NEEDS_ALL_THREE = ["planet_positions", "houses", "divisional_planet_positions"]

# Tables needing only updated_at + deleted_at (created_at already present)
_NEEDS_UPDATED_AND_DELETED = ["dashas"]

# Tables needing only deleted_at (created_at + updated_at already present)
_NEEDS_DELETED_ONLY = ["divisional_charts"]

# Tables that need the updated_at trigger attached (any table gaining
# updated_at in this migration, i.e. everything except _NEEDS_DELETED_ONLY,
# which already has updated_at and — per 0002 — already has the trigger)
_NEEDS_TRIGGER = _NEEDS_ALL_THREE + _NEEDS_UPDATED_AND_DELETED


def _trigger(conn, table: str) -> None:
    conn.execute(sa.text(
        f"CREATE TRIGGER trg_{table}_updated_at "
        f"BEFORE UPDATE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))


def upgrade() -> None:
    conn = op.get_bind()

    for table in _NEEDS_ALL_THREE:
        op.add_column(table, sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ))
        op.add_column(table, sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ))
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

    for table in _NEEDS_DELETED_ONLY:
        op.add_column(table, sa.Column(
            "deleted_at", sa.DateTime(timezone=True), nullable=True,
        ))

    for table in _NEEDS_TRIGGER:
        _trigger(conn, table)

    # combustion_orb_deg holds a true 0-180° angular distance from the
    # Sun, not just small combustion-range values — see docstring.
    op.alter_column(
        "planet_positions", "combustion_orb_deg",
        type_=sa.Numeric(9, 6),
        existing_type=sa.Numeric(6, 4),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "planet_positions", "combustion_orb_deg",
        type_=sa.Numeric(6, 4),
        existing_type=sa.Numeric(9, 6),
        existing_nullable=True,
    )

    for table in _NEEDS_TRIGGER:
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}"))

    for table in _NEEDS_ALL_THREE:
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")

    for table in _NEEDS_UPDATED_AND_DELETED:
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "updated_at")

    for table in _NEEDS_DELETED_ONLY:
        op.drop_column(table, "deleted_at")
