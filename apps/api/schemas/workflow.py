"""
AstroOS — Workflow Orchestrator API Schemas (v2 Phase A)

Request/response contract for the Unified Analysis Pipeline
(POST /api/v1/workflow/analyze). The response composes the existing
per-engine response schemas (D1ChartResponse, AllVargaChartsResponse,
DashaTreeResponse, YogaEvaluationResponse, AllAshtakavargaResponse,
TransitResponse, KnowledgeSearchResultResponse, ChartReportResponse)
rather than re-deriving them, plus a handful of new schemas for the
three engines that had no HTTP-facing shape yet: Rule Engine results,
Verification findings, and a Benchmark placeholder (Phase C — no
execution engine exists yet, see ASTROOS_V2_ROADMAP.md).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from apps.api.schemas.ashtakavarga import AllAshtakavargaResponse
from apps.api.schemas.common import BirthDataInput
from apps.api.schemas.dasha import DashaTreeResponse
from apps.api.schemas.divisional import AllVargaChartsResponse
from apps.api.schemas.horoscope import D1ChartResponse
from apps.api.schemas.knowledge import KnowledgeSearchResultResponse
from apps.api.schemas.kp import KPAnalysisResponse
from apps.api.schemas.report import BirthDataInput, ChartReportResponse
from apps.api.schemas.transit import TransitResponse
from apps.api.schemas.yoga import YogaEvaluationResponse

DashaSystem = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


# ── Request ───────────────────────────────────────────────────────────────────


class WorkflowAnalysisRequest(BirthDataInput):
    """One birth-data submission drives the entire pipeline."""

    dasha_system: DashaSystem = "vimshottari"
    transit_datetime_utc: Optional[datetime] = Field(
        default=None, description="Defaults to now (UTC) if omitted — the 'current transits' moment."
    )
    include_vargas: bool = Field(
        default=True, description="Compute all 15 divisional charts. Set false to skip for speed."
    )
    subject_name: str = "Unnamed"
    gender: Optional[str] = Field(
        default=None,
        description="Subject gender: Male, Female, or Other.",
    )
    place_name: Optional[str] = Field(
        default=None,
        description="Human-readable birth place, if resolved on the client (e.g. from place search). Saved on the birth_charts row for display on the saved-charts list.",
    )
    generated_by: Optional[str] = None
    research_project_id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "If supplied, this chart's computed chart/yogas/shadbala/"
            "ashtakavarga/dasha/vargas/timeline/verification are captured "
            "as an AstrologicalSnapshot into this Research project "
            "(POST /research/projects to create one first). Omitted "
            "entirely if not supplied — not every analysis is research."
        ),
    )
    persist: bool = Field(
        default=True,
        description=(
            "Set false to recompute an already-saved chart (e.g. for "
            "display or comparison) without writing a new birth_charts "
            "row — Swiss Ephemeris recompute is deterministic, so this "
            "reproduces the exact same chart from its stored birth data. "
            "Requires chart_id. Divisional charts are likewise not "
            "persisted in this mode."
        ),
    )
    chart_id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "The existing saved chart this recompute belongs to. Required "
            "when persist=false; ignored when persist=true (a new/"
            "matching birth_charts row is resolved via get_or_create "
            "instead)."
        ),
    )
    force_new: bool = Field(
        default=False,
        description=(
            "When persist=true, get_or_create() normally reuses an "
            "existing birth_charts row that exactly matches this user's "
            "(birth_datetime_utc, latitude, longitude, ayanamsa, "
            "house_system) — two different people can legitimately share "
            "an exact birth moment and location (e.g. a coincidence, or "
            "twins at different precision). Set true to always insert a "
            "new row instead of reusing a match. Callers should check "
            "POST /workflow/check-existing first and let the user decide "
            "before setting this."
        ),
    )

    @model_validator(mode="after")
    def chart_id_required_when_not_persisting(self) -> "WorkflowAnalysisRequest":
        if not self.persist and self.chart_id is None:
            raise ValueError("chart_id is required when persist=false.")
        return self


# ── Duplicate check (confirm before persist) ─────────────────────────────────


class WorkflowDuplicateCheckRequest(BirthDataInput):
    """Same natural key BirthChartRepository.get_or_create() dedups on —
    check before submitting persist=true so the caller can ask the user
    to confirm rather than silently merging into someone else's chart."""


class WorkflowDuplicateCheckResponse(BaseModel):
    exists: bool
    chart_id: Optional[uuid.UUID] = None
    subject_name: Optional[str] = None
    saved_at: Optional[datetime] = None


# ── Bulk Import (CSV/JSON upload of birth data) ──────────────────────────────


class BulkImportRow(BirthDataInput):
    """One row of a bulk-import file — just enough to run through the same
    analysis pipeline as WorkflowAnalysisRequest, with saner client-side
    defaults (vargas skipped for speed, matching the recompute-for-display
    path elsewhere in this API)."""

    subject_name: str = "Unnamed"
    place_name: Optional[str] = None
    force_new: bool = Field(
        default=False,
        description="See WorkflowAnalysisRequest.force_new — applies per row.",
    )


class BulkImportRequest(BaseModel):
    rows: list[BulkImportRow] = Field(min_length=1, max_length=100)


