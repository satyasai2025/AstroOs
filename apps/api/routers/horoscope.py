"""
AstroOS — Horoscope Router (Task 4)

Exposes the D1 chart generation endpoint.
The chart-computation endpoints (generate_d1_chart) keep business logic
in HoroscopeEngine; this file handles only HTTP concerns there: input
validation, response serialisation, error mapping.

list_my_charts/delete_chart/set_default_chart are deliberately different:
they're simple CRUD against BirthChartRepository (list, soft-delete, flag
one row as default) with no chart-computation logic to own, so they call
the repository directly rather than round-tripping through
HoroscopeEngine for no reason. This is the intended pattern for
simple-CRUD routes in this codebase (documented as part of Phase 10's
retroactive review, 2026-07-23) — an earlier version of this docstring's
blanket "all business logic lives in HoroscopeEngine" claim didn't carve
out this exception, which risked someone reading it as license to force
an engine indirection where none is needed.
"""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    get_ephemeris_wrapper,
    require_entitlement,
)
from apps.api.domain.ephemeris import DignityType
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.user import User
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.schemas.horoscope import (
    AscendantSchema,
    AspectSchema,
    BirthChartListResponse,
    BirthChartSummarySchema,
    D1ChartRequest,
    D1ChartResponse,
    HouseCuspSchema,
    KaranaSchema,
    NakshatraInfoSchema,
    PanchangaSchema,
    PlanetPositionSchema,
    PlanetStrengthSchema,
    TithiSchema,
    VaraSchema,
    YogaSchema,
)
from apps.api.schemas.lagna_scan import (
    BoundaryDistanceSchema,
    LagnaIntervalSchema,
    LagnaScanRequest,
    LagnaScanResponse,
    PlanetSignChangeRequest,
    PlanetSignChangeResponse,
    PlanetSignPeriodSchema,
    ShiftBirthtimeRequest,
    ShiftBirthtimeResponse,
)
from apps.api.schemas.upagraha import (
    DerivedPointSchema,
    UpagrahaRequest,
    UpagrahaResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.lagna_scan_engine import LagnaScanEngine
from apps.api.services.sign_change_engine import SignChangeEngine
from apps.api.services.upagraha_engine import UpagrahaEngine
from apps.api.services.quota_service import QuotaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/horoscope", tags=["Horoscope"])


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    session: AsyncSession = Depends(get_db_session),
) -> HoroscopeEngine:
    """
    Build a HoroscopeEngine using the process-wide EphemerisWrapper singleton,
    plus request-scoped repositories for persistence.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    The repositories, unlike the wrapper, are cheap and request-scoped —
    each request gets its own, bound to that request's DB session.
    """
    return HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(session),
        planet_position_repo=PlanetPositionRepository(session),
        house_repo=HouseRepository(session),
    )


