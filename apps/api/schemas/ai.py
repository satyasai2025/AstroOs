"""
AstroOS — AI API Schemas (Module 24 — HTTP surface)

Pydantic request/response models for the AI Engine's template-based
narration endpoints. AIEngine is never a live LLM call — see
ai_engine.py's module docstring ("No external LLM, no network calls").

Scope note: routers/ai.py wires chart_summary, yoga_explanation,
dasha_interpretation, transit_reading, and qa — the four generators
computable directly from birth data. verification_report,
research_insight, and recommendation are wired separately in
routers/ai_phase_e.py (Task #13) — see that module's docstring.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal, Optional


from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.common import BirthDataInput

DashaSystem = Literal["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"]


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


class KnowledgeQuestionRequest(BaseModel):
    """Request payload for a general astrology knowledge question — no
    birth data, since this answers from AstroOS's classical-text
    knowledge base (RAG), not from a specific chart. See
    QuestionRequest above for chart-specific Q&A."""
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


class AISBCAnalysisRequest(BaseModel):
    reference_nakshatra: str = Field(default="mrigashira", description="Janma Nakshatra token (e.g. 'mrigashira' or 'uttara_phalguni')")
    transit_date: Optional[datetime] = Field(default=None, description="Active transit datetime in UTC")
    event_type: Literal["market", "life_events", "muhurta", "general"] = Field(
        default="general",
        description="Event category: 'market', 'life_events', 'muhurta', or 'general'"
    )
    malefic_vedhas: list[dict[str, Any]] = Field(default_factory=list, description="Current malefic afflictions")
    benefic_vedhas: list[dict[str, Any]] = Field(default_factory=list, description="Current benefic shields")
    active_sangyas: list[dict[str, Any]] = Field(default_factory=list, description="Status of the 10 Sangyas")
    custom_context: Optional[str] = Field(default=None, description="Optional custom user context")

    @field_validator("transit_date")
    @classmethod
    def _require_tz_sbc(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AISBCSangyaBreakdownItem(BaseModel):
    sangya_key: str
    sangya_name: str
    nakshatra_name: str
    status: str
    domain: str
    grahas_involved: list[str] = Field(default_factory=list)
    interpretation: str


class AISBCWarningItem(BaseModel):
    headline: str
    what_not_to_do: str
    affected_area: str
    severity: str = "warning"  # "critical" | "warning" | "caution"


class AISBCSafeZoneItem(BaseModel):
    area_name: str
    plain_title: str
    description: str
    benefit: str


class AISBCPracticalStep(BaseModel):
    action: str
    why: str
    timing_tip: str


class AISBCAnalysisResponse(BaseModel):
    event_type: str
    title: str
    verdict: str = "Cautious / Wait & Watch"
    verdict_badge: str = "caution"  # "high_risk" | "caution" | "favorable" | "auspicious"
    the_story: str = ""
    executive_summary: str = ""
    risk_level: str = "moderate"
    quick_chips: list[str] = Field(default_factory=list)
    major_warnings: list[AISBCWarningItem] = Field(default_factory=list)
    safe_zones: list[AISBCSafeZoneItem] = Field(default_factory=list)
    practical_steps: list[AISBCPracticalStep] = Field(default_factory=list)
    sangya_breakdown: list[AISBCSangyaBreakdownItem] = Field(default_factory=list)
    predictions: list[str] = Field(default_factory=list)
    protective_shields: list[str] = Field(default_factory=list)
    actionable_remedies: list[str] = Field(default_factory=list)
    markdown_report: str = ""
    confidence: float = 0.95
    version: str = "2.1.0"