class BulkImportRowResult(BaseModel):
    row_index: int
    subject_name: str
    success: bool
    chart_id: Optional[uuid.UUID] = None
    error: Optional[str] = None
    matched_existing: bool = Field(
        default=False,
        description=(
            "True when this row's birth data exactly matched an already-"
            "saved chart and force_new was not set, so the existing row "
            "was reused rather than a new one created. Review these — a "
            "match doesn't necessarily mean this is the same person."
        ),
    )


class BulkImportResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[BulkImportRowResult]


# ── New response pieces (no existing schema covered these engines) ───────────


class ShadbalaTotalResponse(BaseModel):
    """Per-planet Shadbala total, summed across Phase 1 + Phase 2 + Sthana Bala — same reduction FactBuilder uses for `shadbala.{planet}.total` facts."""

    planet: str
    total_rupas: float


class RuleResultResponse(BaseModel):
    """Response payload describing rule result data."""
    rule_id: str
    rule_name: str
    rule_category: str
    matched: bool
    matched_conditions: list[str]
    failed_conditions: list[str]
    explanation: str
    priority: int = 0
    evaluation_trace: list[str] = []
    derived_facts: dict[str, Any] = {}


class VerificationPairSummaryResponse(BaseModel):
    """Response payload describing verification pair summary data."""
    rule_id: str
    rule_name: str
    event_id: uuid.UUID
    event_title: str
    event_date: date
    alignment: str
    strength: str


class VerificationSummaryResponse(BaseModel):
    """
    Populated only if the chart already has recorded events (via
    POST /events) — verifying rule predictions against life events
    requires events to exist. `None` on the parent response (not this
    schema) signals "no events recorded yet," not an error.
    """

    total_events: int
    total_rules_evaluated: int
    total_pairs: int
    pairs: list[VerificationPairSummaryResponse]
    confidence_score: float = 0.0


class PlanetBenchmarkResponse(BaseModel):
    """Response payload describing planet benchmark data."""
    planet: str
    computed_longitude: float
    expected_longitude: float
    error_degrees: float
    within_tolerance: bool


class BenchmarkResponse(BaseModel):
    """
    Benchmark validation result against the GC-MASTER golden-reference
    dataset. Only populated when the computed chart matches a GC-MASTER
    reference by birth data. `status: "not_applicable"` when no match
    is found — this is not an error, simply a chart outside the
    reference dataset.
    """

    status: Literal["passed", "failed", "not_applicable"]
    reference_id: str = ""
    reference_name: str = ""
    chart_count: int = 0
    mean_error: float = 0.0
    max_error: float = 0.0
    tolerance: float = 0.5
    planets: list[PlanetBenchmarkResponse] = []
    detail: str = ""


# ── Top-level response ────────────────────────────────────────────────────────


class WorkflowAnalysisResponse(BaseModel):
    """Response payload describing workflow analysis data."""
    chart_id: uuid.UUID
    chart: D1ChartResponse
    vargas: Optional[AllVargaChartsResponse] = None
    dasha: DashaTreeResponse
    yogas: YogaEvaluationResponse
    shadbala: list[ShadbalaTotalResponse]
    ashtakavarga: AllAshtakavargaResponse
    transits: TransitResponse
    rule_results: list[RuleResultResponse]
    knowledge_citations: list[KnowledgeSearchResultResponse]
    verification: Optional[VerificationSummaryResponse] = Field(
        default=None,
        description="None if this chart has no recorded events yet — not an error.",
    )
    benchmark: BenchmarkResponse
    report: ChartReportResponse
    research_snapshot_id: Optional[uuid.UUID] = Field(
        default=None,
        description=(
            "Set only if the request supplied research_project_id — the "
            "id of the AstrologicalSnapshot captured into that project. "
            "None if no research_project_id was supplied."
        ),
    )


# ── Full Report (workflow pipeline + KP in one call) ─────────────────────────


class FullReportRequest(BirthDataInput):
    """
    Request body for POST /report/full — the complete astrology report.

    Extends BirthDataInput (the same birth-data contract as the other
    report endpoints) plus the pipeline options: which dasha system,
    whether to compute divisional charts / KP analysis, and the display
    title / subject name. The full report never persists a new chart —
    the pipeline runs with persist=false so a saved chart is not required.
    """

    title: str = "Complete Astrology Report"
    subject_name: str = "Unnamed"
    generated_by: Optional[str] = None
    dasha_system: DashaSystem = "vimshottari"
    transit_datetime_utc: Optional[datetime] = Field(
        default=None,
        description="Defaults to now (UTC) if omitted — the 'current transits' moment.",
    )
    include_vargas: bool = Field(
        default=True, description="Compute all 15 divisional charts. Set false to skip for speed."
    )
    include_kp: bool = Field(
        default=True, description="Include the KP analysis + evidence sections in the response."
    )


class FullReportResponse(WorkflowAnalysisResponse):
    """
    Response payload for POST /report/full.

    The complete workflow analysis (chart, vargas, dasha, yogas,
    shadbala, ashtakavarga, transits, rule results, knowledge citations,
    verification, benchmark, report) plus the KP analysis + evidence
    sections. chart_id is None because the full report runs the pipeline
    with persist=false (no birth_charts row is written).
    """

    chart_id: Optional[uuid.UUID] = None
    title: str = "Complete Astrology Report"
    subject_name: str = "Unnamed"
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the full report was generated.",
    )
    kp_analysis: Optional[KPAnalysisResponse] = Field(
        default=None,
        description="KP analysis + evidence, when include_kp was requested.",
    )
