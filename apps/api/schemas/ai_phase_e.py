"""
AstroOS — Phase E AI API Schemas

Pydantic request/response models for the Phase E AI Layer endpoints:
chart comparison, research assistant, hypothesis generation, and
enhanced QA.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]


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