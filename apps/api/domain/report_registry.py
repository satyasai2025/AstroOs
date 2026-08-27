"""
AstroOS — Report Registry.

Single source of truth for "which reports exist, who may download them, and
how many pages each must be". Defined by the report tier architecture spec,
section 5.

Design rules the spec is explicit about:

  · Reports are TIERED and MODULAR — Basic / Detailed / domain analyses are
    separate documents, never one report that grows.
  · Subscription checks do NOT live inside report builders. A builder renders;
    the registry declares the entitlement, and the router enforces it with the
    existing `require_entitlement` dependency.
  · The frontend derives its Export menu from
    (application context + user entitlement + this registry) — it must not
    hard-code report lists.

Entitlement alignment: `minimum_entitlement` names a plan_code that already
exists in the Phase 2 plans table (FREE / PRO / RESEARCH / CUSTOM), and
`feature_key` / `action` name a real cell of
`apps.api.services.feature_catalog.DECIDED_MATRIX`, so a registry entry can be
handed straight to `require_entitlement(feature_key, action)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ReportDomain(str, Enum):
    """Which part of the product a report belongs to."""

    FOUNDATION = "foundation"   # birth-chart reference sheets
    ANALYSIS = "analysis"       # domain predictions (marriage, career, ...)
    TIMING = "timing"           # period/transit documents
    RESEARCH = "research"       # evidence / benchmark output


class ReportFormat(str, Enum):
    PDF = "PDF"
    HTML = "HTML"
    JSON = "JSON"


# Plan codes as seeded by migration 0030. Kept as a tuple rather than an enum
# so a CUSTOM/admin-defined plan does not require a code change here.
PLAN_ORDER: tuple[str, ...] = ("FREE", "PRO", "RESEARCH", "CUSTOM")


@dataclass(frozen=True)
class ReportDefinition:
    """One downloadable report."""

    report_type: str
    domain: ReportDomain
    title: str
    description: str

    minimum_entitlement: str
    """plan_code from the plans table — the lowest tier that may download."""

    feature_key: str
    """DECIDED_MATRIX feature this maps to, for require_entitlement()."""

    action: str = "export"
    """Matrix action. Reports are downloads, so 'export' unless stated."""

    page_target: int | None = None
    """Exact A4 page count. None = dynamic length (domain analyses)."""

    supported_formats: tuple[ReportFormat, ...] = (
        ReportFormat.PDF, ReportFormat.HTML, ReportFormat.JSON,
    )

    required_context: tuple[str, ...] = ("birth_chart",)
    """Context keys the caller must supply for this report to be buildable."""

    report_version: str = "1.0"

    template_name: str | None = None
    """Jinja template, when the report has one."""

    implemented: bool = False
    """
    False = declared but not yet buildable. Declared-not-built is deliberate:
    the Export menu and entitlement matrix can be reasoned about before every
    document exists, and `available_for()` filters these out so the UI never
    offers a download that would 404.
    """

    def is_available_to(self, plan_code: str) -> bool:
        """Whether `plan_code` meets this report's minimum tier."""
        if self.minimum_entitlement == "FREE":
            return True
        if plan_code == "CUSTOM":
            # CUSTOM is configured per agreement — the plan_features rows, not
            # this ordering, decide. Treated as eligible here and gated by
            # require_entitlement at the route.
            return True
        try:
            return PLAN_ORDER.index(plan_code) >= PLAN_ORDER.index(
                self.minimum_entitlement
            )
        except ValueError:
            return False


# ── The registry ─────────────────────────────────────────────────────────
#
# page_target values are contract, not aspiration: they are asserted against a
# real rendered PDF in tests/unit/test_report_page_geometry.py.

