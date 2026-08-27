"""
AstroOS — Report Router (Module 20 — HTTP surface)

HTTP adapter layer over ReportEngine. ReportEngine itself never calls
another engine (see report_engine.py's module docstring) — it only
composes already-computed domain objects into report sections. This
router:
  1. Computes the D1Chart(s) from raw birth data the same way
     POST /horoscope/d1 does.
  2. Reconstructs minimal Timeline / VerificationFindings / AggregateReport
     placeholder objects from the "summary" inputs in schemas/report.py —
     ReportEngine's own extraction functions only ever read a small fixed
     subset of fields from those objects (see report_engine.py's
     _extract_timeline_summary / _extract_verification_summary /
     _extract_statistics_summary), so every other required dataclass
     field is filled with a placeholder value that is never read.

Endpoints
---------
POST /report/chart      — Full single-chart report.
POST /report/research   — Snapshot-collection report (summary-level).
POST /report/comparison — Side-by-side comparison of 2+ charts.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_db_session,
    get_ephemeris_wrapper,
    require_authenticated,
    require_entitlement,
)
from apps.api.domain.user import User
from apps.api.domain.research import AstrologicalSnapshot
from apps.api.domain.statistics import AggregateReport, DatasetMetadata, Distribution
from apps.api.domain.timeline import Timeline, TimelineSummary
from apps.api.domain.verification import (
    Alignment,
    VerificationFindings,
    VerificationPair,
    VerificationStrength,
)
from apps.api.schemas.report import (
    ChartComparisonInput,
    ChartReportRequest,
    ChartReportResponse,
    ComparisonReportRequest,
    ComparisonReportResponse,
    ReportMetadataResponse,
    ReportSectionResponse,
    ResearchReportRequest,
    ResearchReportResponse,
    StatisticsSummaryInput,
    TimelineSummaryInput,
    VerificationSummaryInput,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.report_engine import ReportEngine
from apps.api.services.yoga_engine import YogaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["Report"])

_PLACEHOLDER_CHART_ID = uuid.UUID(int=0)


def _compute_dasha_and_yogas(
    wrapper: EphemerisWrapper,
    chart,
    body: ChartReportRequest,
):
    """
    Optional Vimshottari dasha + yoga sections for a chart report.
    Both are independent, already-existing engines (DashaEngine,
    YogaEngine) — this just runs them and finds the dasha chain active
    as of "today" (report generation time), same pattern as
    prediction_orchestration.py / timeline.py already use elsewhere.
    """
    dasha_tree = None
    active_chain: tuple = ()
    if body.include_dasha:
        dasha_engine = DashaEngine(wrapper)
        dasha_tree = dasha_engine.compute_vimshottari(
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        active_chain = find_active_dasha_chain(dasha_tree, date.today())

    yoga_results = None
    if body.include_yogas:
        yoga_results = YogaEngine().evaluate_with_strength(chart)

    return dasha_tree, active_chain, yoga_results


def _metadata_response(m) -> ReportMetadataResponse:
    return ReportMetadataResponse(
        report_id=m.report_id, report_type=m.report_type, report_version=m.report_version,
        generated_at=m.generated_at, engine_versions=dict(m.engine_versions),
        chart_id=m.chart_id, research_project_id=m.research_project_id,
        generated_by=m.generated_by,
    )


def _sections_response(sections) -> list[ReportSectionResponse]:
    return [
        ReportSectionResponse(
            title=s.title, section_type=s.section_type, data=dict(s.content.data), order=s.order
        )
        for s in sections
    ]


def _build_timeline(summary: TimelineSummaryInput | None) -> Timeline | None:
    if summary is None:
        return None
    date_range = summary.date_range or (date.today(), date.today())
    return Timeline(
        chart_id=_PLACEHOLDER_CHART_ID,
        entries=(),
        summary=TimelineSummary(
            total_events=summary.total_events,
            date_range=date_range,
            events_per_category=dict(summary.events_per_category),
            events_per_dasha_system={},
            verified_count=0,
            unverified_count=0,
        ),
        dasha_breakdown={},
        clusters=(),
    )


def _build_verification(summary: VerificationSummaryInput | None) -> VerificationFindings | None:
    if summary is None:
        return None
    pairs = tuple(
        VerificationPair(
            rule_id="", rule_name="", rule_category="", rule_matched=True,
            event_id=uuid.uuid4(), event_date=date.today(), event_title="",
            event_description=None, event_category=None, event_is_verified=False,
            derived_facts={}, inferred_domains=(),
            alignment=Alignment(p.alignment), strength=VerificationStrength(p.strength),
            explanation="",
        )
        for p in summary.pairs
    )
    return VerificationFindings(
        chart_id=_PLACEHOLDER_CHART_ID,
        period_covered=(date.today(), date.today()),
        total_events=0,
        total_rules_evaluated=summary.total_rules_evaluated,
        total_pairs=summary.total_pairs,
        rule_summaries=(),
        verification_pairs=pairs,
    )


def _build_statistics(summary: StatisticsSummaryInput | None) -> AggregateReport | None:
    if summary is None:
        return None
    distributions = tuple(
        Distribution(
            label=d.label, variable=d.variable, bins=tuple(d.bins), counts=tuple(d.counts),
            total=d.total if d.total is not None else sum(d.counts),
        )
        for d in summary.distributions
    )
    return AggregateReport(
        title="",
        metadata=DatasetMetadata(sample_size=summary.sample_size, snapshot_count=summary.sample_size),
        distributions=distributions,
    )


@router.post("/chart", response_model=ChartReportResponse, summary="Build a full single-chart report")
async def build_chart_report(
    body: ChartReportRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ChartReportResponse:
    horoscope_engine = HoroscopeEngine(wrapper)
    try:
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
            node_type=body.node_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing chart for report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chart for report.",
        )

    report = ReportEngine.build_chart_report(
        chart,
        timeline=_build_timeline(body.timeline),
        verification=_build_verification(body.verification),
        stats=_build_statistics(body.statistics),
        title=body.title,
        subject_name=body.subject_name,
        generated_by=body.generated_by,
    )
    return ChartReportResponse(
        metadata=_metadata_response(report.metadata),
        title=report.title,
        subject_name=report.subject_name,
        sections=_sections_response(report.sections),
    )


@router.post(
    "/research", response_model=ResearchReportResponse, summary="Build a research snapshot report"
)
async def build_research_report(body: ResearchReportRequest) -> ResearchReportResponse:
    snapshots = tuple(
        AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=body.project_id, chart_id=uuid.uuid4(),
            label=label, captured_at=datetime.now(timezone.utc), chart_ref=None,
        )
        for label in body.snapshot_labels
    )
    report = ReportEngine.build_research_report(
        body.project_id, snapshots,
        stats=_build_statistics(body.statistics),
        title=body.title,
        generated_by=body.generated_by,
    )
    return ResearchReportResponse(
        metadata=_metadata_response(report.metadata),
        title=report.title,
        snapshot_count=report.snapshot_count,
        sections=_sections_response(report.sections),
    )


@router.post(
    "/comparison", response_model=ComparisonReportResponse, summary="Compare 2+ charts side by side"
)
async def build_comparison_report(
    body: ComparisonReportRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ComparisonReportResponse:
    horoscope_engine = HoroscopeEngine(wrapper)

    async def _compute(c: ChartComparisonInput):
        return await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=c.birth_datetime_utc,
            latitude=c.latitude,
            longitude=c.longitude,
            ayanamsa=c.ayanamsa,
            house_system=c.house_system,
        )

    try:
        charts = tuple([await _compute(c) for c in body.charts])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing charts for comparison report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute charts for comparison report.",
        )

    labels = tuple(c.label for c in body.charts)
    try:
        report = ReportEngine.build_comparison_report(
            charts, labels, title=body.title, generated_by=body.generated_by
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return ComparisonReportResponse(
        metadata=_metadata_response(report.metadata),
        title=report.title,
        chart_labels=list(report.chart_labels),
        sections=_sections_response(report.sections),
    )


@router.get("/templates", summary="List available report templates")
async def list_available_templates() -> list[str]:
    """Return list of available HTML templates for PDF generation."""
    from apps.api.services.report_template_engine import ReportTemplateEngine
    return ReportTemplateEngine.list_templates()


@router.post(
    "/chart/pdf",
    summary="Generic chart report as PDF (legacy)",
    deprecated=True,
)
async def generate_chart_pdf(
    body: ChartReportRequest,
    template_name: str = "horoscope.html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """Generic chart report as PDF. Superseded by the report registry routes.

    IMPORTANT — what ``template_name`` actually does. The selectable
    templates (career.html, marriage.html, health.html, wealth.html,
    spiritual.html, transit.html) are ~140-byte stubs that all extend
    _report_layout.html and differ ONLY in their title and heading string.
    They are byte-identical apart from the domain word. Passing
    ``career.html`` therefore returns the same generic chart document as
    ``horoscope.html``, headed "Career Report" — it performs no career
    analysis of any kind.

    For a real domain report with houses, karakas, cited classical rules and
    dasha timing, use the registry routes: POST /report/analysis/career,
    /report/analysis/marriage, /report/analysis/dasha. Those are declared in
    the report registry and gated by require_entitlement.

    Kept because existing callers and scripts/check_phase_f.py depend on it.
    """
    from apps.api.services.report_template_engine import ReportTemplateEngine
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = await asyncio.to_thread(
        horoscope_engine.generate_d1,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        node_type=body.node_type,
    )
    dasha_tree, active_dasha_chain, yoga_results = _compute_dasha_and_yogas(wrapper, chart, body)
    report = ReportEngine.build_chart_report(
        chart,
        timeline=_build_timeline(body.timeline),
        verification=_build_verification(body.verification),
        stats=_build_statistics(body.statistics),
        dasha_tree=dasha_tree,
        active_dasha_chain=active_dasha_chain,
        yoga_results=yoga_results,
        title=body.title,
        subject_name=body.subject_name,
        generated_by=body.generated_by,
    )
    # Convert domain dataclass → Pydantic model before calling .model_dump()
    # (AMP-009 fix: ChartReport is a plain @dataclass, not a BaseModel)
    resp = ChartReportResponse(
        metadata=_metadata_response(report.metadata),
        title=report.title,
        subject_name=report.subject_name or "",
        sections=_sections_response(report.sections),
    )
    pdf_bytes = ReportTemplateEngine.render_pdf(resp.model_dump(), template_name=template_name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{body.title or "report"}.pdf"'},
    )


@router.post(
    "/chart/html",
    summary="Generic chart report as HTML (legacy)",
    deprecated=True,
)
async def generate_chart_html(
    body: ChartReportRequest,
    template_name: str = "horoscope.html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """Generic chart report as standalone HTML. See generate_chart_pdf.

    The selectable domain templates change only the heading text — they do
    not produce a domain analysis. Use POST /report/analysis/{career,
    marriage,dasha} for the real reports.
    """
    from apps.api.services.report_template_engine import ReportTemplateEngine
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = await asyncio.to_thread(
        horoscope_engine.generate_d1,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        node_type=body.node_type,
    )
    dasha_tree, active_dasha_chain, yoga_results = _compute_dasha_and_yogas(wrapper, chart, body)
    report = ReportEngine.build_chart_report(
        chart,
        timeline=_build_timeline(body.timeline),
        verification=_build_verification(body.verification),
        stats=_build_statistics(body.statistics),
        dasha_tree=dasha_tree,
        active_dasha_chain=active_dasha_chain,
        yoga_results=yoga_results,
        title=body.title,
        subject_name=body.subject_name,
        generated_by=body.generated_by,
    )
    # Convert domain dataclass → Pydantic model before calling .model_dump()
    # (AMP-009 fix: ChartReport is a plain @dataclass, not a BaseModel)
    resp = ChartReportResponse(
        metadata=_metadata_response(report.metadata),
        title=report.title,
        subject_name=report.subject_name or "",
        sections=_sections_response(report.sections),
    )
    html_content = ReportTemplateEngine.render_html(resp.model_dump(), template_name=template_name)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="{body.title or "report"}.html"'},
    )


@router.post("/chart/csv", summary="Generate chart report as CSV")
async def generate_chart_csv(
    body: ChartReportRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """Generate a chart report as CSV."""
    from apps.api.services.report_template_engine import ReportTemplateEngine
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = await asyncio.to_thread(
        horoscope_engine.generate_d1,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        node_type=body.node_type,
    )
    report = ReportEngine.build_chart_report(
        chart,
        timeline=_build_timeline(body.timeline),
        verification=_build_verification(body.verification),
        stats=_build_statistics(body.statistics),
        title=body.title,
        subject_name=body.subject_name,
        generated_by=body.generated_by,
    )
@router.get("/registry", summary="List reports available to the caller's plan")
async def list_available_reports(
    context: str | None = Query(
        None,
        description=(
            "Comma-separated app context keys, e.g. 'birth_chart' or "
            "'birth_chart,dasha'. Omit for all reports the plan allows."
        ),
    ),
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_authenticated),
) -> list[dict]:
    """
    Drives the contextual Export menu.

    The frontend must not hard-code report lists or subscription checks — it
    asks here with its current app context and renders whatever comes back.
    Entitlement is resolved from the caller's actual plan.
    """
    from apps.api.domain.report_registry import available_for
    from apps.api.services.entitlement_service import EntitlementService

    plan = await EntitlementService(session).resolve_user_plan(user)
    plan_code = getattr(plan, "plan_code", "FREE")

    ctx = {c.strip() for c in context.split(",") if c.strip()} if context else None
    return [
        {
            "report_type": r.report_type,
            "domain": r.domain.value,
            "title": r.title,
            "description": r.description,
            "page_target": r.page_target,
            "minimum_entitlement": r.minimum_entitlement,
            "supported_formats": [f.value for f in r.supported_formats],
            "report_version": r.report_version,
        }
        for r in available_for(plan_code, context=ctx)
    ]


async def _render_registry_report(
    *,
    report_type: str,
    body: ChartReportRequest,
    export_format: str,
    wrapper: EphemerisWrapper,
) -> Response:
    """
    Shared render path for every registry-declared birth report.

    Entitlement is NOT checked here — it is declared on the ReportDefinition
    and enforced by the route's require_entitlement dependency, so a builder
    can never become a second, divergent paywall.
    """
    from apps.api.domain.report_registry import get_report
    from apps.api.services.report_assembler import ReportAssembler
    from apps.api.services.report_template_engine import ReportTemplateEngine

    definition = get_report(report_type)

    horoscope_engine = HoroscopeEngine(wrapper)
    chart = await asyncio.to_thread(
        horoscope_engine.generate_d1,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
        node_type=body.node_type,
    )

    report_data = await asyncio.to_thread(
        ReportAssembler(wrapper).assemble,
        report_type=report_type,
        chart=chart,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        subject_name=body.subject_name or "Subject",
        place_name=getattr(body, "place_name", "") or "—",
        ayanamsa=body.ayanamsa,
        ayanamsa_name=(body.ayanamsa or "lahiri").capitalize(),
        house_system_code=body.house_system,
    )

    stem = (body.subject_name or "chart").replace(" ", "_")
    fmt = export_format.lower()

    if fmt == "json":
        import json
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{stem}.json"'},
        )
    if fmt == "pdf":
        # page_target is the registry's contract (Foundation 2, Detailed 5).
        # Passing it makes the renderer verify the result, so a template
        # regression fails the request instead of shipping a 6-page "2-page"
        # report. Domain analyses declare None — their length is dynamic.
        pdf_bytes = ReportTemplateEngine.render_pdf(
            report_data,
            template_name=definition.template_name,
            expected_pages=definition.page_target,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{stem}.pdf"'},
        )
    html_content = ReportTemplateEngine.render_html(
        report_data, template_name=definition.template_name
    )
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="{stem}.html"'},
    )


@router.post(
    "/foundation/birth-chart",
    summary="Birth Chart Foundation — 2-page A4 reference sheet (free tier)",
)
async def generate_foundation_birth_chart(
    body: ChartReportRequest,
    export_format: str = "html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """Free-tier reference sheet. Declared FREE in the report registry."""
    return await _render_registry_report(
        report_type="BIRTH_CHART_FOUNDATION",
        body=body,
        export_format=export_format,
        wrapper=wrapper,
    )


@router.post(
    "/detailed/birth-chart",
    summary="Detailed Birth Report — 5-page A4 (paid tier)",
    dependencies=[Depends(require_entitlement("reports", "export"))],
)
async def generate_detailed_birth_chart(
    body: ChartReportRequest,
    export_format: str = "html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """
    Paid-tier birth report. `require_entitlement` gates it against the
    Phase 2 matrix; the registry declares PRO as the minimum plan.
    """
    return await _render_registry_report(
        report_type="BIRTH_CHART_DETAILED",
        body=body,
        export_format=export_format,
        wrapper=wrapper,
    )


# ── Premium domain analyses ──────────────────────────────────────────────
#
# One route per domain rather than a single /analysis/{domain} endpoint: each
# is a distinct product with its own entry in the report registry, and an
# explicit route keeps the entitlement dependency visible at the definition
# instead of hidden behind a path parameter.
#
# These carry no `page_target` — a domain report's length follows the number
# of classical rules that fired and dasa windows that qualified, so the
# geometry test asserts A4 dimensions and zero overflow rather than an exact
# page count.


@router.post(
    "/analysis/marriage",
    summary="Marriage Analysis — Promise & Timing (premium)",
    dependencies=[Depends(require_entitlement("reports", "export"))],
)
async def generate_marriage_analysis(
    body: ChartReportRequest,
    export_format: str = "html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    return await _render_registry_report(
        report_type="MARRIAGE_ANALYSIS",
        body=body,
        export_format=export_format,
        wrapper=wrapper,
    )


@router.post(
    "/analysis/career",
    summary="Career Analysis — Promise & Timing (premium)",
    dependencies=[Depends(require_entitlement("reports", "export"))],
)
async def generate_career_analysis(
    body: ChartReportRequest,
    export_format: str = "html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    return await _render_registry_report(
        report_type="CAREER_ANALYSIS",
        body=body,
        export_format=export_format,
        wrapper=wrapper,
    )


@router.post(
    "/analysis/dasha",
    summary="Dasha Analysis — full Vimshottari reading (premium)",
    dependencies=[Depends(require_entitlement("reports", "export"))],
)
async def generate_dasha_analysis(
    body: ChartReportRequest,
    export_format: str = "html",
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    return await _render_registry_report(
        report_type="DASHA_ANALYSIS",
        body=body,
        export_format=export_format,
        wrapper=wrapper,
    )
