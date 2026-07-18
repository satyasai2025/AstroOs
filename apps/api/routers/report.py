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

from fastapi import APIRouter, Depends, HTTPException, Response, status

from apps.api.dependencies import get_ephemeris_wrapper
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
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.report_engine import ReportEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["Report"])

_PLACEHOLDER_CHART_ID = uuid.UUID(int=0)


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


@router.post("/chart/pdf", summary="Generate chart report as PDF")
async def generate_chart_pdf(
    body: ChartReportRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """Generate a chart report as PDF using WeasyPrint."""
    from apps.api.services.report_template_engine import ReportTemplateEngine
    horoscope_engine = HoroscopeEngine(wrapper)
    chart = await asyncio.to_thread(
        horoscope_engine.generate_d1,
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
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
    pdf_bytes = ReportTemplateEngine.render_pdf(report.model_dump())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{body.title or "report"}.pdf"'},
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
    csv_content = ReportTemplateEngine.render_csv(report.model_dump())
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{body.title or "report"}.csv"'},
    )
