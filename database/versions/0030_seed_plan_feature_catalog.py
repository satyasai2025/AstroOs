"""Seed plan / feature / entitlement catalog (Phase 2)

Revision ID: 0030
Revises: 0029
Create Date: 2026-08-26 00:00:00.000000

Populates the (schema-only) tables created in 0029 so the Phase 2 plan +
feature entitlement foundation is usable:

  - plans         : FREE, PRO, RESEARCH, CUSTOM
  - features      : the AstroOS feature catalog (keys mirror real routers/UI)
  - plan_limits   : saved_horoscopes, research_projects_monthly per plan
  - plan_features : ONLY the decided Feature x Plan x Action cells.

Unresolved matrix cells deliberately produce NO plan_features row. The
EntitlementService surfaces those as `unresolved` so admins / later phases can
decide them without code changes (see services/feature_catalog.py docstring).

This mirrors services/feature_catalog.py's canonical catalog but is frozen
here as migration data — migrations are immutable snapshots.
"""

import uuid
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0030"
down_revision: Union[str, None] = "0029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ── Plans ────────────────────────────────────────────────────────────────────
PLAN_ROWS = [
    ("FREE", "Free", "Personal astrology essentials.", True),
    ("PRO", "Pro", "Serious students: more saved charts and light research.", True),
    ("RESEARCH", "Research", "Full research workspace for working researchers.", True),
    ("CUSTOM", "Custom", "Bespoke limits and feature access, configured per agreement.", True),
]

# ── Feature catalog (keys mirror real AstroOS routers/UI modules) ────────────
FEATURE_ROWS: list[tuple[str, str, str, str]] = [
    ("chart_calculation", "core", "Chart Calculation", "Birth-chart computation pipeline (ephemeris, ayanamsa, houses)."),
    ("saved_horoscopes", "core", "Saved Horoscopes", "Save and revisit birth charts/horoscopes. Count-limited per plan."),
    ("planet_explorer", "core", "Planet Explorer", "Canonical planet explorer at /charts/planets."),
    ("dasha", "core", "Dasha", "Vimshottari and multi-dasha timelines and confluence."),
    ("varga", "core", "Varga", "Divisional charts (D1-D60) via the divisional engine."),
    ("transit", "core", "Transit", "Gochara transit tracking and transit-pattern scanning."),
    ("prashna", "core", "Prashna", "Horary (Prashna) chart casting and judgement."),
    ("analysis", "core", "Analysis", "Event analysis, yogas and strength modules (Shadbala, Ashtakavarga)."),
    ("reports", "core", "Reports", "Narrative and full-life report generation."),
    ("export", "core", "Export", "PDF/CSV/data export of charts, reports and research output."),
    ("ai_analysis", "premium", "AI Analysis", "LLM-backed interpretation, explanations and source-grounded Q&A."),
    ("research_workspace", "research", "Research Workspace", "Guided research tooling (query builder, hypothesis mining, sweeps)."),
    ("research_projects", "research", "Research Projects", "Persistent research projects/cases/experiments. Monthly-count-limited."),
    ("pattern_discovery", "research", "Pattern Discovery", "Fact-builder-driven statistical pattern discovery over cohorts."),
    ("benchmarking", "research", "Benchmarking", "Benchmark experiments, regression monitoring and validation runs."),
    ("knowledge_graph", "research", "Knowledge Graph", "Knowledge-graph construction and graph analytics."),
    ("knowledge_rag", "research", "Knowledge / RAG", "Classical-text ingestion, embeddings and grounded retrieval."),
    ("api_sdk", "enterprise", "API / SDK Access", "Programmatic API access (mobile sync endpoints today, SDK later)."),
]

# ── Decided Feature x Plan x Action matrix cells ─────────────────────────────
# feature_key -> plan_code -> {action: bool}
DECISION_ENTITLEMENTS: dict[str, dict[str, dict[str, bool]]] = {
    "saved_horoscopes": {
        "FREE":     {"view": True, "create": True, "edit": True},
        "PRO":      {"view": True, "create": True, "edit": True},
        "RESEARCH": {"view": True, "create": True, "edit": True},
        "CUSTOM":   {"view": True, "create": True, "edit": True},
    },
    "research_projects": {
        "PRO":      {"view": True, "create": True},
        "RESEARCH": {"view": True, "create": True},
        # FREE (0/month) and CUSTOM (configurable): no decided cells -> no rows
    },
}

# ── Plan limits ──────────────────────────────────────────────────────────────
PLAN_LIMIT_ROWS = {
    "FREE":     {"saved_horoscopes": 5,   "research_projects_monthly": 0},
    "PRO":      {"saved_horoscopes": 50,  "research_projects_monthly": 1},
    "RESEARCH": {"saved_horoscopes": 100, "research_projects_monthly": 3},
    "CUSTOM":   {"saved_horoscopes": None, "research_projects_monthly": None},
}

_ACTION_COLUMNS = ("view", "create", "edit", "run", "export")
def upgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import text

    plan_ids: dict[str, uuid.UUID] = {}
    for code, name, description, is_active in PLAN_ROWS:
        pid = uuid.uuid4()
        plan_ids[code] = pid
        bind.execute(
            text(
                "INSERT INTO plans (id, plan_code, name, description, is_active) "
                "VALUES (:id, :code, :name, :description, :active)"
            ),
            {"id": pid, "code": code, "name": name,
             "description": description, "active": is_active},
        )

    feature_lookup: dict[str, uuid.UUID] = {}
    for key, category, name, description in FEATURE_ROWS:
        fid = uuid.uuid4()
        feature_lookup[key] = fid
        bind.execute(
            text(
                "INSERT INTO features "
                "(id, feature_key, name, description, category, is_system) "
                "VALUES (:id, :key, :name, :description, :category, :is_system)"
            ),
            {"id": fid, "key": key, "name": name, "description": description,
             "category": category, "is_system": True},
        )

    for code, vals in PLAN_LIMIT_ROWS.items():
        bind.execute(
            text(
                "INSERT INTO plan_limits "
                "(id, plan_id, saved_horoscopes, research_projects_monthly) "
                "VALUES (:id, :plan_id, :saved_horoscopes, :research_projects_monthly)"
            ),
            {
                "id": uuid.uuid4(),
                "plan_id": plan_ids[code],
                "saved_horoscopes": vals["saved_horoscopes"],
                "research_projects_monthly": vals["research_projects_monthly"],
            },
        )

    for feature_key, by_plan in DECISION_ENTITLEMENTS.items():
        feature_id = feature_lookup[feature_key]
        for plan_code, actions in by_plan.items():
            row = {
                "id": uuid.uuid4(),
                "plan_id": plan_ids[plan_code],
                "feature_id": feature_id,
            }
            for a in _ACTION_COLUMNS:
                row[f"can_{a}"] = bool(actions.get(a, False))
            bind.execute(
                text(
                    "INSERT INTO plan_features "
                    "(id, plan_id, feature_id, can_view, can_create, can_edit, can_run, can_export) "
                    "VALUES (:id, :plan_id, :feature_id, :can_view, :can_create, "
                    ":can_edit, :can_run, :can_export)"
                ),
                row,
            )


def downgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import text
    # Cleanup in dependency order (child -> parent).
    bind.execute(text("DELETE FROM plan_features"))
    bind.execute(text("DELETE FROM plan_limits"))
    bind.execute(text("DELETE FROM features"))
    bind.execute(text("DELETE FROM plans"))