"""Seed saved_horoscopes edit entitlement (Phase 2 fix)

Revision ID: 0036
Revises: 0035
Create Date: 2026-08-28 00:00:00.000000

Updates plan_features rows for `saved_horoscopes` so that `can_edit` is True
for all plans (FREE, PRO, RESEARCH, CUSTOM), matching DECIDED_MATRIX in
apps/api/services/feature_catalog.py.

This enables DELETE /api/v1/horoscope/charts/{id} and
POST /api/v1/horoscope/charts/{id}/set-default, which are gated by
require_entitlement("saved_horoscopes", "edit").
"""

import uuid
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "0036"
down_revision: Union[str, None] = "0035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FEATURE_KEY = "saved_horoscopes"
PLANS = ("FREE", "PRO", "RESEARCH", "CUSTOM")


def upgrade() -> None:
    bind = op.get_bind()
    feature_id = bind.execute(
        text("SELECT id FROM features WHERE feature_key = :k"), {"k": FEATURE_KEY}
    ).scalar()
    if feature_id is None:
        return

    for plan_code in PLANS:
        plan_id = bind.execute(
            text("SELECT id FROM plans WHERE plan_code = :c"), {"c": plan_code}
        ).scalar()
        if plan_id is None:
            continue

        existing = bind.execute(
            text(
                "SELECT id FROM plan_features "
                "WHERE plan_id = :p AND feature_id = :f"
            ),
            {"p": plan_id, "f": feature_id},
        ).scalar()

        if existing is not None:
            bind.execute(
                text(
                    "UPDATE plan_features SET can_edit = True WHERE id = :id"
                ),
                {"id": existing},
            )
        else:
            bind.execute(
                text(
                    "INSERT INTO plan_features "
                    "(id, plan_id, feature_id, can_view, can_create, "
                    " can_edit, can_run, can_export) "
                    "VALUES (:id, :plan_id, :feature_id, True, True, True, False, False)"
                ),
                {"id": uuid.uuid4(), "plan_id": plan_id, "feature_id": feature_id},
            )


def downgrade() -> None:
    bind = op.get_bind()
    feature_id = bind.execute(
        text("SELECT id FROM features WHERE feature_key = :k"), {"k": FEATURE_KEY}
    ).scalar()
    if feature_id is None:
        return

    for plan_code in PLANS:
        plan_id = bind.execute(
            text("SELECT id FROM plans WHERE plan_code = :c"), {"c": plan_code}
        ).scalar()
        if plan_id is None:
            continue

        bind.execute(
            text(
                "UPDATE plan_features SET can_edit = False "
                "WHERE plan_id = :p AND feature_id = :f"
            ),
            {"p": plan_id, "f": feature_id},
        )
