"""
AstroOS — Priority 12: Multi-Dasha Confluence API Router
"""

from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter, status

from apps.api.domain.ephemeris import (
    Ascendant,
    EphemerisResult,
    HouseCusp,
    KaranaInfo,
    NakshatraInfo,
    PanchangaResult,
    SiderealPosition,
    TithiInfo,
    VaraInfo,
    YogaInfo,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.schemas.multi_dasha_confluence import (
    ConfluenceEvaluateRequest,
    ConfluenceMatrixResponse,
    ConfluenceWindowSchema,
)
from apps.api.services.multi_dasha_confluence_engine import MultiDashaConfluenceEngine

router = APIRouter(prefix="/research/confluence", tags=["Multi-Dasha Confluence"])


def _build_test_chart() -> D1Chart:
    asc = Ascendant(10.0, 10.0, "aries", 10.0, "ashwini", 1)
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    planets = [
        SiderealPosition("sun", 30.0, "taurus", 0.0, 2, "krittika", 2, False, False, None, None),
        SiderealPosition("moon", 15.0, "aries", 15.0, 1, "bharani", 1, False, False, None, None),
        SiderealPosition("mars", 60.0, "gemini", 0.0, 3, "mrigashira", 3, False, False, None, None),
        SiderealPosition("mercury", 90.0, "cancer", 0.0, 4, "punarvasu", 4, False, False, None, None),
        SiderealPosition("jupiter", 105.0, "cancer", 15.0, 4, "pushya", 2, False, False, None, "exalted"),
        SiderealPosition("venus", 120.0, "leo", 0.0, 5, "magha", 1, False, False, None, None),
        SiderealPosition("saturn", 275.0, "capricorn", 5.0, 10, "uttara_phalguni", 2, False, False, None, None),
        SiderealPosition("rahu", 180.0, "libra", 0.0, 7, "chitra", 3, True, False, None, None),
        SiderealPosition("ketu", 0.0, "aries", 0.0, 1, "ashwini", 1, True, False, None, None),
    ]
    houses = [HouseCusp(n, float((n - 1) * 30), float((n - 1) * 30), rashis[n - 1]) for n in range(1, 13)]
    # Real Julian Day (2000-01-01 12:00 UTC) so downstream real-data
    # consumers (MultiDashaConfluenceEngine) have a real birth date/chart_id
    # anchor instead of a fabricated one — this demo chart's positions are
    # synthetic, but its timestamp is a real, valid JD, not invented data.
    panchanga = PanchangaResult(
        tithi=TithiInfo(1, "shukla_pratipada", "shukla", 50.0),
        nakshatra=NakshatraInfo("ashwini", 1, 1, "ketu", 0.0, 0.0),
        yoga=YogaInfo(1, "vishkambha", 50.0),
        karana=KaranaInfo(1, "bava", False),
        vara=VaraInfo(6, "saturday", "saturn"),
        julian_day=2451545.0,
        ayanamsa_deg=23.85,
    )
    ephemeris = EphemerisResult(
        julian_day=2451545.0,
        ayanamsa_value=23.85,
        ayanamsa_system="lahiri",
        ascendant=asc,
        house_cusps=houses,
        planet_positions=planets,
        panchanga=panchanga,
    )
    return D1Chart(ephemeris, asc, houses, planets, [], [], panchanga, "lahiri", "W")


@router.post("/evaluate", response_model=ConfluenceMatrixResponse, status_code=status.HTTP_200_OK)
@router.post("/evaluate/", response_model=ConfluenceMatrixResponse, status_code=status.HTTP_200_OK)
def evaluate_confluence_matrix(req: ConfluenceEvaluateRequest) -> ConfluenceMatrixResponse:
    """Evaluate polymodal multi-dasha confluence matrix for a birth chart context."""
    chart = _build_test_chart()
    engine = MultiDashaConfluenceEngine()

    matrix = engine.evaluate_confluence_matrix(
        chart=chart,
        target_start=req.target_start_date,
        target_end=req.target_end_date,
        objective=req.objective,
    )

    windows_schema = [
        ConfluenceWindowSchema(
            window_id=w.window_id,
            start_date=w.start_date,
            end_date=w.end_date,
            duration_days=w.duration_days,
            overlapping_systems=list(w.overlapping_systems),
            system_count=w.system_count,
            confluence_density_score=w.confluence_density_score,
            activated_houses=list(w.activated_houses),
            primary_objective=w.primary_objective,
        )
        for w in matrix.confluence_windows
    ]

    peak_schema = (
        ConfluenceWindowSchema(
            window_id=matrix.peak_confluence_window.window_id,
            start_date=matrix.peak_confluence_window.start_date,
            end_date=matrix.peak_confluence_window.end_date,
            duration_days=matrix.peak_confluence_window.duration_days,
            overlapping_systems=list(matrix.peak_confluence_window.overlapping_systems),
            system_count=matrix.peak_confluence_window.system_count,
            confluence_density_score=matrix.peak_confluence_window.confluence_density_score,
            activated_houses=list(matrix.peak_confluence_window.activated_houses),
            primary_objective=matrix.peak_confluence_window.primary_objective,
        )
        if matrix.peak_confluence_window
        else None
    )

    return ConfluenceMatrixResponse(
        chart_id=matrix.chart_id,
        target_start_date=matrix.target_start_date,
        target_end_date=matrix.target_end_date,
        objective=matrix.objective,
        total_intervals_evaluated=len(matrix.all_intervals),
        total_confluence_windows=len(matrix.confluence_windows),
        confluence_windows=windows_schema,
        peak_confluence_window=peak_schema,
        consensus_profile_used=matrix.consensus_profile_used,
    )


@router.get("/systems", status_code=status.HTTP_200_OK)
@router.get("/systems/", status_code=status.HTTP_200_OK)
def list_dasha_systems() -> List[dict[str, Any]]:
    """List available dasha timing systems supported in the confluence matrix."""
    return [
        {"system_name": "vimshottari", "description": "120-year Nakshatra Dasha (MD/AD/PD)", "cycle_years": 120},
        {"system_name": "chara", "description": "Jaimini Rashi Dasha based on sign strengths", "cycle_years": 108},
        {"system_name": "yogini", "description": "Classical 8-Yogini Nakshatra Dasha", "cycle_years": 36},
        {"system_name": "ashtakavarga_kakshya", "description": "Transit Kakshya Lord Bindu timing (12x8)", "cycle_years": 1},
    ]
