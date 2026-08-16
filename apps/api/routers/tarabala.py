"""
AstroOS — Navatara / Tarabala Router

Endpoints
---------
POST /api/v1/tarabala/report — Natal + transit + lordship Tarabala,
                                yearly Tara cycle, and best-stars
                                intersection for a given Janma
                                Nakshatra.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.tarabala import (
    LordshipTaraEntryResponse,
    PlanetTaraResponse,
    SpecialPointEntryResponse,
    TarabalaReportRequest,
    TarabalaReportResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.tarabala_report_service import TarabalaReport, TarabalaReportService

router = APIRouter(prefix="/tarabala", tags=["Navatara / Tarabala"])


def _get_tarabala_service(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TarabalaReportService:
    return TarabalaReportService(wrapper)


def _serialise(report: TarabalaReport) -> TarabalaReportResponse:
    return TarabalaReportResponse(
        janma_nakshatra=report.janma_nakshatra,
        lagna_nakshatra=report.lagna_nakshatra,
        moment_utc=report.moment_utc,
        natal_tarabala=[
            PlanetTaraResponse(planet=p.planet, nakshatra=p.nakshatra, position=p.position, name=p.name, is_favorable=p.is_favorable)
            for p in report.natal_tarabala
        ],
        transit_tarabala=[
            PlanetTaraResponse(planet=p.planet, nakshatra=p.nakshatra, position=p.position, name=p.name, is_favorable=p.is_favorable)
            for p in report.transit_tarabala
        ],
        lordship_tarabala=[
            LordshipTaraEntryResponse(dasha_level=l.dasha_level, lord=l.lord, position_name=l.position_name, is_favorable=l.is_favorable)
            for l in report.lordship_tarabala
        ],
        favorable_level_count=report.favorable_level_count,
        total_active_levels=report.total_active_levels,
        all_levels_favorable=report.all_levels_favorable,
        yearly_age=report.yearly_age,
        yearly_position=report.yearly_position,
        yearly_name=report.yearly_name,
        best_stars=report.best_stars,
        special_points=[
            SpecialPointEntryResponse(name=sp.name, from_moon=sp.from_moon, from_lagna=sp.from_lagna)
            for sp in report.special_points
        ],
    )


@router.post("/report", response_model=TarabalaReportResponse)
async def get_tarabala_report(
    request: TarabalaReportRequest,
    service: TarabalaReportService = Depends(_get_tarabala_service),
) -> TarabalaReportResponse:
    moment_utc = request.moment_utc or datetime.now(timezone.utc)
    report = service.build_report(
        janma_nakshatra=request.janma_nakshatra,
        birth_datetime_utc=request.birth_datetime_utc,
        moment_utc=moment_utc,
        lagna_nakshatra=request.lagna_nakshatra,
        dasha_chain=request.dasha_chain,
    )
    return _serialise(report)
