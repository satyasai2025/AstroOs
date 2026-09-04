"""
AstroOS — Governed RAG & AI Copilot Schemas (Phase 12)
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ShastraCitation(BaseModel):
    source: str = Field(..., description="Classical Shastra name (e.g. Brihat Parashara Hora Shastra)")
    chapter: int = Field(..., description="Chapter number")
    verse: str = Field(..., description="Verse or Sloka number")
    sanskrit_sloka: Optional[str] = None
    translation: str = Field(..., description="Authoritative translation")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class GovernedRAGRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Astrological or research question")
    domain_filter: Optional[str] = Field(default="all", description="E.g. parashari, jaimini, kp, remedies")


class GovernedRAGResponse(BaseModel):
    query: str
    plan_tier: str
    ai_backend_used: str
    interpretation: str
    provenance_citations: List[ShastraCitation]
    technique_isolation_valid: bool = True
    grounding_score: float = 0.98
