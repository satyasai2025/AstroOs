"""
AstroOS — Horoscope Engine (Task 4)

Generates a D1 (Rashi / Janma Kundali) birth chart from:
  - A UTC datetime
  - Geographic coordinates
  - Ayanamsa system
  - House system

Responsibilities:
  - Orchestrates EphemerisWrapper calls
  - Delegates aspect computation to AspectEngine
  - Delegates planet strength scoring to GrahaEngine
  - Returns a D1Chart domain object

No database I/O here — persistence is the repository's concern.

As of Module 6.5 (Foundation Completion), aspect computation and planet
strength/dignity scoring were extracted into their own independent
services (aspect_engine.py, graha_engine.py) — this engine now
orchestrates them rather than computing either inline. The algorithms
themselves are unchanged; this is a relocation, verified by the full
existing test suite still passing unmodified against the new code path.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.graha_engine import (
    DUSTHANA_HOUSES as _DUSTHANA_HOUSES,
    GrahaEngine,
    KENDRA_HOUSES as _KENDRA_HOUSES,
    TRIKONA_HOUSES as _TRIKONA_HOUSES,
)
from packages.shared.enums import AyanamsaSystem

logger = logging.getLogger(__name__)

# _KENDRA_HOUSES / _TRIKONA_HOUSES / _DUSTHANA_HOUSES are re-exported from
# graha_engine.py (their new home) under their original names here purely
# for backward compatibility — tests/unit/test_horoscope_engine.py imports
# them from this module. New code should import them from graha_engine
# directly (as KENDRA_HOUSES etc, without the leading underscore).


# ---------------------------------------------------------------------------
# HoroscopeEngine
# ---------------------------------------------------------------------------

class HoroscopeEngine:
    """
    Service that generates a complete D1 chart from birth data.

    Designed to be instantiated once per request (stateless per-request logic)
    and share the underlying EphemerisWrapper singleton across requests.
    """

    def __init__(
        self,
        wrapper: EphemerisWrapper,
        birth_chart_repo=None,
        planet_position_repo=None,
        house_repo=None,
        graha_engine: Optional[GrahaEngine] = None,
        aspect_engine: Optional[AspectEngine] = None,
    ) -> None:
        self._wrapper = wrapper
        # Optional — only required for persist_d1(). Kept optional (default
        # None) so existing callers/tests that construct HoroscopeEngine
        # with just a wrapper (no persistence) are unaffected.
        self._birth_chart_repo = birth_chart_repo
        self._planet_position_repo = planet_position_repo
        self._house_repo = house_repo
        # GrahaEngine/AspectEngine are stateless and cheap to construct, so
        # a default instance is created here if the caller doesn't supply
        # one — existing single-argument construction (HoroscopeEngine
        # (wrapper)) keeps working exactly as before.
        self._graha_engine = graha_engine or GrahaEngine()
        self._aspect_engine = aspect_engine or AspectEngine()

    def generate_d1(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = AyanamsaSystem.LAHIRI.value,
        house_system: str = "W",
    ) -> D1Chart:
        """
        Generate a complete D1 (Rashi) birth chart.

        Args:
            birth_datetime_utc: UTC birth datetime (must be timezone-aware).
            latitude: Geographic latitude (+N, -S).
            longitude: Geographic longitude (+E, -W).
            ayanamsa: Ayanamsa key (default: 'lahiri').
            house_system: House system code ('W'=Whole Sign, 'P'=Placidus).

        Returns:
            D1Chart with all positions, aspects, and strength assessments.
        """
        logger.info(
            "Generating D1 chart",
            extra={
                "datetime": birth_datetime_utc.isoformat(),
                "lat": latitude,
                "lon": longitude,
                "ayanamsa": ayanamsa,
                "house_system": house_system,
            },
        )

        ephe_result = self._wrapper.calculate(
            dt=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )

        aspects = self._aspect_engine.compute(ephe_result.planet_positions)
        strengths = self._graha_engine.compute_strength(ephe_result.planet_positions)

        return D1Chart(
            ephemeris=ephe_result,
            ascendant=ephe_result.ascendant,
            houses=ephe_result.house_cusps,
            planets=ephe_result.planet_positions,
            aspects=aspects,
            planet_strengths=strengths,
            panchanga=ephe_result.panchanga,
            ayanamsa_system=ayanamsa,
            house_system=house_system,
        )

    # ── Persistence ──────────────────────────────────────────────────────────
    #
    # Deliberately separate from generate_d1() rather than a combined
    # "generate_and_persist" method: generate_d1() is a blocking, CPU-bound
    # pyswisseph call that routers offload via asyncio.to_thread (see
    # routers/horoscope.py). Persistence is async DB I/O with no CPU-bound
    # work, so it does not need — and should not be wrapped in — to_thread.
    # Keeping them as two methods lets the router keep doing exactly what
    # it already does for the calculation step, unchanged.

    async def persist_d1(
        self,
        chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = AyanamsaSystem.LAHIRI.value,
        house_system: str = "W",
        user_id: Optional[uuid.UUID] = None,
        subject_name: str = "Unnamed",
        place_name: Optional[str] = None,
        force_new: bool = False,
    ) -> uuid.UUID:
        """
        Persist an already-computed D1Chart (from generate_d1()) to
        PostgreSQL: the birth_charts anchor row, its D1 summary fields, all
        12 houses, and all 9 planet positions.

        Requires this engine to have been constructed with
        birth_chart_repo, planet_position_repo, and house_repo — raises
        RuntimeError otherwise, so a missing wiring mistake fails loudly
        instead of silently skipping persistence.

        Returns the birth_charts row id.
        """
        if not (self._birth_chart_repo and self._planet_position_repo and self._house_repo):
            raise RuntimeError(
                "HoroscopeEngine.persist_d1() requires birth_chart_repo, "
                "planet_position_repo, and house_repo to be provided at "
                "construction time."
            )

        chart_id = await self._birth_chart_repo.get_or_create(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            user_id=user_id,
            subject_name=subject_name,
            place_name=place_name,
            force_new=force_new,
        )

        await self._birth_chart_repo.update_d1_summary(
            chart_id,
            ayanamsa_value_deg=chart.ephemeris.ayanamsa_value,
            lagna_rashi=chart.ascendant.rashi,
            lagna_degree=chart.ascendant.rashi_degree,
            moon_nakshatra=chart.panchanga.nakshatra.nakshatra,
        )

        await self._house_repo.replace_for_chart(chart_id, chart.houses)

        await self._planet_position_repo.replace_for_chart(
            chart_id,
            chart.planets,
            ayanamsa_value_deg=chart.ephemeris.ayanamsa_value,
        )

        return chart_id
