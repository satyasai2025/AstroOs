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
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.ashtakavarga import AllAshtakavargaResponse
from apps.api.schemas.dasha import DashaTreeResponse
from apps.api.schemas.divisional import AllVargaChartsResponse
from apps.api.schemas.horoscope import D1ChartResponse
from apps.api.schemas.knowledge import KnowledgeSearchResultResponse
from apps.api.schemas.report import ChartReportResponse
from apps.api.schemas.transit import TransitResponse
from apps.api.schemas.yoga import YogaEvaluationResponse

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]
DashaSystem = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


# ── Request ───────────────────────────────────────────────────────────────────


class WorkflowAnalysisRequest(BaseModel):
    """One birth-data submission drives the entire pipeline."""

    birth_datetime_utc: datetime = Field(
        description="UTC birth datetime (ISO-8601, must include timezone offset)."
    )
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"
    dasha_system: DashaSystem = "vimshottari"
    transit_datetime_utc: Optional[datetime] = Field(
        default=None, description="Defaults to now (UTC) if omitted — the 'current transits' moment."
    )
    include_vargas: bool = Field(
        default=True, description="Compute all 15 divisional charts. Set false to skip for speed."
    )
    subject_name: str = "Unnamed"
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

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware.")
        return v


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
