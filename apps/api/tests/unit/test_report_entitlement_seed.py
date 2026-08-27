"""
AstroOS — report entitlement cells must exist and stay in step.

Guards a real leak: the paid Detailed Birth Report route carried
`require_entitlement("reports", "export")`, but `reports` had no cells in
DECIDED_MATRIX and therefore no plan_features rows. `get_decision` returned
"unresolved", `reports` was not in GOVERNED_FEATURES, and the guard fell
through its legacy pass — so a FREE-plan user rendered the paid report with a
full 200.

Two halves have to agree or the paywall silently reopens:
  · DECIDED_MATRIX["reports"]  — makes the feature GOVERNED
  · migration 0032            — writes the matching plan_features rows
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from apps.api.services.feature_catalog import ACTION_COLUMNS, DECIDED_MATRIX

_REPO_ROOT = Path(__file__).resolve().parents[4]
_MIGRATION = _REPO_ROOT / "database" / "versions" / "0032_seed_report_entitlements.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("m0032", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reports_feature_is_governed():
    """
    Presence in DECIDED_MATRIX is what puts `reports` into GOVERNED_FEATURES,
    which is what turns an unresolved cell into a denial instead of a pass.
    """
    from apps.api.dependencies import GOVERNED_FEATURES

    assert "reports" in DECIDED_MATRIX
    assert "reports" in GOVERNED_FEATURES


def test_free_plan_is_explicitly_denied_export():
    """
    FREE carries an explicit export=False rather than being omitted — omission
    is what produced the "unresolved -> legacy pass" leak.
    """
    free = DECIDED_MATRIX["reports"]["FREE"]
    assert free.get("export") is False


def test_paid_plans_are_granted_export():
    for plan in ("PRO", "RESEARCH", "CUSTOM"):
        assert DECIDED_MATRIX["reports"][plan].get("export") is True, (
            f"{plan} must be able to export reports"
        )


def test_migration_cells_match_the_catalog_matrix():
    """The migration writes the DB rows; drift between the two reopens the gap."""
    module = _load_migration()
    assert module.FEATURE_KEY == "reports"

    for plan, actions in module.CELLS.items():
        assert plan in DECIDED_MATRIX["reports"], f"{plan} missing from matrix"
        for action, allowed in actions.items():
            assert DECIDED_MATRIX["reports"][plan].get(action) == allowed, (
                f"migration and DECIDED_MATRIX disagree on "
                f"reports/{plan}/{action}"
            )

    for plan in DECIDED_MATRIX["reports"]:
        assert plan in module.CELLS, f"{plan} decided in matrix but not seeded"


def test_migration_declares_only_known_actions():
    module = _load_migration()
    for plan, actions in module.CELLS.items():
        for action in actions:
            assert action in ACTION_COLUMNS, (
                f"unknown action {action!r} for plan {plan}"
            )


def test_migration_follows_the_current_head():
    module = _load_migration()
    assert module.revision == "0032"
    assert module.down_revision == "0031", (
        "0032 must chain off 0031; a reused revision id previously broke the "
        "whole alembic chain in this project"
    )
