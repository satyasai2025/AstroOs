"""
AstroOS — Dasha Persistence Fixes

Two schema gaps block persisting dasha calculations that DashaEngine already
produces (no new calculation logic — this migration only widens storage to
match existing output):

1. `dasha_type` enum was missing 'chara' and 'narayana'. DashaEngine computes
   all six systems (vimshottari, yogini, ashtottari, kalachakra, chara,
   narayana) and the DashaRequest/DashaSystem API contract already exposes
   all six — but the enum created in 0002 only listed four. Without this,
   persisting a Chara or Narayana tree fails at the database with an invalid
   enum value error.

2. `dashas.lord` was typed as the `graha` enum (9 planet names only). Per
   apps/api/domain/dasha.py's own docstring, `DashaPeriod.lord` holds:
     - Graha name for Vimshottari / Ashtottari (fits the old column)
     - Yogini name for Yogini dasha (e.g. "siddha") — NOT a valid graha
     - Rashi name for Kalachakra / Chara / Narayana (e.g. "cancer") — NOT
       a valid graha
   The old column could only ever have stored 2 of the 6 systems correctly.
   Widened to a plain VARCHAR(40) since it must hold three different kinds
   of reference name depending on dasha_type.

ALTER TYPE ... ADD VALUE cannot run inside a transaction in PostgreSQL, so
this migration temporarily disables Alembic's transactional DDL wrapper for
the enum step.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Extend dasha_type enum ────────────────────────────────────────────
    # Must run outside a transaction block — PostgreSQL forbids ALTER TYPE
    # ... ADD VALUE inside a transaction that might still roll back.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE dasha_type ADD VALUE IF NOT EXISTS 'chara'")
        op.execute("ALTER TYPE dasha_type ADD VALUE IF NOT EXISTS 'narayana'")

    # ── 2. Widen dashas.lord from the graha enum to a plain string ───────────
    op.execute(
        "ALTER TABLE dashas ALTER COLUMN lord TYPE VARCHAR(40) USING lord::text"
    )


def downgrade() -> None:
    # Reverting the enum widening (chara/narayana) is intentionally not
    # supported — PostgreSQL cannot remove values from an enum type without
    # recreating it, and any 'chara'/'narayana' rows would need to be
    # deleted first. Re-narrowing `lord` back to the graha enum is also
    # destructive (any yogini/rashi-name rows would fail the cast). If a
    # rollback is genuinely required, restore from a pre-migration backup.
    raise NotImplementedError(
        "Downgrade of 0003 is not supported — see migration docstring."
    )