REPORTS: tuple[ReportDefinition, ...] = (
    ReportDefinition(
        report_type="BIRTH_CHART_FOUNDATION",
        domain=ReportDomain.FOUNDATION,
        title="Birth Chart Foundation",
        description=(
            "Astronomical reference sheet — birth details, panchanga, D-1 and "
            "D-9 charts, full body table and the Vimshottari sequence. "
            "Contains no predictive interpretation."
        ),
        minimum_entitlement="FREE",
        feature_key="reports",
        page_target=2,
        template_name="birth_chart_foundation.html",
        report_version="1.1",
        implemented=True,
    ),
    ReportDefinition(
        report_type="BIRTH_CHART_DETAILED",
        domain=ReportDomain.FOUNDATION,
        title="Detailed Birth Report",
        description=(
            "Extended birth report — planetary detail, divisional charts, "
            "dasha and strength, Ashtakavarga and yogas, plus a structured "
            "chart summary."
        ),
        minimum_entitlement="PRO",
        feature_key="reports",
        page_target=5,
        template_name="birth_chart_detailed.html",
        report_version="1.0",
        implemented=True,
    ),
    ReportDefinition(
        report_type="MARRIAGE_ANALYSIS",
        domain=ReportDomain.ANALYSIS,
        title="Marriage Analysis",
        description="Promise and timing of marriage, with classical evidence.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        required_context=("birth_chart",),
        template_name="domain_analysis.html",
        implemented=True,
    ),
    ReportDefinition(
        report_type="CAREER_ANALYSIS",
        domain=ReportDomain.ANALYSIS,
        title="Career Analysis",
        description="Promise and timing of career direction and advancement.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        template_name="domain_analysis.html",
        implemented=True,
    ),
    ReportDefinition(
        report_type="DASHA_ANALYSIS",
        domain=ReportDomain.ANALYSIS,
        title="Dasha Analysis",
        description="Period-by-period reading of the Vimshottari sequence.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        required_context=("birth_chart", "dasha"),
        template_name="domain_analysis.html",
        implemented=True,
    ),
    ReportDefinition(
        report_type="TRANSIT_ANALYSIS",
        # TIMING, not ANALYSIS: a gochara report reads periods, not a birth
        # promise. The pre-existing registry classified it the same way, and
        # leaving it under ANALYSIS would put it in a different bucket from
        # SARVATOBHADRA_VEDHA, which is the same kind of document.
        domain=ReportDomain.TIMING,
        title="Transit Analysis",
        description="Current and forthcoming gochara influences.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        required_context=("birth_chart", "transit"),
        implemented=False,
    ),
    # ── Carried over from the pre-existing registry ───────────────────────
    #
    # This module replaced an earlier `REPORT_REGISTRY` (commit ab3d084) that
    # declared these report types. Nothing imported it — it was unwired
    # scaffolding — but it recorded real product scope, and dropping it during
    # the rewrite would have silently narrowed the roadmap. They are restored
    # here as declared-not-built so `available_for()` still filters them out
    # of the Export menu while the intent stays on the record.
    #
    # Deliberately NOT carried over: the old "markdown" export format. No
    # renderer produces it, and advertising a format we cannot generate is the
    # same defect as the PDF path that raised on every request.

    ReportDefinition(
        report_type="MARRIAGE_COMPATIBILITY",
        domain=ReportDomain.ANALYSIS,
        title="Marriage Compatibility Assessment",
        description=(
            "Two-chart matching: Ashtakoota, Mangal Dosha balance and "
            "planet/house compatibility with exceptions."
        ),
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        # Distinct from MARRIAGE_ANALYSIS, which reads one chart's promise.
        # This needs a second chart, so it can never be offered from a
        # single-chart context.
        required_context=("birth_chart", "partner_chart"),
        implemented=False,
    ),
    ReportDefinition(
        report_type="WEALTH_FINANCE",
        domain=ReportDomain.ANALYSIS,
        title="Wealth & Finance Analysis",
        description="Promise and timing of wealth, income and accumulation.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        implemented=False,
    ),
    ReportDefinition(
        report_type="HEALTH_VITALITY",
        domain=ReportDomain.ANALYSIS,
        title="Health & Vitality Analysis",
        description="Constitutional strength and affliction periods.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        implemented=False,
    ),
    ReportDefinition(
        report_type="FOREIGN_JOB",
        domain=ReportDomain.ANALYSIS,
        title="Foreign Job & International Career",
        description=(
            "12th/11th/10th house analysis, Videsh Dhan yogas and favourable "
            "timing windows."
        ),
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        implemented=False,
    ),
    ReportDefinition(
        report_type="MULTI_VARGA",
        domain=ReportDomain.FOUNDATION,
        title="Divisional (Varga) Chart Set",
        description="Shodashavarga divisional charts, six per A4 sheet.",
        minimum_entitlement="PRO",
        feature_key="reports",
        page_target=None,
        implemented=False,
    ),
    ReportDefinition(
        report_type="SHADBALA_ASHTAKAVARGA",
        domain=ReportDomain.FOUNDATION,
        title="Shadbala & Ashtakavarga Reference",
        description="Full six-fold strength and Ashtakavarga bindu tables.",
        minimum_entitlement="PRO",
        feature_key="reports",
        page_target=None,
        implemented=False,
    ),
    ReportDefinition(
        report_type="SARVATOBHADRA_VEDHA",
        domain=ReportDomain.TIMING,
        title="Sarvatobhadra Chakra & Vedha",
        description="Sarvatobhadra chakra with vedha and transit triggers.",
        minimum_entitlement="RESEARCH",
        feature_key="reports",
        page_target=None,
        required_context=("birth_chart", "transit"),
        implemented=False,
    ),
    ReportDefinition(
        report_type="RESEARCH_EVIDENCE",
        domain=ReportDomain.RESEARCH,
        title="Research / Evidence Report",
        description="Rule, evidence and benchmark output for a research case.",
        minimum_entitlement="RESEARCH",
        feature_key="research_projects",
        page_target=None,
        required_context=("research_case",),
        implemented=False,
    ),
)

_BY_TYPE = {r.report_type: r for r in REPORTS}


def get_report(report_type: str) -> ReportDefinition:
    """Look up one report. Raises KeyError with the valid set on a typo."""
    try:
        return _BY_TYPE[report_type]
    except KeyError as exc:
        raise KeyError(
            f"unknown report_type {report_type!r}; "
            f"known: {sorted(_BY_TYPE)}"
        ) from exc


def available_for(
    plan_code: str,
    *,
    domain: ReportDomain | None = None,
    context: Iterable[str] | None = None,
    include_unimplemented: bool = False,
) -> list[ReportDefinition]:
    """
    Reports a plan may download, optionally narrowed to an app context.

    This is what the contextual Export menu is built from: the Birth Chart app
    passes context={"birth_chart"}, the Dasha app adds "dasha", and so on, so
    each app offers only the reports it can actually produce.
    """
    have = set(context) if context is not None else None
    out = []
    for r in REPORTS:
        if not include_unimplemented and not r.implemented:
            continue
        if domain is not None and r.domain is not domain:
            continue
        if not r.is_available_to(plan_code):
            continue
        if have is not None and not set(r.required_context).issubset(have):
            continue
        out.append(r)
    return out
