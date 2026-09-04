"""
AstroOS — Medical Jyotish Empirical Research API Router
======================================================
Serves statistically validated medical pattern mining findings and evaluates
native chart disease vulnerability based on the 66,732-case research dataset.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.services.medical_research_service import MedicalResearchService

router = APIRouter(prefix="/api/v1/research/medical", tags=["Medical Jyotish Research"])


class NativeMedicalEvaluateRequest(BaseModel):
    lagna_rashi: str = Field(..., description="Ascendant / Lagna sign, e.g., 'Leo'")
    planet_positions: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Planetary positions dictionary mapping planet names to {rashi, house, ...}"
    )
    current_dasha_lord: Optional[str] = Field(None, description="Active Mahadasha lord")
    current_antardasha_lord: Optional[str] = Field(None, description="Active Antardasha lord")


@router.get("/patterns")
@router.get("-patterns")
def get_medical_patterns() -> Dict[str, Any]:
    """
    Returns empirical medical pattern mining findings, sample counts,
    lift ratios, and classical Shastric rules across disease categories.
    """
    try:
        return MedicalResearchService.get_empirical_medical_patterns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve medical patterns: {e}")


@router.post("/evaluate")
def evaluate_native_medical_vulnerability(req: NativeMedicalEvaluateRequest) -> Dict[str, Any]:
    """
    Evaluates native birth chart planetary coordinates against empirical
    medical vulnerability signatures, organ afflictions, and protective factors.
    """
    try:
        return MedicalResearchService.evaluate_native_medical_chart(
            planet_positions=req.planet_positions,
            lagna_rashi=req.lagna_rashi,
            current_dasha_lord=req.current_dasha_lord,
            current_antardasha_lord=req.current_antardasha_lord
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate medical vulnerabilities: {e}")
