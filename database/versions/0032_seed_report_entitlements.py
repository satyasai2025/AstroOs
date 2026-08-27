"""Seed report-download entitlements

Revision ID: 0032
Revises: 0031
Create Date: 2026-08-27

Adds the `reports` x plan x action cells to plan_features.

WHY THIS IS NEEDED
------------------
`require_entitlement` resolves a decision from plan_features rows, and treats
an unresolved cell as a legacy pass unless the feature appears in
GOVERNED_FEATURES (which is derived from DECIDED_MATRIX). `reports` had no
cells at all, so the paid Detailed Birth Report rendered a full 200 for a user
on the FREE plan — the route guard was inert.

Decided by the report tier architecture:
    Birth Chart Foundation -> free   (served by an UNGATED route)
    Detailed Birth Report  -> paid   (require_entitlement("reports","export"))

FREE gets an explicit export=False row rather than no row, so a free user
receives a clean ACTION_NOT_ALLOWED instead of silently falling through.

Data-only: no schema change, and it touches only rows for the `reports`
feature. Idempotent — re-running updates the same rows rather than duplicating.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0032"
down_revision: Union[str, None] = "0031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FEATURE_KEY = "reports"

# plan_code -> {action: allowed}. Mirrors DECIDED_MATRIX["reports"] in
# services/feature_catalog.py; the two must stay in step (asserted by
# tests/unit/test_report_entitlement_seed.py).
CELLS: dict[str, dict[str, bool]] = {
    "FREE":     {"view": True, "export": False},
    "PRO":      {"view": True, "export": True},
    "RESEARCH": {"view": True, "export": True},
    "CUSTOM":   {"view": True, "export": True},
}

_ACTIONS = ("view", "create", "edit", "run", "export")


def upgrade() -> None:
    import uuid

    from sqlalchemy import text

    bind = op.get_bind()

    feature_id = bind.execute(
        text("SELECT id FROM features WHERE feature_key = :k"), {"k": FEATURE_KEY}
    ).scalar()
    if feature_id is None:
        # The feature catalog seed (0030) must have run first. Failing loudly
        # is correct: silently skipping would leave the paywall inert again.
        raise RuntimeError(
            f"feature '{FEATURE_KEY}' not found — run migration 0030 first"
        )

    for plan_code, actions in CELLS.items():
        plan_id = bind.execute(
            text("SELECT id FROM plans WHERE plan_code = :c"), {"c": plan_code}
        ).scalar()
        if plan_id is None:
            continue  # plan not seeded in this environment

        existing = bind.execute(
            text(
                "SELECT id FROM plan_features "
                "WHERE plan_id = :p AND feature_id = :f"
            ),
            {"p": plan_id, "f": feature_id},
        ).scalar()

        values = {f"can_{a}": bool(actions.get(a, False)) for a in _ACTIONS}

        if existing is None:
            bind.execute(
                text(
                    "INSERT INTO plan_features "
                    "(id, plan_id, feature_id, can_view, can_create, "
                    " can_edit, can_run, can_export) "
                    "VALUES (:id, :plan_id, :feature_id, :can_view, :can_create, "
                    " :can_edit, :can_run, :can_export)"
                ),
                {"id": uuid.uuid4(), "plan_id": plan_id, "feature_id": feature_id, **values},
            )
        else:
            bind.execute(
                text(
                    "UPDATE plan_features SET can_view = :can_view, "
                    "can_create = :can_create, can_edit = :can_edit, "
                    "can_run = :can_run, can_export = :can_export "
                    "WHERE id = :id"
                ),
                {"id": existing, **values},
            )


def downgrade() -> None:
    from sqlalchemy import text

    bind = op.get_bind()
    bind.execute(
        text(
            "DELETE FROM plan_features WHERE feature_id = "
            "(SELECT id FROM features WHERE feature_key = :k)"
        ),
        {"k": FEATURE_KEY},
    )
