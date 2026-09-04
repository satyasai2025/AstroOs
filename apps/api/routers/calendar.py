"""
AstroOS — Calendar Router

Endpoints
---------
GET /api/v1/calendar   — Masa (Amanta/Purnimanta) + Samvatsara (Shaka/Vikram) for a date

No business logic lives here — computation is delegated to CalendarEngine.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.calendar import CalendarResponse, MasaResponse, SamvatsaraResponse
from apps.api.services.calendar_engine import CalendarEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])


def _get_calendar_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> CalendarEngine:
    return CalendarEngine(wrapper)


@router.get(
    "",
    response_model=CalendarResponse,
    summary="Lunar month and Samvatsara year-name for a date",
)
async def get_calendar(
    local_date: date = Query(..., description="Calendar date (local)."),
    utc_offset_minutes: int = Query(
        ..., description="UTC offset in minutes for the location on this date (e.g. IST = 330)."
    ),
    engine: CalendarEngine = Depends(_get_calendar_engine),
) -> CalendarResponse:
    local_noon = datetime.combine(local_date, time(12, 0)).replace(
        tzinfo=timezone(timedelta(minutes=utc_offset_minutes))
    )
    jd = datetime_to_jd(local_noon)

    result = engine.calculate(jd)

    return CalendarResponse(
        masa=MasaResponse(amanta=result.masa.amanta, purnimanta=result.masa.purnimanta),
        samvatsara=SamvatsaraResponse(
            shaka_year=result.samvatsara.shaka_year,
            shaka_samvatsara=result.samvatsara.shaka_samvatsara,
            vikram_year=result.samvatsara.vikram_year,
            vikram_samvatsara=result.samvatsara.vikram_samvatsara,
        ),
    )
