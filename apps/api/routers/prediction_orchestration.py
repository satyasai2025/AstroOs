"""
AstroOS — Prediction Orchestration Router

Provides API endpoints for deterministic multi-factor event prediction:
  POST /api/v1/predictions/orchestrate
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
    ConsensusProfile,
    PredictionSynthesisResult,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.prediction_orchestrator import PredictionOrchestrator

router = APIRouter(prefix="/predictions", tags=["Prediction Intelligence"])


class PredictionWindowSchema(BaseModel):
    event_type: str
    start_date: str
    end_date: str
    peak_date: str
    peak_score: int
    promise_status: str
    primary_drivers: list[str]
    supporting_factors: list[str]
    opposing_factors: list[str]
    evidence_trace: list[str]
    resolution_level: str
    deterministic_hash: str


class PredictionOrchestrateRequest(BaseModel):
    objective: str = Field(..., description="Target life domain, e.g. 'career', 'marriage_timing', 'wealth'")
    target_start_date: date = Field(..., description="Start of temporal scan range (YYYY-MM-DD)")
    target_end_date: date = Field(..., description="End of temporal scan range (YYYY-MM-DD)")
    profile_id: Optional[str] = Field("parashari_standard_v1", description="Consensus profile ID")
    enable_micro_zoom: bool = True
    # For testing / direct payload
    birth_datetime_utc: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PredictionOrchestrateResponse(BaseModel):
    event_type: str
    target_start_date: str
    target_end_date: str
    consensus_profile_used: str
    candidate_windows: list[PredictionWindowSchema]
    total_slices_evaluated: int
    macro_slices_count: int
    refined_slices_count: int
    deterministic_signature: str
    summary: str


@router.post("/orchestrate", response_model=PredictionOrchestrateResponse)
async def orchestrate_predictions(
    body: PredictionOrchestrateRequest,
) -> PredictionOrchestrateResponse:
    """Run deterministic multi-factor event prediction across the adaptive temporal timeline."""
    profile = (
        EMPIRICAL_RESEARCH_PROFILE
        if body.profile_id == "empirical_research_v1"
        else PARASHARI_STANDARD_PROFILE
    )

    from apps.api.config import get_settings
    from apps.api.services.horoscope_engine import HoroscopeEngine

    settings = get_settings()
    wrapper = EphemerisWrapper(settings.EPHEMERIS_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)

    from datetime import datetime, timezone

    dt = datetime.fromisoformat(body.birth_datetime_utc) if body.birth_datetime_utc else datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)
    lat = body.latitude if body.latitude is not None else 28.6139
    lon = body.longitude if body.longitude is not None else 77.2090

    chart = horoscope_engine.generate_d1(dt, lat, lon, ayanamsa="lahiri")
    dasha_tree = dasha_engine.compute_vimshottari(dt, lat, lon, ayanamsa="lahiri")

    orchestrator = PredictionOrchestrator()
    result = orchestrator.predict_event_windows(
        chart=chart,
        dasha_tree=dasha_tree,
        objective=body.objective,
        target_start=body.target_start_date,
        target_end=body.target_end_date,
        profile=profile,
        enable_micro_zoom=body.enable_micro_zoom,
    )

    return PredictionOrchestrateResponse(
        event_type=result.event_type,
        target_start_date=result.target_start_date.isoformat(),
        target_end_date=result.target_end_date.isoformat(),
        consensus_profile_used=result.consensus_profile_used.name,
        candidate_windows=[
            PredictionWindowSchema(
                event_type=c.event_type,
                start_date=c.start_date.isoformat(),
                end_date=c.end_date.isoformat(),
                peak_date=c.peak_date.isoformat(),
                peak_score=c.peak_score,
                promise_status=c.promise_status.value,
                primary_drivers=list(c.primary_drivers),
                supporting_factors=list(c.supporting_factors),
                opposing_factors=list(c.opposing_factors),
                evidence_trace=list(c.evidence_trace),
                resolution_level=c.resolution_level.value,
                deterministic_hash=c.deterministic_hash,
            )
            for c in result.candidate_windows
        ],
        total_slices_evaluated=result.total_slices_evaluated,
        macro_slices_count=result.macro_slices_count,
        refined_slices_count=result.refined_slices_count,
        deterministic_signature=result.deterministic_signature,
        summary=result.summary,
    )