def _chart_to_response(chart: D1Chart, chart_id: uuid.UUID | None = None) -> D1ChartResponse:
    """Convert a D1Chart domain object to the HTTP response schema."""

    asc_nav_rashi, asc_nav_deg = compute_varga_sign("D9", chart.ascendant.sidereal_longitude)
    ascendant = AscendantSchema(
        longitude=round(chart.ascendant.longitude, 8),
        sidereal_longitude=round(chart.ascendant.sidereal_longitude, 8),
        rashi=chart.ascendant.rashi,
        rashi_degree=round(chart.ascendant.rashi_degree, 8),
        nakshatra=chart.ascendant.nakshatra,
        pada=chart.ascendant.pada,
        nakshatra_lord=chart.ascendant.nakshatra_lord,
        sub_lord=chart.ascendant.sub_lord,
        sub_sub_lord=chart.ascendant.sub_sub_lord,
        navamsa_rashi=asc_nav_rashi,
        navamsa_rashi_degree=round(asc_nav_deg, 8),
    )

    houses = [
        HouseCuspSchema(
            house_number=h.house_number,
            longitude=round(h.longitude, 8),
            sidereal_longitude=round(h.sidereal_longitude, 8),
            rashi=h.rashi,
            nakshatra_lord=h.nakshatra_lord,
            sub_lord=h.sub_lord,
            sub_sub_lord=h.sub_sub_lord,
        )
        for h in chart.houses
    ]

    planets = []
    for p in chart.planets:
        nav_rashi, nav_deg = compute_varga_sign("D9", p.sidereal_longitude)
        planets.append(
            PlanetPositionSchema(
                planet=p.planet,
                sidereal_longitude=round(p.sidereal_longitude, 8),
                rashi=p.rashi,
                rashi_degree=round(p.rashi_degree, 8),
                house_number=p.house_number,
                nakshatra=p.nakshatra,
                pada=p.pada,
                is_retrograde=p.is_retrograde,
                is_combust=p.is_combust,
                combustion_orb=round(p.combustion_orb, 8) if p.combustion_orb is not None else None,
                dignity=p.dignity.value if p.dignity else None,
                nakshatra_lord=p.nakshatra_lord,
                sub_lord=p.sub_lord,
                sub_sub_lord=p.sub_sub_lord,
                rashi_house_number=p.rashi_house_number,
                navamsa_rashi=nav_rashi,
                navamsa_rashi_degree=round(nav_deg, 8),
            )
        )

    aspects = [
        AspectSchema(
            from_planet=a.from_planet,
            to_planet=a.to_planet,
            aspect_type=a.aspect_type,
            orb_degrees=a.orb_degrees,
            is_applying=a.is_applying,
        )
        for a in chart.aspects
    ]

    strengths = [
        PlanetStrengthSchema(
            planet=s.planet,
            dignity=s.dignity.value if s.dignity else None,
            is_retrograde=s.is_retrograde,
            is_combust=s.is_combust,
            house_number=s.house_number,
            is_in_own_sign=s.is_in_own_sign,
            is_exalted=s.is_exalted,
            is_debilitated=s.is_debilitated,
            is_in_kendra=s.is_in_kendra,
            is_in_trikona=s.is_in_trikona,
            is_in_dusthana=s.is_in_dusthana,
            strength_score=s.strength_score,
        )
        for s in chart.planet_strengths
    ]

    panchanga = chart.panchanga
    pan_schema = PanchangaSchema(
        tithi=TithiSchema(
            number=panchanga.tithi.number,
            name=panchanga.tithi.name,
            paksha=panchanga.tithi.paksha,
            completion_percent=panchanga.tithi.completion_percent,
        ),
        nakshatra=NakshatraInfoSchema(
            nakshatra=panchanga.nakshatra.nakshatra,
            nakshatra_number=panchanga.nakshatra.nakshatra_number,
            pada=panchanga.nakshatra.pada,
            lord=panchanga.nakshatra.lord,
            degree_in_nakshatra=round(panchanga.nakshatra.degree_in_nakshatra, 6),
            degree_in_pada=round(panchanga.nakshatra.degree_in_pada, 6),
        ),
        yoga=YogaSchema(
            number=panchanga.yoga.number,
            name=panchanga.yoga.name,
            completion_percent=panchanga.yoga.completion_percent,
        ),
        karana=KaranaSchema(
            number=panchanga.karana.number,
            name=panchanga.karana.name,
            is_fixed=panchanga.karana.is_fixed,
        ),
        vara=VaraSchema(
            number=panchanga.vara.number,
            name=panchanga.vara.name,
            lord=panchanga.vara.lord,
        ),
        julian_day=panchanga.julian_day,
        ayanamsa_deg=round(panchanga.ayanamsa_deg, 8),
    )

    return D1ChartResponse(
        id=chart_id,
        ascendant=ascendant,
        houses=houses,
        planets=planets,
        aspects=aspects,
        planet_strengths=strengths,
        panchanga=pan_schema,
        ayanamsa_system=chart.ayanamsa_system,
        house_system=chart.house_system,
        julian_day=chart.ephemeris.julian_day,
        ayanamsa_value=round(chart.ephemeris.ayanamsa_value, 8),
    )


