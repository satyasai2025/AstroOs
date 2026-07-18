"""
AstroOS — Ashtakavarga Router

Endpoints
---------
POST /api/v1/ashtakavarga/bhinnashtakavarga           — unreduced per-graha bindu tables
POST /api/v1/ashtakavarga/bhinnashtakavarga/reduced   — per-graha bindu tables after Shodhana
POST /api/v1/ashtakavarga/sarvashtakavarga            — combined bindu table (all 7 grahas)
POST /api/v1/ashtakavarga/all                         — all of the above in one call

No business logic lives here — all computation is delegated to
AshtakavargaEngine. AshtakavargaEngine itself has no persistence layer
(no repository takes its results), so these endpoints are compute-only,
matching what the engine actually supports — see
apps/api/services/ashtakavarga_engine.py's module docstring.

The D1Chart AshtakavargaEngine needs is built via HoroscopeEngine,
constructed here without any repositories (compute-only — HoroscopeEngine
makes all three repo constructor args optional specifically so it can be
used this way, see horoscope_engine.py). No D1 chart persistence happens
from this router either.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.horoscope import D1Chart
from apps.api.schemas.ashtakavarga import (
    AllAshtakavargaResponse,
    AshtakavargaRequest,
    BhinnashtakavargaResponse,
    SarvashtakavargaResponse,
)
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ashtakavarga", tags=["Ashtakavarga"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    """
    Build a compute-only HoroscopeEngine (no repositories) using the
    process-wide EphemerisWrapper singleton — needed here only to obtain
    the D1Chart AshtakavargaEngine consumes, not to persist anything.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    """
    return HoroscopeEngine(wrapper)


def _get_ashtakavarga_engine() -> AshtakavargaEngine:
    """AshtakavargaEngine is stateless and needs only a D1Chart at call time."""
    return AshtakavargaEngine()


async def _build_chart(
    horoscope_engine: HoroscopeEngine, body: AshtakavargaRequest
) -> D1Chart:
    try:
        # Blocking pyswisseph call — offload to a worker thread so it does
        # not freeze the event loop. See horoscope.py's generate_d1_chart
        # for the full rationale.
        return await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error building D1 chart for Ashtakavarga: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build birth chart for Ashtakavarga computation.",
        ) from exc


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_bhinna(result: BhinnashtakavargaResult) -> BhinnashtakavargaResponse:
    return BhinnashtakavargaResponse(
        target_planet=result.target_planet,
        bindus_by_rashi=list(result.bindus_by_rashi),
        total_bindus=result.total_bindus,
        rule_version=result.rule_version,
    )


def _serialise_sarva(
    result: SarvashtakavargaResult, checksum_valid: bool
) -> SarvashtakavargaResponse:
    return SarvashtakavargaResponse(
        bindus_by_rashi=list(result.bindus_by_rashi),
        total_bindus=result.total_bindus,
        rule_version=result.rule_version,
        checksum_valid=checksum_valid,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/bhinnashtakavarga",
    response_model=list[BhinnashtakavargaResponse],
    summary="Compute unreduced Bhinnashtakavarga for all 7 grahas",
    description=(
        "Computes each of the 7 classical grahas' individual Ashtakavarga "
        "bindu table (12 rashis, unreduced)."
    ),
)
async def compute_bhinnashtakavarga(
    body: AshtakavargaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: AshtakavargaEngine = Depends(_get_ashtakavarga_engine),
) -> list[BhinnashtakavargaResponse]:
    chart = await _build_chart(horoscope_engine, body)

    try:
        results = await asyncio.to_thread(engine.compute_bhinnashtakavarga, chart)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing Bhinnashtakavarga: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Bhinnashtakavarga.",
        ) from exc

    return [_serialise_bhinna(r) for r in results]


@router.post(
    "/bhinnashtakavarga/reduced",
    response_model=list[BhinnashtakavargaResponse],
    summary="Compute reduced Bhinnashtakavarga for all 7 grahas",
    description=(
        "Computes each of the 7 classical grahas' Bhinnashtakavarga after "
        "both classical Shodhana (reduction) passes — Trikona Shodhana "
        "then Ekadhipatya Shodhana."
    ),
)
async def compute_reduced_bhinnashtakavarga(
    body: AshtakavargaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: AshtakavargaEngine = Depends(_get_ashtakavarga_engine),
) -> list[BhinnashtakavargaResponse]:
    chart = await _build_chart(horoscope_engine, body)

    try:
        results = await asyncio.to_thread(engine.compute_reduced_bhinnashtakavarga, chart)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing reduced Bhinnashtakavarga: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute reduced Bhinnashtakavarga.",
        ) from exc

    return [_serialise_bhinna(r) for r in results]


@router.post(
    "/sarvashtakavarga",
    response_model=SarvashtakavargaResponse,
    summary="Compute Sarvashtakavarga",
    description=(
        "Sum of all 7 planetary Bhinnashtakavargas (unreduced). Includes "
        "a checksum flag — a correctly computed chart always totals 337 "
        "bindus across the 12 rashis."
    ),
)
async def compute_sarvashtakavarga(
    body: AshtakavargaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: AshtakavargaEngine = Depends(_get_ashtakavarga_engine),
) -> SarvashtakavargaResponse:
    chart = await _build_chart(horoscope_engine, body)

    try:
        result = await asyncio.to_thread(engine.compute_sarvashtakavarga, chart)
        checksum_valid = await asyncio.to_thread(engine.verify_checksum, chart, result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing Sarvashtakavarga: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Sarvashtakavarga.",
        ) from exc

    return _serialise_sarva(result, checksum_valid)


@router.post(
    "/all",
    response_model=AllAshtakavargaResponse,
    summary="Compute the full Ashtakavarga view",
    description=(
        "Computes unreduced Bhinnashtakavarga, reduced Bhinnashtakavarga, "
        "and Sarvashtakavarga in a single call."
    ),
)
async def compute_all_ashtakavarga(
    body: AshtakavargaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: AshtakavargaEngine = Depends(_get_ashtakavarga_engine),
) -> AllAshtakavargaResponse:
    chart = await _build_chart(horoscope_engine, body)

    try:
        bhinna = await asyncio.to_thread(engine.compute_bhinnashtakavarga, chart)
        bhinna_reduced = await asyncio.to_thread(
            engine.compute_reduced_bhinnashtakavarga, chart, bhinna
        )
        sarva = await asyncio.to_thread(engine.compute_sarvashtakavarga, chart, bhinna)
        checksum_valid = await asyncio.to_thread(engine.verify_checksum, chart, sarva)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing full Ashtakavarga view: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Ashtakavarga.",
        ) from exc

    return AllAshtakavargaResponse(
        bhinnashtakavarga=[_serialise_bhinna(r) for r in bhinna],
        bhinnashtakavarga_reduced=[_serialise_bhinna(r) for r in bhinna_reduced],
        sarvashtakavarga=_serialise_sarva(sarva, checksum_valid),
    )
