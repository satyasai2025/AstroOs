"""
AstroOS — Professional Archetype Empirical Research API Router
==============================================================
Serves statistically validated archetype pattern mining findings and evaluates
native chart resonance with vocational archetypes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.services.archetype_research_service import ArchetypeResearchService

router = APIRouter(prefix="/api/v1/research/archetypes", tags=["Professional Archetype Research"])


class NativeArchetypeEvaluateRequest(BaseModel):
    lagna_rashi: str = Field(..., description="Ascendant / Lagna sign, e.g., 'Aries'")
    planet_positions: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Planetary positions dictionary mapping planet names to {rashi, house, ...}"
    )


@router.get("/patterns")
def get_archetype_patterns() -> Dict[str, Any]:
    """
    Returns empirical archetype pattern mining discoveries across politicians,
    actors, sports champions, business titans, and spiritual saints.
    """
    try:
        return ArchetypeResearchService.get_empirical_archetype_patterns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve archetype patterns: {e}")


@router.post("/evaluate")
def evaluate_native_archetype_resonance(req: NativeArchetypeEvaluateRequest) -> Dict[str, Any]:
    """
    Evaluates native birth chart planetary coordinates against 5 empirical
    vocational archetypes, returning resonance scores and planetary proofs.
    """
    try:
        return ArchetypeResearchService.evaluate_native_archetype(
            planet_positions=req.planet_positions,
            lagna_rashi=req.lagna_rashi
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate archetype resonance: {e}")
