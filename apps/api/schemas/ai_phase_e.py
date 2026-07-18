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
    dimension: str
    chart_a_value: str
    chart_b_value: str
    similarity: float
    significance: str
    commentary: str = ""


class ChartComparisonResponse(BaseModel):
    summary: str
    overall_similarity: float
    key_differences: list[ComparisonDimensionResponse] = []
    key_similarities: list[ComparisonDimensionResponse] = []
    compatibility_notes: str = ""
    relationship_potential: str = ""
    timing_synergies: str = ""


class ChartComparisonRequest(BaseModel):
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
    source: str
    reference: str
    text: str
    relevance: float
    entity_type: str
    tradition: Optional[str] = None


class ResearchAnswerResponse(BaseModel):
    question: str
    summary: str
    body: str
    evidence: list[ResearchEvidenceResponse] = []
    related_conflicts: list[str] = []
    confidence: str
    unanswered_aspects: list[str] = []


class ResearchQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    domain_filter: Optional[str] = Field(
        default=None,
        description="Optional domain filter: graha, bhava, yoga, dasha, aspect, dignity, transit, remedy, karakatva, conflict",
    )
    tradition_filter: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=50)


class AvailableDomainResponse(BaseModel):
    id: str
    name: str
    description: str


class AvailableDomainsResponse(BaseModel):
    domains: list[AvailableDomainResponse]


# ── Hypothesis Generation ─────────────────────────────────────────────────────

class HypothesisTemplateResponse(BaseModel):
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


class HypothesisListResponse(BaseModel):
    hypotheses: list[GeneratedHypothesisResponse]
    total: int


class HypothesisTemplatesResponse(BaseModel):
    templates: list[HypothesisTemplateResponse]
    total: int


class HypothesisGenerateRequest(BaseModel):
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