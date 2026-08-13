"""
AstroOS — Report API Schemas (Module 20 — HTTP surface)

Pydantic request/response models for the Report Engine endpoints.

ReportEngine (apps/api/services/report_engine.py) is a pure assembly layer:
it takes already-computed domain objects (D1Chart, Timeline,
VerificationFindings, AggregateReport) and composes them into a
ChartReport / ResearchReport / ComparisonReport. It never calls another
engine and never performs astrology or statistics itself.

To keep these endpoints self-contained (no dependency on other routers'
response shapes, which are being built concurrently), the chart itself is
computed here from raw birth data using the same HoroscopeEngine flow as
/horoscope/d1 — see routers/report.py's _get_horoscope_engine.

Timeline / Verification / Statistics inputs are accepted at "summary"
granularity rather than as full domain-object mirrors: ReportEngine's own
extraction functions (_extract_timeline_summary, _extract_verification_summary,
_extract_statistics_summary) only ever read a small, fixed subset of fields
from those objects (see report_engine.py). Modelling the full nested
graphs (Timeline.entries[].analysis -> EventAnalysis -> ... ,
VerificationFindings.verification_pairs[], AggregateReport.distributions[])
down to their last field would add a large amount of schema surface that
the engine never reads. The router fills the remaining required-but-unused
dataclass fields with empty/placeholder values when reconstructing the
domain object to hand to the engine.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput

# ── Shared literals (same convention as schemas/divisional.py, schemas/dasha.py) ──

AlignmentCode = Literal["confirmed", "untested", "category_mismatch", "not_applicable"]
StrengthCode = Literal["high", "medium", "low", "unknown"]


# ── Summary-level inputs for the optional Timeline/Verification/Statistics sections ──


class TimelineSummaryInput(BaseModel):
    """
    Subset of Timeline actually read by ReportEngine._extract_timeline_summary.

    Corresponds to Timeline.summary (a TimelineSummary) — total_events,
    date_range, events_per_category.
    """

    total_events: int = 0
    date_range: Optional[tuple[date, date]] = None
    events_per_category: dict[str, int] = Field(default_factory=dict)


class VerificationPairInput(BaseModel):
    """Subset of VerificationPair actually read by the report/AI engines."""

    alignment: AlignmentCode = "not_applicable"
    strength: StrengthCode = "unknown"


class VerificationSummaryInput(BaseModel):
    """
    Subset of VerificationFindings actually read by the report/AI engines:
    total_pairs, total_rules_evaluated, and each pair's alignment/strength.
    """

    total_pairs: int = 0
    total_rules_evaluated: int = 0
    pairs: list[VerificationPairInput] = Field(default_factory=list)


class DistributionInput(BaseModel):
    """Mirrors domain.statistics.Distribution."""

    label: str
    variable: str
    bins: list[str] = Field(default_factory=list)
    counts: list[int] = Field(default_factory=list)
    total: Optional[int] = Field(
        default=None, description="Defaults to sum(counts) when omitted."
    )


class StatisticsSummaryInput(BaseModel):
    """Subset of AggregateReport actually read by the report/AI engines."""

    sample_size: int = 0
    distributions: list[DistributionInput] = Field(default_factory=list)


# ── Requests ──────────────────────────────────────────────────────────────────


class ChartReportRequest(BirthDataInput):
    """Request body for POST /report/chart."""

    title: str = "Chart Analysis"
    subject_name: str = "Unnamed"
    generated_by: Optional[str] = None
    timeline: Optional[TimelineSummaryInput] = None
    verification: Optional[VerificationSummaryInput] = None
    statistics: Optional[StatisticsSummaryInput] = None


class ResearchReportRequest(BaseModel):
    """
    Request body for POST /report/research.

    snapshot_labels stands in for the full AstrologicalSnapshot collection —
    ReportEngine.build_research_report only reads len(snapshots) and each
    snapshot's `.label` (see report_engine.py's snapshot_overview section).
    """

    project_id: uuid.UUID
    snapshot_labels: Annotated[list[str], Field(min_length=1)]
    title: str = "Research Analysis"
    generated_by: Optional[str] = None
    statistics: Optional[StatisticsSummaryInput] = None


class ChartComparisonInput(BirthDataInput):
    """One chart + its comparison label."""

    label: str


class ComparisonReportRequest(BaseModel):
    """Request body for POST /report/comparison. Requires 2+ charts."""

    charts: Annotated[list[ChartComparisonInput], Field(min_length=2)]
    title: str = "Chart Comparison"
    generated_by: Optional[str] = None


# ── Response pieces ───────────────────────────────────────────────────────────


class ReportSectionResponse(BaseModel):
    """Response payload describing report section data."""
    title: str
    section_type: str
    data: dict = Field(default_factory=dict)
    order: int = 0


class ReportMetadataResponse(BaseModel):
    """Response payload describing report metadata data."""
    report_id: uuid.UUID
    report_type: str
    report_version: str
    generated_at: datetime
    engine_versions: dict[str, str] = Field(default_factory=dict)
    chart_id: Optional[uuid.UUID] = None
    research_project_id: Optional[uuid.UUID] = None
    generated_by: Optional[str] = None


class ChartReportResponse(BaseModel):
    """Response payload describing chart report data."""
    metadata: ReportMetadataResponse
    title: str
    subject_name: str
    sections: list[ReportSectionResponse]


class ResearchReportResponse(BaseModel):
    """Response payload describing research report data."""
    metadata: ReportMetadataResponse
    title: str
    snapshot_count: int
    sections: list[ReportSectionResponse]


class ComparisonReportResponse(BaseModel):
    """Response payload describing comparison report data."""
    metadata: ReportMetadataResponse
    title: str
    # No chart_ids: ReportEngine.build_comparison_report's `charts` input is
    # tuple[D1Chart, ...] and D1Chart has no id field, so the engine's
    # chart_ids field can never be genuinely populated (always ()). Dropped
    # from the response rather than surfacing an always-empty list.
    chart_labels: list[str]
    sections: list[ReportSectionResponse]