@router.post(
    "/d1",
    response_model=D1ChartResponse,
    summary="Generate D1 (Rashi) birth chart",
    description=(
        "Calculates the complete Rashi chart (D1) for the given birth data. "
        "Returns all nine Graha positions, house cusps, aspects, planet strengths, "
        "and the Panchanga (Tithi, Nakshatra, Yoga, Karana, Vara)."
    ),
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_entitlement("saved_horoscopes", "create"))],
)
async def generate_d1_chart(
    request: D1ChartRequest,
    user: User = Depends(get_current_user_from_bearer),
    engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    session: AsyncSession = Depends(get_db_session),
) -> D1ChartResponse:
    """
    Generate a D1 (Rashi) birth chart.

    - **birth_datetime_utc**: UTC birth datetime (must include timezone, e.g. `2000-01-01T05:30:00+00:00`)
    - **latitude**: Decimal degrees (+N / -S)
    - **longitude**: Decimal degrees (+E / -W)
    - **ayanamsa**: `lahiri` (default) | `kp` | `raman` | `yukteshwar` | `fagan_bradley` | `true_chitra` | `true_pushya`
    - **house_system**: `W` = Whole Sign (default) | `P` = Placidus | `K` = Koch | `E` = Equal
    """
    try:
        # generate_d1 is a blocking, CPU-bound call into pyswisseph's C
        # library. Running it directly inside this async handler would
        # freeze the event loop for every other in-flight request (auth,
        # health checks, everything) for the duration of the calculation.
        # asyncio.to_thread offloads it to a worker thread; the wrapper's
        # internal lock (see EphemerisWrapper.calculate) still serializes
        # access to pyswisseph's process-global state across those threads.
        chart = await asyncio.to_thread(
            engine.generate_d1,
            birth_datetime_utc=request.birth_datetime_utc,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
            node_type=request.node_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.exception("Swiss Ephemeris calculation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ephemeris calculation failed. Check server logs.",
        ) from exc

    # ── Phase 4 quota pre-check ────────────────────────────────────────────────
    # Before we persist (which is the actual quota-consuming operation), verify
    # the user still has headroom under their plan's monthly limit for
    # saved_horoscopes.  The entitlement dependency above already confirmed the
    # plan includes the feature at all; this is the usage-budget gate.
    quota_service = QuotaService(session)
    quota_status = await quota_service.check_quota(
        user=user,
        feature_key="saved_horoscopes",
        amount=1,
    )
    if not quota_status.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXHAUSTED",
                "message": (
                    f"You have reached your monthly limit of "
                    f"{quota_status.limit} saved horoscopes. "
                    f"Limit resets in {quota_status.reset_in}s."
                ),
                "limit": quota_status.limit,
                "current_usage": quota_status.current_usage,
                "reset_in_seconds": quota_status.reset_in,
            },
        )

    # Persistence step. The calculation above already succeeded and its
    # result is what we return either way — but if saving it fails, that
    # is reported as an error rather than silently returned as if nothing
    # was persisted. get_db_session's session (see apps/api/dependencies.py)
    # rolls back automatically once this exception propagates out of the
    # request, so a failed persist never leaves a partial chart committed.
    try:
        chart_id = await engine.persist_d1(
            chart,
            birth_datetime_utc=request.birth_datetime_utc,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
            user_id=user.id.value,
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to persist D1 chart: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Chart was computed successfully but could not be saved. "
                "Please retry."
            ),
        ) from exc

    # ── Phase 4 quota consumption ────────────────────────────────────────────────
    # Persistence succeeded → atomically increment the usage counter so it
    # cannot exceed the plan limit between the pre-check above and the record
    # insertion.  consume_quota re-checks atomically (row-level lock on the
    # usage row) to close the race window for concurrent requests.
    consumed = await quota_service.consume_quota(
        user=user,
        feature_key="saved_horoscopes",
        amount=1,
    )
    if not consumed:
        # Extremely unlikely: raced past the pre-check.  Roll back the just
        # committed chart so the user's quota state stays consistent.
        logger.error(
            "Quota consumed after pre-check passed for user %s, feature "
            "saved_horoscopes — rolling back chart_id %s",
            user.id.value,
            chart_id,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "QUOTA_EXHAUSTED_RACE",
                "message": (
                    "Your monthly saved-horoscope limit was reached by a "
                    "concurrent request. The chart was computed but not "
                    "saved; please retry next month."
                ),
            },
        )

    return _chart_to_response(chart, chart_id=chart_id)


