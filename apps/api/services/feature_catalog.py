"""
AstroOS — Feature Catalog & Canonical Access Matrix (Phase 2)

Single source of truth for:
  1. The AstroOS feature catalog (keys mirror real routers/UI modules
     discovered during the Phase 1 audit).
  2. The canonical Feature x Plan x Action access-matrix SEED.

IMPORTANT — scope of decided vs unresolved access (do not silently change):

  DECIDED (from the product spec):
    - saved_horoscopes : every plan may VIEW + CREATE; counts limited per plan
                         (FREE=5, PRO=50, RESEARCH=100, CUSTOM=configurable).
    - research_projects: FREE has research_projects_monthly = 0 -> NO access.
                         PRO (1/mo), RESEARCH (3/mo), CUSTOM (configurable)
                         may VIEW + CREATE projects.

  UNRESOLVED (deliberately NOT invented):
    Every other feature x plan combination, and every action beyond the two
    above, is UNRESOLVED. Unresolved cells produce NO entitlement row in the
    database. EntitlementService surfaces them as `unresolved` so future
    phases (or admins) can decide them without code changes.

    The service-level fallback for unresolved cells is controlled by
    Settings.ENTITLEMENT_UNRESOLVED_DEFAULT ("allow" | "deny") and defaults
    to "allow" purely to preserve current behaviour until enforcement lands
    in a later phase. It is a compatibility fallback, NOT a product decision.
"""
from __future__ import annotations

from dataclasses import dataclass

# Sentinel for an unset cell in the matrix; distinct from explicit False.
UNRESOLVED = None


@dataclass(frozen=True)
class FeatureDef:
    """One entry of the feature catalog."""
    key: str
    name: str
    category: str            # core | premium | research | enterprise
    description: str


@dataclass(frozen=True)
class PlanDef:
    """One plan-tier definition."""
    code: str                # FREE | PRO | RESEARCH | CUSTOM
    name: str
    description: str
    is_active: bool = True


@dataclass(frozen=True)
class PlanLimitDef:
    """Concrete numeric limits for one plan (Phase 2 spec)."""
    plan_code: str
    saved_horoscopes: int | None       # None = unlimited / configurable (CUSTOM)
    research_projects_monthly: int | None


# ── Plans ─────────────────────────────────────────────────────────────────────
PLANS: tuple[PlanDef, ...] = (
    PlanDef("FREE", "Free", "Personal astrology essentials."),
    PlanDef("PRO", "Pro", "Serious students: more saved charts and light research."),
    PlanDef("RESEARCH", "Research", "Full research workspace for working researchers."),
    PlanDef("CUSTOM", "Custom", "Bespoke limits and feature access, configured per agreement."),
)

PLAN_LIMITS: tuple[PlanLimitDef, ...] = (
    PlanLimitDef("FREE", saved_horoscopes=5, research_projects_monthly=0),
    PlanLimitDef("PRO", saved_horoscopes=50, research_projects_monthly=1),
    PlanLimitDef("RESEARCH", saved_horoscopes=100, research_projects_monthly=3),
    PlanLimitDef("CUSTOM", saved_horoscopes=None, research_projects_monthly=None),
)

# ── Feature catalog ───────────────────────────────────────────────────────────
FEATURES: tuple[FeatureDef, ...] = (
    # ── Core calculation & exploration ────────────────────────────────────────
    FeatureDef("chart_calculation", "Chart Calculation", "core",
               "Birth-chart computation pipeline (ephemeris, ayanamsa, houses)."),
    FeatureDef("saved_horoscopes", "Saved Horoscopes", "core",
               "Save and revisit birth charts/horoscopes. Count-limited per plan."),
    FeatureDef("planet_explorer", "Planet Explorer", "core",
               "Canonical planet explorer at /charts/planets."),
    FeatureDef("dasha", "Dasha", "core",
               "Vimshottari and multi-dasha timelines and confluence."),
    FeatureDef("varga", "Varga", "core",
               "Divisional charts (D1-D60) via the divisional engine."),
    FeatureDef("transit", "Transit", "core",
               "Gochara transit tracking and transit-pattern scanning."),
    FeatureDef("prashna", "Prashna", "core",
               "Horary (Prashna) chart casting and judgement."),
    # ── Analysis & output ─────────────────────────────────────────────────────
    FeatureDef("analysis", "Analysis", "core",
               "Event analysis, yogas and strength modules (Shadbala, Ashtakavarga)."),
    FeatureDef("reports", "Reports", "core",
               "Narrative and full-life report generation."),
    FeatureDef("export", "Export", "core",
               "PDF/CSV/data export of charts, reports and research output."),
    # ── Premium AI ────────────────────────────────────────────────────────────
    FeatureDef("ai_analysis", "AI Analysis", "premium",
               "LLM-backed interpretation, explanations and source-grounded Q&A."),
    # ── Research workspace ────────────────────────────────────────────────────
    FeatureDef("research_workspace", "Research Workspace", "research",
               "Guided research tooling (query builder, hypothesis mining, sweeps)."),
    FeatureDef("research_projects", "Research Projects", "research",
               "Persistent research projects/cases/experiments. Monthly-count-limited."),
    FeatureDef("pattern_discovery", "Pattern Discovery", "research",
               "Fact-builder-driven statistical pattern discovery over cohorts."),
    FeatureDef("benchmarking", "Benchmarking", "research",
               "Benchmark experiments, regression monitoring and validation runs."),
    # ── Knowledge ─────────────────────────────────────────────────────────────
    FeatureDef("knowledge_graph", "Knowledge Graph", "research",
               "Knowledge-graph construction and graph analytics."),
    FeatureDef("knowledge_rag", "Knowledge / RAG", "research",
               "Classical-text ingestion, embeddings and grounded retrieval."),
    # ── Platform ──────────────────────────────────────────────────────────────
    FeatureDef("api_sdk", "API / SDK Access", "enterprise",
               "Programmatic API access (mobile sync endpoints today, SDK later)."),
)


# ── Decided seed cells of the Feature x Plan x Action matrix ─────────────────
# Everything not listed here is UNRESOLVED by design (see module docstring).
DECIDED_MATRIX: dict[str, dict[str, dict[str, bool]]] = {
    # feature_key -> plan_code -> {action: bool}
    "saved_horoscopes": {
        "FREE":     {"view": True, "create": True},
        "PRO":      {"view": True, "create": True},
        "RESEARCH": {"view": True, "create": True},
        "CUSTOM":   {"view": True, "create": True},
        # edit/run/export: UNRESOLVED for every plan
    },
    "research_projects": {
        "FREE":     {},                       # limit 0/mo -> no access at all
        "PRO":      {"view": True, "create": True},
        "RESEARCH": {"view": True, "create": True},
        "CUSTOM":   {},                       # configurable — left to admins
        # edit/run/export: UNRESOLVED for every plan
    },
}

ACTION_COLUMNS: tuple[str, ...] = ("view", "create", "edit", "run", "export")


def iter_decided_cells():
    """Yield (feature_key, plan_code, {action: bool}) for every decided cell."""
    for feature_key, by_plan in DECIDED_MATRIX.items():
        for plan_code, actions in by_plan.items():
            yield feature_key, plan_code, dict(actions)