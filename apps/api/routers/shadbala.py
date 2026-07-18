"""
AstroOS — Shadbala Router

Endpoints
---------
POST /api/v1/shadbala/phase1            — Naisargika + Dig + Drik Bala
POST /api/v1/shadbala/phase2            — Chesta + Paksha + Ayana + Yuddha Bala
POST /api/v1/shadbala/sthana-bala       — Uchcha + Kendradi + Drekkana Bala
POST /api/v1/shadbala/saptavargaja      — Sthana Bala's cross-varga sub-component
POST /api/v1/shadbala/ojayugmarasyamsa  — Sthana Bala's D1/D9 odd-even sub-component
POST /api/v1/shadbala/tribhaga          — Kala Bala's day/night sub-component
POST /api/v1/shadbala/nathonnata        — Kala Bala's noon/midnight sub-component
POST /api/v1/shadbala/dina-hora         — Kala Bala's day/hour lordship sub-component
POST /api/v1/shadbala/all               — Every implemented component in one call

No business logic lives here — all computation is delegated to
ShadbalaEngine. ShadbalaEngine deliberately exposes no persistence
layer and no "total Shadbala" sum (see services/shadbala_engine.py's
module docstring) — these endpoints are compute-only and mirror that
same grouping exactly.

The D1Chart ShadbalaEngine needs is built via HoroscopeEngine,
constructed here without any repositories (compute-only — see
horoscope_engine.py, whose repo constructor args are all optional
specifically to support this). No D1 chart persistence happens from
this router either.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.schemas.shadbala import (
    AllShadbalaResponse,
    BalaComponentResponse,
    Phase1ComponentsResponse,
    Phase2ComponentsResponse,
    ShadbalaRequest,
    SthanaBalaComponentsResponse,
)
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala_engine import ShadbalaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shadbala", tags=["Shadbala"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    """
    Build a compute-only HoroscopeEngine (no repositories) using the
    process-wide EphemerisWrapper singleton — needed here only to obtain
    the D1Chart ShadbalaEngine consumes, not to persist anything.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    """
    return HoroscopeEngine(wrapper)


def _get_shadbala_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ShadbalaEngine:
    """
    Build a fully-wired ShadbalaEngine — with both a DivisionalEngine
    (for Saptavargaja/Ojayugmarasyamsa Bala) and the process-wide
    EphemerisWrapper (for Tribhaga/Nathonnata/Dina-Hora Bala's following-
    sunrise search) — so every implemented compute_*() method works.

    DivisionalEngine is constructed here compute-only too (no repos —
    see divisional_engine.py, whose repo constructor args are all
    optional), matching this router's no-persistence scope.
    """
    return ShadbalaEngine(
        divisional_engine=DivisionalEngine(wrapper),
        ephemeris_wrapper=wrapper,
    )


async def _build_chart(
    horoscope_engine: HoroscopeEngine, body: ShadbalaRequest
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
        logger.exception("Error building D1 chart for Shadbala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build birth chart for Shadbala computation.",
        ) from exc


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_component(c: BalaComponentResult) -> BalaComponentResponse:
    return BalaComponentResponse(
        component_id=c.component_id,
        component_name=c.component_name,
        rule_version=c.rule_version,
        planet=c.planet,
        value_shashtiamsas=c.value_shashtiamsas,
        trace=list(c.trace),
    )


def _serialise_list(results: list[BalaComponentResult]) -> list[BalaComponentResponse]:
    return [_serialise_component(r) for r in results]


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/phase1",
    response_model=Phase1ComponentsResponse,
    summary="Compute Naisargika + Dig + Drik Bala",
    description="Phase 1 Shadbala components — need only the already-built D1 chart.",
)
async def compute_phase1(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> Phase1ComponentsResponse:
    chart = await _build_chart(horoscope_engine, body)
    try:
        components = await asyncio.to_thread(engine.compute_phase1_components, chart)
    except Exception as exc:
        logger.exception("Error computing Shadbala phase1: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Shadbala phase1 components.",
        ) from exc

    return Phase1ComponentsResponse(
        naisargika_bala=_serialise_list(components["naisargika_bala"]),
        dig_bala=_serialise_list(components["dig_bala"]),
        drik_bala=_serialise_list(components["drik_bala"]),
    )


@router.post(
    "/phase2",
    response_model=Phase2ComponentsResponse,
    summary="Compute Chesta + Paksha + Ayana + Yuddha Bala",
    description="Phase 2 Kala Bala sub-components — need only the already-built D1 chart.",
)
async def compute_phase2(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> Phase2ComponentsResponse:
    chart = await _build_chart(horoscope_engine, body)
    try:
        components = await asyncio.to_thread(engine.compute_phase2_components, chart)
    except Exception as exc:
        logger.exception("Error computing Shadbala phase2: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Shadbala phase2 components.",
        ) from exc

    return Phase2ComponentsResponse(
        chesta_bala=_serialise_list(components["chesta_bala"]),
        paksha_bala=_serialise_list(components["paksha_bala"]),
        ayana_bala=_serialise_list(components["ayana_bala"]),
        yuddha_bala=_serialise_list(components["yuddha_bala"]),
    )


@router.post(
    "/sthana-bala",
    response_model=SthanaBalaComponentsResponse,
    summary="Compute Uchcha + Kendradi + Drekkana Bala",
    description=(
        "3 of Sthana Bala's 5 sub-components — the ones needing only the "
        "already-built D1 chart. See /saptavargaja and /ojayugmarasyamsa "
        "for the other 2."
    ),
)
async def compute_sthana_bala(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> SthanaBalaComponentsResponse:
    chart = await _build_chart(horoscope_engine, body)
    try:
        components = await asyncio.to_thread(engine.compute_sthana_bala_components, chart)
    except Exception as exc:
        logger.exception("Error computing Shadbala sthana-bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Sthana Bala components.",
        ) from exc

    return SthanaBalaComponentsResponse(
        uchcha_bala=_serialise_list(components["uchcha_bala"]),
        kendradi_bala=_serialise_list(components["kendradi_bala"]),
        drekkana_bala=_serialise_list(components["drekkana_bala"]),
    )


@router.post(
    "/saptavargaja",
    response_model=list[BalaComponentResponse],
    summary="Compute Saptavargaja Bala",
    description=(
        "Sthana Bala's cross-varga sub-component — computes D2/D3/D7/D9/"
        "D12/D30 internally via DivisionalEngine."
    ),
)
async def compute_saptavargaja(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> list[BalaComponentResponse]:
    chart = await _build_chart(horoscope_engine, body)
    try:
        results = await asyncio.to_thread(
            engine.compute_saptavargaja_bala,
            chart,
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
        logger.exception("Error computing Saptavargaja Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Saptavargaja Bala.",
        ) from exc

    return _serialise_list(results)


@router.post(
    "/ojayugmarasyamsa",
    response_model=list[BalaComponentResponse],
    summary="Compute Ojayugmarasyamsa Bala",
    description="Sthana Bala's last sub-component — D1 + D9 odd/even sign check.",
)
async def compute_ojayugmarasyamsa(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> list[BalaComponentResponse]:
    chart = await _build_chart(horoscope_engine, body)
    try:
        results = await asyncio.to_thread(
            engine.compute_ojayugmarasyamsa_bala,
            chart,
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
        logger.exception("Error computing Ojayugmarasyamsa Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Ojayugmarasyamsa Bala.",
        ) from exc

    return _serialise_list(results)


@router.post(
    "/tribhaga",
    response_model=list[BalaComponentResponse],
    summary="Compute Tribhaga Bala",
    description="Kala Bala's three-part day/night sub-component.",
)
async def compute_tribhaga(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> list[BalaComponentResponse]:
    chart = await _build_chart(horoscope_engine, body)
    try:
        results = await asyncio.to_thread(
            engine.compute_tribhaga_bala,
            chart,
            latitude=body.latitude,
            longitude=body.longitude,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing Tribhaga Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Tribhaga Bala.",
        ) from exc

    return _serialise_list(results)


@router.post(
    "/nathonnata",
    response_model=list[BalaComponentResponse],
    summary="Compute Nathonnata Bala",
    description="Kala Bala's noon/midnight proximity sub-component.",
)
async def compute_nathonnata(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> list[BalaComponentResponse]:
    chart = await _build_chart(horoscope_engine, body)
    try:
        results = await asyncio.to_thread(
            engine.compute_nathonnata_bala,
            chart,
            latitude=body.latitude,
            longitude=body.longitude,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing Nathonnata Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Nathonnata Bala.",
        ) from exc

    return _serialise_list(results)


@router.post(
    "/dina-hora",
    response_model=list[BalaComponentResponse],
    summary="Compute Dina-Hora Bala",
    description=(
        "Kala Bala's day/hour lordship sub-component — the Dina+Hora half "
        "of the classical Varsha-Masa-Dina-Hora Bala (Varsha/Masa lord is "
        "a tracked scope gap, see not_yet_implemented_components in /all)."
    ),
)
async def compute_dina_hora(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> list[BalaComponentResponse]:
    chart = await _build_chart(horoscope_engine, body)
    try:
        results = await asyncio.to_thread(
            engine.compute_dina_hora_bala,
            chart,
            latitude=body.latitude,
            longitude=body.longitude,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing Dina-Hora Bala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Dina-Hora Bala.",
        ) from exc

    return _serialise_list(results)


@router.post(
    "/all",
    response_model=AllShadbalaResponse,
    summary="Compute every implemented Shadbala component",
    description=(
        "Computes every implemented Shadbala component/sub-component in a "
        "single call, grouped exactly as ShadbalaEngine groups them. No "
        "total Shadbala sum is provided — see "
        "not_yet_implemented_components for the one remaining scope gap."
    ),
)
async def compute_all_shadbala(
    body: ShadbalaRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    engine: ShadbalaEngine = Depends(_get_shadbala_engine),
) -> AllShadbalaResponse:
    chart = await _build_chart(horoscope_engine, body)

    try:
        phase1 = await asyncio.to_thread(engine.compute_phase1_components, chart)
        phase2 = await asyncio.to_thread(engine.compute_phase2_components, chart)
        sthana = await asyncio.to_thread(engine.compute_sthana_bala_components, chart)
        saptavargaja = await asyncio.to_thread(
            engine.compute_saptavargaja_bala,
            chart,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        ojayugmarasyamsa = await asyncio.to_thread(
            engine.compute_ojayugmarasyamsa_bala,
            chart,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        tribhaga = await asyncio.to_thread(
            engine.compute_tribhaga_bala, chart, latitude=body.latitude, longitude=body.longitude
        )
        nathonnata = await asyncio.to_thread(
            engine.compute_nathonnata_bala, chart, latitude=body.latitude, longitude=body.longitude
        )
        dina_hora = await asyncio.to_thread(
            engine.compute_dina_hora_bala, chart, latitude=body.latitude, longitude=body.longitude
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.exception("Error computing full Shadbala view: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Shadbala.",
        ) from exc

    return AllShadbalaResponse(
        phase1=Phase1ComponentsResponse(
            naisargika_bala=_serialise_list(phase1["naisargika_bala"]),
            dig_bala=_serialise_list(phase1["dig_bala"]),
            drik_bala=_serialise_list(phase1["drik_bala"]),
        ),
        phase2=Phase2ComponentsResponse(
            chesta_bala=_serialise_list(phase2["chesta_bala"]),
            paksha_bala=_serialise_list(phase2["paksha_bala"]),
            ayana_bala=_serialise_list(phase2["ayana_bala"]),
            yuddha_bala=_serialise_list(phase2["yuddha_bala"]),
        ),
        sthana_bala=SthanaBalaComponentsResponse(
            uchcha_bala=_serialise_list(sthana["uchcha_bala"]),
            kendradi_bala=_serialise_list(sthana["kendradi_bala"]),
            drekkana_bala=_serialise_list(sthana["drekkana_bala"]),
        ),
        saptavargaja_bala=_serialise_list(saptavargaja),
        ojayugmarasyamsa_bala=_serialise_list(ojayugmarasyamsa),
        tribhaga_bala=_serialise_list(tribhaga),
        nathonnata_bala=_serialise_list(nathonnata),
        dina_hora_bala=_serialise_list(dina_hora),
        implemented_components=engine.implemented_components(),
        not_yet_implemented_components=engine.not_yet_implemented_components(),
    )