@router.get(
    "/my-charts",
    response_model=BirthChartListResponse,
    summary="List the logged-in user's saved charts",
    description=(
        "Returns the birth charts saved under the authenticated user's "
        "account, most recently created first."
    ),
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_entitlement("saved_horoscopes", "view"))],
)
async def list_my_charts(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> BirthChartListResponse:
    repo = BirthChartRepository(session)
    user_id = current_user.id.value
    charts = await repo.list_for_user(user_id, limit=limit, offset=offset)
    total = await repo.count_for_user(user_id)
    return BirthChartListResponse(
        charts=[BirthChartSummarySchema.model_validate(c) for c in charts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/charts/{chart_id}",
    response_model=BirthChartSummarySchema,
    summary="Get a saved chart by id",
    description=(
        "Returns the saved birth chart summary for the authenticated user."
    ),
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_entitlement("saved_horoscopes", "view"))],
)
async def get_chart_by_id(
    chart_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> BirthChartSummarySchema:
    repo = BirthChartRepository(session)
    chart = await repo.get_by_id(chart_id)
    if chart is None or (chart.user_id is not None and chart.user_id != current_user.id.value):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved chart with that id, or it isn't yours.",
        )
    return BirthChartSummarySchema.model_validate(chart)


@router.delete(
    "/charts/{chart_id}",
    summary="Delete a saved chart",
    description=(
        "Soft-deletes one of the authenticated user's saved charts. The "
        "underlying row (and its planet positions, houses, divisional "
        "charts, dashas) is kept in the database with deleted_at set, not "
        "actually removed — it just stops appearing in my-charts and "
        "every other chart query."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_entitlement("saved_horoscopes", "edit"))],
)
async def delete_chart(
    chart_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    repo = BirthChartRepository(session)
    deleted = await repo.soft_delete(chart_id, current_user.id.value)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved chart with that id, or it isn't yours.",
        )
    await session.commit()


@router.post(
    "/charts/{chart_id}/set-default",
    summary="Mark a saved chart as the user's default",
    description=(
        "Sets one of the authenticated user's saved charts as their "
        "default, unsetting whichever chart previously held that flag. "
        "A user's first saved chart is marked default automatically; this "
        "endpoint is for switching it to a different chart later."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_entitlement("saved_horoscopes", "edit"))],
)
async def set_default_chart(
    chart_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    repo = BirthChartRepository(session)
    ok = await repo.set_default(chart_id, current_user.id.value)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved chart with that id, or it isn't yours.",
        )
    await session.commit()


