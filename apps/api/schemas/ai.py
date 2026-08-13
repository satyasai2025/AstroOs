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

from datetime import date, datetime
from typing import Literal, Optional

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
