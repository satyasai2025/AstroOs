"""
AstroOS — Muhurta Router

Endpoints
---------
GET /api/v1/muhurta   — Hora + Rahukalam/Gulikalam/Yamagandam for a date + location

No business logic lives here — computation is delegated to MuhurtaEngine.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.muhurta import (
    ChoghadiyaPeriod,
    HoraPeriod,
    InauspiciousPeriod,
    MuhurtaResult,
)
from apps.api.schemas.muhurta import (
    ChoghadiyaResponse,
    HoraResponse,
    InauspiciousPeriodResponse,
    MuhurtaResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd, jd_to_datetime
from apps.api.services.muhurta_engine import MuhurtaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/muhurta", tags=["Muhurta"])


def _get_muhurta_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> MuhurtaEngine:
    return MuhurtaEngine(wrapper)


def _serialise_hora(h: HoraPeriod) -> HoraResponse:
    return HoraResponse(
        index=h.index, lord=h.lord,
        start=jd_to_datetime(h.start_jd), end=jd_to_datetime(h.end_jd),
        is_day=h.is_day,
    )


def _serialise_period(p: InauspiciousPeriod) -> InauspiciousPeriodResponse:
    return InauspiciousPeriodResponse(
        name=p.name, start=jd_to_datetime(p.start_jd), end=jd_to_datetime(p.end_jd),
    )


def _serialise_choghadiya(c: ChoghadiyaPeriod) -> ChoghadiyaResponse:
    return ChoghadiyaResponse(
        index=c.index, name=c.name, nature=c.nature,
        start=jd_to_datetime(c.start_jd), end=jd_to_datetime(c.end_jd),
        is_day=c.is_day,
    )


def _serialise_result(r: MuhurtaResult) -> MuhurtaResponse:
    return MuhurtaResponse(
        sunrise=jd_to_datetime(r.sunrise_jd),
        sunset=jd_to_datetime(r.sunset_jd),
        next_sunrise=jd_to_datetime(r.next_sunrise_jd),
        horas=[_serialise_hora(h) for h in r.horas],
        rahukalam=_serialise_period(r.rahukalam),
        gulikalam=_serialise_period(r.gulikalam),
        yamagandam=_serialise_period(r.yamagandam),
        choghadiya=[_serialise_choghadiya(c) for c in r.choghadiya],
    )


@router.get(
    "",
    response_model=MuhurtaResponse,
    summary="Hora and inauspicious-period timings for a date and location",
)
async def get_muhurta(
    local_date: date = Query(..., description="Calendar date (local)."),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    utc_offset_minutes: int = Query(
        ..., description="UTC offset in minutes for the location on this date (e.g. IST = 330)."
    ),
    engine: MuhurtaEngine = Depends(_get_muhurta_engine),
) -> MuhurtaResponse:
    # Anchor at local NOON, not midnight — MuhurtaEngine resolves the day's
    # sunrise/sunset by bracketing this instant, and midnight falls before
    # sunrise, which would bracket to the PREVIOUS day's sunrise instead.
    local_noon = datetime.combine(local_date, time(12, 0)).replace(
        tzinfo=timezone(timedelta(minutes=utc_offset_minutes))
    )
    jd = datetime_to_jd(local_noon)

    try:
        result = engine.calculate(jd, latitude, longitude)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return _serialise_result(result)
