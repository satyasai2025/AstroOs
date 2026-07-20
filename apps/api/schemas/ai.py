"""
AstroOS — AI API Schemas (Module 24 — HTTP surface)

Pydantic request/response models for the AI Engine's template-based
narration endpoints. AIEngine is never a live LLM call — see
ai_engine.py's module docstring ("No external LLM, no network calls").

Scope note: this router wires chart_summary, yoga_explanation,
dasha_interpretation, transit_reading, and qa — the four generators
computable directly from birth data. verification_report,
research_insight, and recommendation all require the same
Research/Statistics/Timeline/Verification placeholder reconstruction as
routers/report.py and are left for a follow-up rather than duplicating
that machinery a third time (see routers/report.py's module docstring
for the pattern if/when that follow-up happens).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

AyanamsaCode = Literal["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]
HouseSystemCode = Literal["W", "P", "K", "E"]
DashaSystem = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


class BirthDataInput(BaseModel):
    """Model representing birth data input data."""
    birth_datetime_utc: datetime = Field(
        description="UTC birth datetime (ISO-8601, must include timezone offset)."
    )
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    ayanamsa: AyanamsaCode = "lahiri"
    house_system: HouseSystemCode = "W"

    @field_validator("birth_datetime_utc")
    @classmethod
    def must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("birth_datetime_utc must be timezone-aware.")
        return v


class ChartSummaryRequest(BirthDataInput):
    """Request payload for chart summary operations."""
    style: str = "concise"


class YogaExplanationRequest(BirthDataInput):
    """Request payload for yoga explanation operations."""
    pass


class DashaInterpretationRequest(BirthDataInput):
    """Request payload for dasha interpretation operations."""
    system: DashaSystem = "vimshottari"
    target_date: Optional[date] = Field(
        default=None, description="Defaults to today if omitted."
    )


class TransitReadingRequest(BirthDataInput):
    """Request payload for transit reading operations."""
    transit_datetime_utc: Optional[datetime] = Field(
        default=None, description="Defaults to now (UTC) if omitted."
    )


class QuestionRequest(BirthDataInput):
    """Request payload for question operations."""
    question: str = Field(min_length=1)


class ExplainRuleRequest(BirthDataInput):
    """Rule ID is passed as path parameter, not body field."""
    pass


# ── Response ──────────────────────────────────────────────────────────────────


class CitationResponse(BaseModel):
    """Response payload describing citation data."""
    source: str
    reference: str
    text: str
    relevance: float = 0.0


class AIResponseSchema(BaseModel):
    """Schema representing ai response data."""
    response_type: str
    title: str
    summary: str
    body: str
    citations: list[CitationResponse] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: str
    version: str
