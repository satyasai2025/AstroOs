"""
AstroOS — Tri-Lifespan (Ayurdaya) & Maraka Router
===================================================

Endpoints:
- POST /api/v1/lifespan/tri-ayurdaya  — Complete Pindayu, Nisargayu, Amshayu & Maraka assessment.
"""

from __future__ import annotations

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.lifespan import (
    LifespanRequest,
    MethodLifespanSchema,
    PlanetaryAyurContributionSchema,
    MarakaVulnerabilitySchema,
    TriLifespanResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.lifespan_engine import LifespanEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lifespan", tags=["Lifespan"])


def _get_lifespan_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> LifespanEngine:
    return LifespanEngine(wrapper)


@router.post(
    "/tri-ayurdaya",
    response_model=TriLifespanResponse,
    summary="Compute Tri-Lifespan (Pindayu, Nisargayu, Amshayu) and Maraka Vulnerability",
)
async def get_tri_lifespan(
    body: LifespanRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    engine: LifespanEngine = Depends(_get_lifespan_engine),
) -> TriLifespanResponse:
    try:
        chart = await asyncio.to_thread(
            wrapper.calculate,
            dt=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        result = await asyncio.to_thread(engine.calculate_tri_lifespan_synthesis, chart)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error calculating lifespan: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate classical lifespan synthesis.",
        )

    def _serialise_method(m) -> MethodLifespanSchema:
        return MethodLifespanSchema(
            method_name=m.method_name,
            planetary_contributions=[
                PlanetaryAyurContributionSchema(
                    planet=c.planet,
                    base_years=c.base_years,
                    shatrukshetra_reduction=c.shatrukshetra_reduction,
                    astangata_reduction=c.astangata_reduction,
                    chakrapata_reduction=c.chakrapata_reduction,
                    bharana_enhancement=c.bharana_enhancement,
                    net_years=c.net_years,
                )
                for c in m.planetary_contributions
            ],
            lagna_contribution=m.lagna_contribution,
            total_years=m.total_years,
            category=m.category,
        )

    return TriLifespanResponse(
        pindayu=_serialise_method(result.pindayu),
        amshayu=_serialise_method(result.amshayu),
        nisargayu=_serialise_method(result.nisargayu),
        mean_lifespan_years=result.mean_lifespan_years,
        consensus_category=result.consensus_category,
        maraka_assessment=MarakaVulnerabilitySchema(
            primary_maraka_lords=list(result.maraka_assessment.primary_maraka_lords),
            secondary_maraka_lords=list(result.maraka_assessment.secondary_maraka_lords),
            badhaka_lord=result.maraka_assessment.badhaka_lord,
            badhaka_house=result.maraka_assessment.badhaka_house,
            is_saturn_maraka_absorber=result.maraka_assessment.is_saturn_maraka_absorber,
            saturn_maraka_reason=result.maraka_assessment.saturn_maraka_reason,
            d30_afflicted_planets=list(result.maraka_assessment.d30_afflicted_planets),
            high_risk_dasha_lords=list(result.maraka_assessment.high_risk_dasha_lords),
            vulnerability_index=result.maraka_assessment.vulnerability_index,
        ),
        shastric_notes=list(result.shastric_notes),
    )