@router.post(
    "/upagrahas",
    response_model=UpagrahaResponse,
    summary="Compute Gulika/Maandi and the Bhava/Hora/Ghati lagnas",
    description=(
        "Derived chart points that are not planets.\n\n"
        "**Gulika / Maandi** — the day (sunrise→sunset) or night "
        "(sunset→next sunrise) is split into eight equal parts, ruled by the "
        "grahas in weekday order starting from the weekday lord (day birth) "
        "or the 5th weekday onward (night birth). Gulika is the ascendant at "
        "the start of Saturn's part, Maandi at its midpoint.\n\n"
        "**Bhava / Hora / Ghati Lagna** — progressions of the Sun's position "
        "at sunrise, advancing 15°, 30° and 75° per hour respectively.\n\n"
        "Sunrise and sunset use the centre of the solar disc without "
        "refraction, the classical Vedic convention (Swiss Ephemeris defaults "
        "to the refracted upper limb, which shifts these points by ~1°). "
        "`weekday` is reckoned sunrise-to-sunrise, so a pre-dawn birth carries "
        "the previous calendar day."
    ),
    status_code=status.HTTP_200_OK,
)
async def compute_upagrahas(
    request: UpagrahaRequest,
    user: User = Depends(get_current_user_from_bearer),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> UpagrahaResponse:
    """
    - **birth_datetime_utc**: UTC birth datetime (must include timezone)
    - **latitude** / **longitude**: decimal degrees (+N/-S, +E/-W)
    - **ayanamsa**: `lahiri` (default) | `kp` | `raman` | `yukteshwar` |
      `fagan_bradley` | `true_chitra` | `true_pushya`
    """
    engine = UpagrahaEngine(wrapper)
    try:
        # Blocking pyswisseph work — keep it off the event loop, same as /d1.
        result = await asyncio.to_thread(
            engine.compute,
            request.birth_datetime_utc,
            request.latitude,
            request.longitude,
            request.ayanamsa,
        )
    except (RuntimeError, ValueError) as exc:
        logger.exception("Upagraha computation failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not compute upagrahas: {exc}",
        )

    def _point(p) -> DerivedPointSchema:
        return DerivedPointSchema(
            name=p.name,
            sidereal_longitude=p.sidereal_longitude,
            rashi=p.rashi,
            rashi_degree=p.rashi_degree,
            nakshatra=p.nakshatra,
            pada=p.pada,
            nakshatra_lord=p.nakshatra_lord,
            house_number=p.house_number,
        )

    return UpagrahaResponse(
        upagrahas=[_point(p) for p in result.upagrahas],
        special_lagnas=[_point(p) for p in result.special_lagnas],
        is_daytime_birth=result.is_daytime_birth,
        weekday=result.weekday,
        starting_lord=result.starting_lord,
        part_duration_minutes=result.part_duration_hours * 60.0,
    )


@router.post(
    "/lagna-scan",
    response_model=LagnaScanResponse,
    summary="When does the lagna change sign?",
    description=(
        "Birth-time rectification support: where the lagna sits, how close it "
        "is to the next rashi / nakshatra / pada boundary, and a timeline of "
        "lagna sign changes around the birth moment.\n\n"
        "`arcmin_per_minute` is the sensitivity figure — how far the lagna "
        "moves per minute of birth-time error at this latitude and rising "
        "sign. Charts born near a boundary can flip sign on an uncertainty of "
        "well under a minute, changing the lagna lord and every bhava."
    ),
    status_code=status.HTTP_200_OK,
)
async def lagna_scan(
    request: LagnaScanRequest,
    user: User = Depends(get_current_user_from_bearer),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> LagnaScanResponse:
    engine = LagnaScanEngine(wrapper)
    try:
        # Bisection runs dozens of blocking pyswisseph calls — keep it off
        # the event loop, same as /d1.
        result = await asyncio.to_thread(
            engine.scan,
            request.birth_datetime_utc,
            request.latitude,
            request.longitude,
            request.ayanamsa,
            request.window_hours,
        )
    except (RuntimeError, ValueError) as exc:
        logger.exception("Lagna scan failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not scan lagna: {exc}",
        )

    return LagnaScanResponse(
        sidereal_longitude=result.sidereal_longitude,
        rashi=result.rashi,
        rashi_degree=result.rashi_degree,
        nakshatra=result.nakshatra,
        pada=result.pada,
        arcmin_per_minute=result.arcmin_per_minute,
        boundaries=[
            BoundaryDistanceSchema(
                label=b.label,
                minutes_since_previous=b.minutes_since_previous,
                minutes_until_next=b.minutes_until_next,
                degrees_since_previous=b.degrees_since_previous,
                degrees_until_next=b.degrees_until_next,
            )
            for b in result.boundaries
        ],
        intervals=[
            LagnaIntervalSchema(
                rashi=i.rashi,
                start_utc=i.start_utc,
                end_utc=i.end_utc,
                duration_minutes=i.duration_minutes,
                contains_birth=i.contains_birth,
            )
            for i in result.intervals
        ],
        window_start_utc=result.window_start_utc,
        window_end_utc=result.window_end_utc,
    )


@router.post(
    "/shift-birthtime",
    response_model=ShiftBirthtimeResponse,
    summary="Birth time that moves the lagna to the adjacent sign",
    description=(
        "Returns the birth time that would place the lagna just inside the "
        "next or previous rashi — the counterpart to Classical Vedic System's "
        "\"Change birthtime to move lagna to → the previous / the next sign\". "
        "Useful for bounding how far a birth time would have to be wrong for "
        "the lagna to differ."
    ),
    status_code=status.HTTP_200_OK,
)
async def shift_birthtime(
    request: ShiftBirthtimeRequest,
    user: User = Depends(get_current_user_from_bearer),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ShiftBirthtimeResponse:
    engine = LagnaScanEngine(wrapper)
    try:
        shifted = await asyncio.to_thread(
            engine.birthtime_for_adjacent_sign,
            request.birth_datetime_utc,
            request.latitude,
            request.longitude,
            request.direction,
            request.ayanamsa,
        )
        confirm = await asyncio.to_thread(
            engine.scan,
            shifted, request.latitude, request.longitude, request.ayanamsa, 0.1,
        )
    except (RuntimeError, ValueError) as exc:
        logger.exception("Birthtime shift failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not shift birth time: {exc}",
        )

    delta = shifted - request.birth_datetime_utc
    return ShiftBirthtimeResponse(
        original_birth_datetime_utc=request.birth_datetime_utc,
        shifted_birth_datetime_utc=shifted,
        shift_minutes=delta.total_seconds() / 60.0,
        direction=request.direction,
        resulting_rashi=confirm.rashi,
        resulting_rashi_degree=confirm.rashi_degree,
    )


@router.post(
    "/planet-sign-change",
    response_model=PlanetSignChangeResponse,
    summary="When will a planet change sign?",
    description=(
        "For each graha: when it entered its current rashi and when it will "
        "leave. Pass `planet` to scan one, omit it for all nine.\n\n"
        "These come from an actual scan, not from degrees-remaining ÷ speed — "
        "planetary longitude is non-monotonic, so a retrograde planet can "
        "approach a boundary, station, and cross much later or in the other "
        "direction. On the reference chart the naive estimate puts Jupiter in "
        "Libra in 56 days when it actually reaches Sagittarius after 190, and "
        "puts Saturn's change at 196 days when a retrograde loop pushes it to "
        "712.\n\n"
        "`next_rashi` is therefore the sign genuinely entered, which for a "
        "retrograde planet is the preceding one. Ketu is derived from Rahu, so "
        "the two always turn together."
    ),
    status_code=status.HTTP_200_OK,
)
async def planet_sign_change(
    request: PlanetSignChangeRequest,
    user: User = Depends(get_current_user_from_bearer),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> PlanetSignChangeResponse:
    engine = SignChangeEngine(wrapper)
    valid = {"sun", "moon", "mars", "mercury", "jupiter",
             "venus", "saturn", "rahu", "ketu"}
    if request.planet is not None and request.planet not in valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown planet {request.planet!r}. Valid: {sorted(valid)}",
        )

    try:
        # Saturn's scan can run a hundred pyswisseph calls — keep it off the
        # event loop, same as /d1.
        if request.planet:
            periods = [
                await asyncio.to_thread(
                    engine.sign_period,
                    request.planet, request.birth_datetime_utc,
                    request.latitude, request.longitude, request.ayanamsa,
                )
            ]
        else:
            periods = await asyncio.to_thread(
                engine.all_planets,
                request.birth_datetime_utc,
                request.latitude, request.longitude, request.ayanamsa,
            )
    except (RuntimeError, ValueError) as exc:
        logger.exception("Planet sign-change scan failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not scan planet sign change: {exc}",
        )

    return PlanetSignChangeResponse(
        planets=[
            PlanetSignPeriodSchema(
                planet=p.planet,
                sidereal_longitude=p.sidereal_longitude,
                rashi=p.rashi,
                rashi_degree=p.rashi_degree,
                nakshatra=p.nakshatra,
                pada=p.pada,
                is_retrograde=p.is_retrograde,
                speed_deg_per_day=p.speed_deg_per_day,
                entered_utc=p.entered_utc,
                exits_utc=p.exits_utc,
                days_since_entry=p.days_since_entry,
                days_until_exit=p.days_until_exit,
                previous_rashi=p.previous_rashi,
                next_rashi=p.next_rashi,
                exits_retrograde=p.exits_retrograde,
                search_limit_days=p.search_limit_days,
            )
            for p in periods
        ]
    )
