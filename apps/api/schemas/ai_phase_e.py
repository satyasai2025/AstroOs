"""
AstroOS — Phase E AI API Schemas

Pydantic request/response models for the Phase E AI Layer endpoints:
chart comparison, research assistant, hypothesis generation, and
enhanced QA.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


# ── Ashtakoota Compatibility ───────────────────────────────────────────────────

class KootaScoreResponse(BaseModel):
    """Response payload for a single Koota score."""
    name: str
    max_score: float
    obtained_score: float
    status: str  # Excellent, Good, Average, Poor
    description: str


class DoshaResultResponse(BaseModel):
    """Response payload for a Dosha check result."""
    name: str
    has_dosha: bool
    severity: str  # None, Partial, Severe
    description: str


class AshtakootaCompatibilityRequest(BaseModel):
    """Request payload for Ashtakoota compatibility analysis."""
    # Person A data
    birth_datetime_utc_a: datetime = Field(
        description="UTC birth datetime for Person A (ISO-8601, must include timezone offset)."
    )
    latitude_a: float = Field(ge=-90.0, le=90.0)
    longitude_a: float = Field(ge=-180.0, le=180.0)
    subject_name_a: str = Field(default="Person A", max_length=100)

    # Person B data
    birth_datetime_utc_b: datetime = Field(
        description="UTC birth datetime for Person B (ISO-8601, must include timezone offset)."
    )
    latitude_b: float = Field(ge=-90.0, le=90.0)
    longitude_b: float = Field(ge=-180.0, le=180.0)
    subject_name_b: str = Field(default="Person B", max_length=100)

    # Chart settings
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"


class AshtakootaCompatibilityResponse(BaseModel):
    """Response payload for Ashtakoota compatibility analysis."""
    total_score: float
    max_total_score: float = 36.0
    compatibility_percentage: float
    verdict: str  # Excellent Match, Good Match, Average Match, Low Compatibility
    kootas: list[KootaScoreResponse]
    doshas: list[DoshaResultResponse]
    radar_values: dict[str, float]
    strengths: list[str]
    challenges: list[str]
    recommendations: list[str]
    # Subject names for display
    subject_name_a: str
    subject_name_b: str


# ── Best Bet 58-Point Compatibility ────────────────────────────────────────────

class BestBetSubFactorResponse(BaseModel):
    """Single sub-factor in Best Bet scoring."""
    name: str
    score: float
    max: float
    description: str


class BestBetCompatibilityRequest(BaseModel):
    """Request payload for Best Bet 58-point compatibility analysis."""
    # Person A data
    birth_datetime_utc_a: datetime = Field(
        description="UTC birth datetime for Person A (ISO-8601, must include timezone offset)."
    )
    latitude_a: float = Field(ge=-90.0, le=90.0)
    longitude_a: float = Field(ge=-180.0, le=180.0)
    subject_name_a: str = Field(default="Person A", max_length=100)

    # Person B data
    birth_datetime_utc_b: datetime = Field(
        description="UTC birth datetime for Person B (ISO-8601, must include timezone offset)."
    )
    latitude_b: float = Field(ge=-90.0, le=90.0)
    longitude_b: float = Field(ge=-180.0, le=180.0)
    subject_name_b: str = Field(default="Person B", max_length=100)

    # Chart settings
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"


class BestBetCompatibilityResponse(BaseModel):
    """Response payload for Best Bet 58-point compatibility analysis."""
    subject_name_a: str
    subject_name_b: str
    total_score: float
    max_score: float = 58.0
    percentage: float
    verdict: str  # Excellent Match, Good Match, Average Match, Poor Match
    status: str  # Excellent, Good, Average, Poor

    # Group scores
    practical_score: float
    practical_max: float = 36.0
    karmic_score: float
    karmic_max: float = 12.0
    future_score: float
    future_max: float = 10.0

    # Detailed breakdown
    spiritual_score: float
    spiritual_max: float = 12.0
    psychological_score: float
    psychological_max: float = 12.0
    physical_score: float
    physical_max: float = 12.0
    mars_dosha_score: float
    mars_dosha_max: float = 6.0
    karmic_pattern_score: float
    karmic_pattern_max: float = 6.0
    dasha_score: float
    dasha_max: float = 5.0
    mutual_planets_score: float
    mutual_planets_max: float = 5.0

    # Sub-factors
    sub_factors: list[BestBetSubFactorResponse]
    strengths: list[str]
    challenges: list[str]
    recommendations: list[str]


# ── Marriage Timing Transit Scanner (Jupiter / Saturn) ─────────────────────────

MarriageTimingStatus = Literal["probable", "delayed", "not_indicated"]


class MarriageTimingRequest(BaseModel):
    """Request payload for the Jupiter/Saturn marriage-window scan."""
    birth_datetime_utc: datetime = Field(
        description="UTC birth datetime (ISO-8601, must include timezone offset)."
    )
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    subject_name: str = Field(default="", max_length=100)

    # Scanned as ages rather than calendar years so the window travels with
    # the subject's birth date. Capped at 120 to bound the response size.
    scan_start_age: int = Field(default=20, ge=0, le=120)
    scan_end_age: int = Field(default=45, ge=0, le=120)

    # Chart settings
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"

    @model_validator(mode="after")
    def _check_age_range(self) -> "MarriageTimingRequest":
        if self.scan_end_age < self.scan_start_age:
            raise ValueError("scan_end_age must not be earlier than scan_start_age")
        return self


class TransitScanYearResponse(BaseModel):
    """One scanned year of the Jupiter/Saturn marriage-window scan."""
    year: int
    age_at_year: float
    julian_day: float
    jupiter_sidereal: float
    jupiter_rashi: str
    saturn_sidereal: float
    saturn_rashi: str
    status: MarriageTimingStatus
    aspect_details: list[str]
    saturn_obstruction_details: list[str]


class MarriageTimingResponse(BaseModel):
    """Response payload for the Jupiter/Saturn marriage-window scan."""
    subject_name: str
    birth_datetime_utc: datetime
    scan_start_age: int
    scan_end_age: int
    natal_venus_rashi: str
    natal_venus_longitude: float
    natal_seventh_cusp_rashi: str
    total_years_scanned: int
    probable_windows: int
    delayed_windows: int
    scan_results: list[TransitScanYearResponse]


# ── Chart Comparison ──────────────────────────────────────────────────────────

class ComparisonDimensionResponse(BaseModel):
    """Response payload describing comparison dimension data."""
    dimension: str
    chart_a_value: str
    chart_b_value: str
    similarity: float
    significance: str
    commentary: str = ""


class ChartComparisonResponse(BaseModel):
    """Response payload describing chart comparison data."""
    summary: str
    overall_similarity: float
    key_differences: list[ComparisonDimensionResponse] = []
    key_similarities: list[ComparisonDimensionResponse] = []
    compatibility_notes: str = ""
    relationship_potential: str = ""
    timing_synergies: str = ""


class ChartComparisonRequest(BaseModel):
    """Request payload for chart comparison operations."""
    birth_datetime_utc_a: datetime = Field(
        description="UTC birth datetime for Chart A (ISO-8601, must include timezone offset)."
    )
    latitude_a: float = Field(ge=-90.0, le=90.0)
    longitude_a: float = Field(ge=-180.0, le=180.0)
    subject_name_a: str = Field(default="Person A", max_length=100)

    birth_datetime_utc_b: datetime = Field(
        description="UTC birth datetime for Chart B (ISO-8601, must include timezone offset)."
    )
    latitude_b: float = Field(ge=-90.0, le=90.0)
    longitude_b: float = Field(ge=-180.0, le=180.0)
    subject_name_b: str = Field(default="Person B", max_length=100)

    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"
    style: str = "concise"


# ── Research Assistant ────────────────────────────────────────────────────────

class ResearchEvidenceResponse(BaseModel):
    """Response payload describing research evidence data."""
    source: str
    reference: str
    text: str
    relevance: float
    entity_type: str
    tradition: Optional[str] = None


class ResearchAnswerResponse(BaseModel):
    """Response payload describing research answer data."""
    question: str
    summary: str
    body: str
    evidence: list[ResearchEvidenceResponse] = []
    related_conflicts: list[str] = []
    confidence: str
    unanswered_aspects: list[str] = []


class ResearchQueryRequest(BaseModel):
    """Request payload for research query operations."""
    question: str = Field(min_length=1, max_length=1000)
    domain_filter: Optional[str] = Field(
        default=None,
        description="Optional domain filter: graha, bhava, yoga, dasha, aspect, dignity, transit, remedy, karakatva, conflict",
    )
    tradition_filter: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=50)


class AvailableDomainResponse(BaseModel):
    """Response payload describing available domain data."""
    id: str
    name: str
    description: str


class AvailableDomainsResponse(BaseModel):
    """Response payload describing available domains data."""
    domains: list[AvailableDomainResponse]


# ── Hypothesis Generation ─────────────────────────────────────────────────────

class HypothesisTemplateResponse(BaseModel):
    """Response payload describing hypothesis template data."""
    hypothesis_id: str
    title: str
    description: str
    domain: str
    conditions: list[str] = []
    expected_outcome: str
    test_method: str
    classical_references: list[str] = []
    priority: int


class GeneratedHypothesisResponse(BaseModel):
    """Response payload describing generated hypothesis data."""
    hypothesis_id: str
    title: str
    description: str
    domain: str
    supporting_evidence: list[str] = []
    contradicting_evidence: list[str] = []
    testable_prediction: str
    suggested_dataset: str
    priority: int
    related_rules: list[str] = []
    related_yogas: list[str] = []
    confidence: str
    graph_grounded: bool = False


class HypothesisListResponse(BaseModel):
    """Response payload describing hypothesis list data."""
    hypotheses: list[GeneratedHypothesisResponse]
    total: int


class HypothesisTemplatesResponse(BaseModel):
    """Response payload describing hypothesis templates data."""
    templates: list[HypothesisTemplateResponse]
    total: int


class HypothesisGenerateRequest(BaseModel):
    """Request payload for hypothesis generate operations."""
    birth_datetime_utc: datetime = Field(
        description="UTC birth datetime (ISO-8601, must include timezone offset)."
    )
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"
    domain_filter: Optional[str] = None
    max_hypotheses: int = Field(default=5, ge=1, le=20)


# ── Enhanced QA ───────────────────────────────────────────────────────────────

class EnhancedQuestionRequest(BaseModel):
    """Request payload for enhanced question operations."""
    birth_datetime_utc: datetime = Field(
        description="UTC birth datetime (ISO-8601, must include timezone offset)."
    )
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"
    question: str = Field(min_length=1, max_length=1000)
    include_yogas: bool = Field(default=True, description="Include yoga data in context.")
    include_dashas: bool = Field(default=True, description="Include dasha data in context.")
    include_transits: bool = Field(default=True, description="Include transit data in context.")
    include_strengths: bool = Field(default=True, description="Include strength data in context.")


# ── Verification Report ────────────────────────────────────────────────────────


class VerificationReportRequest(BaseModel):
    """Request payload to generate a verification report."""
    chart_id: str = Field(description="UUID of the chart to generate the report for.")
    event_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional list of specific event UUIDs to include in the report.",
    )


class VerificationReportResponse(BaseModel):
    """Response payload for a verification report."""
    response_type: str = "verification_report"
    title: str
    summary: str
    body: str
    sources: list[str] = []
    confidence: str = "medium"
    version: str = "1.0"


# ── Research Insight ────────────────────────────────────────────────────────────


class ResearchInsightRequest(BaseModel):
    """Request payload to generate research insights."""
    experiment_ids: list[str] = Field(
        description="List of experiment UUIDs to generate insights from."
    )


class ResearchInsightResponse(BaseModel):
    """Response payload for a research insight."""
    response_type: str = "research_insight"
    title: str
    summary: str
    body: str
    sources: list[str] = []
    confidence: str = "medium"
    version: str = "1.0"


# ── Recommendation ──────────────────────────────────────────────────────────────


class RecommendationRequest(BaseModel):
    """Request payload to generate recommendations."""
    chart_id: str = Field(description="UUID of the chart to generate recommendations for.")


class RecommendationResponse(BaseModel):
    """Response payload for recommendations."""
    response_type: str = "recommendation"
    title: str
    summary: str
    body: str
    recommendations: list[str] = []
    sources: list[str] = []
    confidence: str = "medium"
    version: str = "1.0"
