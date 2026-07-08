"""
AstroOS — Divisional Chart Router (Task 5)

Endpoints
---------
POST /api/v1/divisional/{varga}   — Compute a single varga chart (D2 … D60)
POST /api/v1/divisional/all       — Compute all 15 varga charts in one call

No business logic lives here — all computation is delegated to DivisionalEngine.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, status

from apps.api.dependencies import get_ephemeris_service
from apps.api.domain.divisional import VargaChart
from apps.api.schemas.divisional import (
    AllVargaChartsResponse,
    VargaAscendantResponse,
    VargaChartRequest,
    VargaChartResponse,
    VargaPlanetResponse,
)
from apps.api.services.divisional_engine import SUPPORTED_VARGAS, DivisionalEngine
from apps.api.services.ephemeris_service import EphemerisService
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/divisional", tags=["Divisional Charts"])

_VALID_VARGAS = sorted(SUPPORTED_VARGAS)


# ── DI helper ────────────────────────────────────────────────────────────────


def _get_divisional_engine(
    ephe_svc: EphemerisService = Depends(get_ephemeris_service),
) -> DivisionalEngine:
    """
    Build a DivisionalEngine by reusing the EphemerisWrapper pattern from the
    horoscope router — creates a wrapper from settings sharing the same swe path.
    """
    from apps.api.config import get_settings
    settings = get_settings()
    wrapper = EphemerisWrapper(
        ephemeris_path=settings.EPHEMERIS_PATH,
        ayanamsa="lahiri",
    )
    return DivisionalEngine(wrapper)


# ── Serialisation helper ──────────────────────────────────────────────────────


def _serialise_chart(chart: VargaChart) -> VargaChartResponse:
    return VargaChartResponse(
        varga=chart.varga,
        divisor=chart.divisor,
        ascendant=VargaAscendantResponse(
            d1_sidereal_longitude=chart.ascendant.d1_sidereal_longitude,
            d1_rashi=chart.ascendant.d1_rashi,
            d1_rashi_degree=round(chart.ascendant.d1_rashi_degree, 6),
            varga_rashi=chart.ascendant.varga_rashi,
            varga_rashi_degree=round(chart.ascendant.varga_rashi_degree, 6),
        ),
        planet_positions=[
            VargaPlanetResponse(
                planet=p.planet,
                d1_sidereal_longitude=p.d1_sidereal_longitude,
                d1_rashi=p.d1_rashi,
                d1_rashi_degree=p.d1_rashi_degree,
                varga_rashi=p.varga_rashi,
                varga_rashi_degree=p.varga_rashi_degree,
                varga_house_number=p.varga_house_number,
                nakshatra=p.nakshatra,
                pada=p.pada,
                is_retrograde=p.is_retrograde,
                is_combust=p.is_combust,
            )
            for p in chart.planet_positions
        ],
        ayanamsa_system=chart.ayanamsa_system,
        julian_day=chart.julian_day,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/all",
    response_model=AllVargaChartsResponse,
    summary="Compute all 15 divisional charts",
    description=(
        "Computes D2 through D60 in a single ephemeris call. "
        "Returns a map of varga code → chart."
    ),
)
async def compute_all_vargas(
    body: VargaChartRequest,
    engine: DivisionalEngine = Depends(_get_divisional_engine),
) -> AllVargaChartsResponse:
    try:
        all_charts = engine.compute_all(
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing all vargas: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute divisional charts.",
        )

    serialised = {code: _serialise_chart(chart) for code, chart in all_charts.items()}
    # Pick any chart for shared metadata
    sample = next(iter(all_charts.values()))
    return AllVargaChartsResponse(
        charts=serialised,
        julian_day=sample.julian_day,
        ayanamsa_system=sample.ayanamsa_system,
    )


@router.post(
    "/{varga}",
    response_model=VargaChartResponse,
    summary="Compute a single divisional chart",
    description=(
        "Compute one of the 15 supported varga charts: "
        + ", ".join(_VALID_VARGAS)
        + "."
    ),
)
async def compute_varga(
    body: VargaChartRequest,
    engine: DivisionalEngine = Depends(_get_divisional_engine),
    varga: str = Path(
        ...,
        description=f"Divisional chart code. One of: {', '.join(_VALID_VARGAS)}.",
    ),
) -> VargaChartResponse:
    varga_upper = varga.upper()
    if varga_upper not in SUPPORTED_VARGAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown varga '{varga}'. Supported: {_VALID_VARGAS}",
        )

    try:
        chart = engine.compute(
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            varga=varga_upper,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing %s: %s", varga_upper, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute {varga_upper} chart.",
        )

    return _serialise_chart(chart)
