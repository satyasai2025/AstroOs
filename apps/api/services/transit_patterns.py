"""
AstroOS — Transit Pattern Detector

Detects classical Vedic transit patterns at a given moment:

  * Sade Sati        — Saturn through 12th/1st/2nd from natal Moon (~7.5 yr)
  * Ashtama Shani    — Saturn in 8th from natal Moon
  * Planet returns   — Transiting planet within orb of its own natal position
  * Transit aspects  — Graha drishti (Vedic house-based aspect) between a
                        transiting planet and each natal planet, using the
                        same rule table as services/aspect_engine.py's natal
                        aspects: every planet aspects the 7th house from its
                        position; Mars additionally aspects the 4th/8th,
                        Jupiter the 5th/9th, Saturn the 3rd/10th, Rahu/Ketu
                        the 5th/9th (by the same tradition aspect_engine.py
                        already follows). Fixed 2026-08-06: this previously
                        used Western/Ptolemaic angles (conjunction/sextile/
                        square/trine/opposition at 0/60/90/120/180°), which
                        aren't a Vedic concept and gave every planet the same
                        aspect set regardless of which graha it was — unlike
                        the natal aspects elsewhere in this app, which
                        already used real graha drishti. This detector now
                        reuses aspect_engine.py's own house-offset rule table
                        so transit and natal aspects are the same system.

All calculations are deterministic — no AI, no external API calls.
Average daily-motion approximations (from classical constants) are used for
date estimates; the detection itself uses exact sidereal ephemeris positions.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.services.aspect_engine import SPECIAL_ASPECTS, UNIVERSAL_ASPECT, AspectEngine
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_rashi,
)
from packages.shared.degrees import shorter_arc_distance as _angular_distance
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset

_RASHI_LIST = [r.value for r in Rashi]

_ALL_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

# Average daily motion in degrees per day (approximate classical values).
# Used only for date estimation, never for detection itself.
_AVG_DAILY_MOTION: dict[str, float] = {
    "sun":     0.9856,
    "moon":    13.176,
    "mars":    0.524,
    "mercury": 1.383,
    "jupiter": 0.083,
    "venus":   1.603,
    "saturn":  0.033,
    "rahu":    0.053,   # mean motion, treated as forward for magnitude
    "ketu":    0.053,
}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _house_from_reference(ref_rashi: str, target_rashi: str) -> int:
    """House number (1-12) of `target_rashi` counted from `ref_rashi`."""
    ref_idx = _RASHI_LIST.index(ref_rashi)
    tgt_idx = _RASHI_LIST.index(target_rashi)
    return house_offset(ref_idx, tgt_idx)


def _jd_to_datetime(jd: float) -> datetime:
    """
    Convert a Julian Day Number (UT) to a UTC-aware datetime.
    Uses a simple offset from J2000.0 — sufficient for date-level precision.
    """
    J2000_JD = 2451545.0
    J2000_DT = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    delta_days = jd - J2000_JD
    return J2000_DT + timedelta(days=delta_days)


# ── Domain result types ──────────────────────────────────────────────────────


class SadeSatiInfo:
    """Sade Sati status at the transit moment."""
    __slots__ = ("is_active", "phase", "house_from_moon", "start_date", "end_date")

    def __init__(
        self,
        is_active: bool = False,
        phase: Optional[str] = None,
        house_from_moon: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        self.is_active = is_active
        self.phase = phase          # "first_year" | "peak" | "third_year" | None
        self.house_from_moon = house_from_moon
        self.start_date = start_date
        self.end_date = end_date


class AshtamaShaniInfo:
    """Ashtama Shani status at the transit moment."""
    __slots__ = ("is_active", "house_from_moon", "start_date", "end_date")

    def __init__(
        self,
        is_active: bool = False,
        house_from_moon: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        self.is_active = is_active
        self.house_from_moon = house_from_moon
        self.start_date = start_date
        self.end_date = end_date


class ReturnPeriodInfo:
    """Whether a transiting planet is near its own natal position."""
    __slots__ = (
        "planet", "natal_longitude", "transit_longitude",
        "orb", "is_at_return", "estimated_return_date",
    )

    def __init__(
        self,
        planet: str,
        natal_longitude: float,
        transit_longitude: float,
        orb: float = 0.0,
        is_at_return: bool = False,
        estimated_return_date: Optional[date] = None,
    ):
        self.planet = planet
        self.natal_longitude = natal_longitude
        self.transit_longitude = transit_longitude
        self.orb = orb
        self.is_at_return = is_at_return
        self.estimated_return_date = estimated_return_date


class TransitAspectInfo:
    """An aspect between a transiting planet and a natal planet."""
    __slots__ = (
        "aspect_type", "transiting_planet", "natal_planet",
        "orb", "transit_longitude", "natal_longitude",
    )

    def __init__(
        self,
        aspect_type: str,
        transiting_planet: str,
        natal_planet: str,
        orb: float = 0.0,
        transit_longitude: float = 0.0,
        natal_longitude: float = 0.0,
    ):
        self.aspect_type = aspect_type
        self.transiting_planet = transiting_planet
        self.natal_planet = natal_planet
        self.orb = orb
        self.transit_longitude = transit_longitude
        self.natal_longitude = natal_longitude


class TransitPatternResult:
    """Aggregated transit pattern detection for one moment."""
    __slots__ = (
        "transit_datetime_utc", "natal_moon_rashi",
        "sade_sati", "ashtama_shani", "return_periods", "aspects",
    )

    def __init__(
        self,
        transit_datetime_utc: datetime,
        natal_moon_rashi: str,
        sade_sati: Optional[SadeSatiInfo] = None,
        ashtama_shani: Optional[AshtamaShaniInfo] = None,
        return_periods: Optional[list[ReturnPeriodInfo]] = None,
        aspects: Optional[list[TransitAspectInfo]] = None,
    ):
        self.transit_datetime_utc = transit_datetime_utc
        self.natal_moon_rashi = natal_moon_rashi
        self.sade_sati = sade_sati or SadeSatiInfo()
        self.ashtama_shani = ashtama_shani or AshtamaShaniInfo()
        self.return_periods = return_periods or []
        self.aspects = aspects or []


# ── Detector ─────────────────────────────────────────────────────────────────


class TransitPatternDetector:
    """
    Detects classical Vedic transit patterns.

    Stateless — construct once with an EphemerisWrapper, then call
    detect_patterns() with any (natal_chart, transit_datetime) pair.
    """

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    # -- Internal position helpers -------------------------------------------

    def _sidereal_lon(self, planet: str, jd: float) -> float:
        """Sidereal longitude of a planet at Julian Day *jd*."""
        trop = self._wrapper.get_planet_position(planet, jd)
        ayan = self._wrapper.get_ayanamsa(jd)
        return self._wrapper.to_sidereal(trop.longitude, ayan)

    def _transit_rashi(self, planet: str, jd: float) -> str:
        """Sidereal rashi of a planet at *jd*."""
        return longitude_to_rashi(self._sidereal_lon(planet, jd))[0]

    def _natal_lon(self, chart: D1Chart, planet: str) -> Optional[float]:
        """Return the natal sidereal longitude of *planet*, or None."""
        for p in chart.planets:
            if p.planet == planet:
                return p.sidereal_longitude
        return None

    # -- Sign-duration estimation --------------------------------------------

    def _days_in_sign(self, planet: str, jd: float) -> Optional[tuple[float, float]]:
        """
        Estimate (days_since_entry, days_until_exit) for *planet*'s current
        sign, using average daily motion.  Returns None if no motion data.
        """
        daily = _AVG_DAILY_MOTION.get(planet)
        if not daily:
            return None

        sid_lon = self._sidereal_lon(planet, jd)
        current = sid_lon % 360.0
        rashi_idx = int(current / 30.0)  # 0-11
        sign_start = rashi_idx * 30.0
        sign_end = sign_start + 30.0
        pos_in_sign = current - sign_start

        return (pos_in_sign / daily, (sign_end - current) / daily)

    def _estimate_sign_dates(
        self, planet: str, target_rashi: str, jd: float
    ) -> tuple[Optional[date], Optional[date]]:
        """
        Estimate the entry and exit dates of *planet*'s current transit
        through *target_rashi*.  Returns (entry_date, exit_date).

        If the planet is not in *target_rashi* at *jd*, returns (None, None).
        """
        current_rashi = self._transit_rashi(planet, jd)
        if current_rashi != target_rashi:
            return None, None

        pair = self._days_in_sign(planet, jd)
        if pair is None:
            return None, None
        since_entry, until_exit = pair

        now_dt = _jd_to_datetime(jd)
        entry_dt = now_dt - timedelta(days=since_entry)
        exit_dt = now_dt + timedelta(days=until_exit)
        return entry_dt.date(), exit_dt.date()

    # -- Pattern detectors ---------------------------------------------------

    def detect_sade_sati(self, natal_chart: D1Chart, jd: float) -> SadeSatiInfo:
        """
        Detect Sade Sati — Saturn transiting 12th, 1st, or 2nd from natal Moon.

        Phase mapping:
          house 12 → "first_year"   (Saturn approaching Moon)
          house 1  → "peak"         (Saturn conjunct Moon sign)
          house 2  → "third_year"   (Saturn departing)
        """
        moon_rashi = next(p.rashi for p in natal_chart.planets if p.planet == "moon")
        sat_rashi = self._transit_rashi("saturn", jd)
        house = _house_from_reference(moon_rashi, sat_rashi)
        active = house in (12, 1, 2)

        phase = None
        if active:
            phase = {12: "first_year", 1: "peak", 2: "third_year"}[house]

        entry_date = None
        exit_date = None
        if active:
            # Sade Sati starts when Saturn enters the 12th from Moon
            rashi_12 = _RASHI_LIST[(_RASHI_LIST.index(moon_rashi) + 11) % 12]
            e, x = self._estimate_sign_dates("saturn", rashi_12, jd)
            if e is not None:
                entry_date = e
            # Sade Sati ends when Saturn leaves the 2nd from Moon
            rashi_2 = _RASHI_LIST[(_RASHI_LIST.index(moon_rashi) + 1) % 12]
            _, x = self._estimate_sign_dates("saturn", rashi_2, jd)
            if x is not None:
                exit_date = x

        return SadeSatiInfo(
            is_active=active,
            phase=phase,
            house_from_moon=house,
            start_date=entry_date,
            end_date=exit_date,
        )

    def detect_ashtama_shani(self, natal_chart: D1Chart, jd: float) -> AshtamaShaniInfo:
        """
        Detect Ashtama Shani — Saturn transiting the 8th house from natal Moon.
        """
        moon_rashi = next(p.rashi for p in natal_chart.planets if p.planet == "moon")
        sat_rashi = self._transit_rashi("saturn", jd)
        house = _house_from_reference(moon_rashi, sat_rashi)
        active = house == 8

        entry_date = None
        exit_date = None
        if active:
            rashi_8 = _RASHI_LIST[(_RASHI_LIST.index(moon_rashi) + 7) % 12]
            e, x = self._estimate_sign_dates("saturn", rashi_8, jd)
            entry_date = e
            exit_date = x

        return AshtamaShaniInfo(
            is_active=active,
            house_from_moon=house,
            start_date=entry_date,
            end_date=exit_date,
        )

    def detect_return_periods(
        self, natal_chart: D1Chart, jd: float, orb: float = 3.0
    ) -> list[ReturnPeriodInfo]:
        """
        Detect planetary returns — transit planet within *orb* degrees of
        its own natal position.

        Returns one entry per graha with the current angular separation and
        an estimated date of next exact return.
        """
        results: list[ReturnPeriodInfo] = []

        for planet in _ALL_PLANETS:
            natal_lon = self._natal_lon(natal_chart, planet)
            if natal_lon is None:
                continue

            transit_lon = self._sidereal_lon(planet, jd)
            angular = _angular_distance(transit_lon, natal_lon)
            is_exact = angular <= orb

            # Estimate next exact return date
            est: Optional[date] = None
            daily = _AVG_DAILY_MOTION.get(planet)
            if daily:
                # Degrees ahead (in the direction of motion) to reach natal
                delta = (natal_lon - transit_lon) % 360.0
                days = delta / daily
                est = _jd_to_datetime(jd + days).date()

            results.append(ReturnPeriodInfo(
                planet=planet,
                natal_longitude=natal_lon,
                transit_longitude=transit_lon,
                orb=angular,
                is_at_return=is_exact,
                estimated_return_date=est,
            ))

        return results

    def detect_aspects(
        self, natal_chart: D1Chart, jd: float, orb: float = 6.0
    ) -> list[TransitAspectInfo]:
        """
        Detect Vedic graha drishti (house-based aspects) cast by each
        transiting planet onto each natal planet.

        Same rule table as aspect_engine.py's natal aspects: every planet
        aspects the 7th house from its own position (UNIVERSAL_ASPECT);
        Mars/Jupiter/Saturn/Rahu/Ketu additionally aspect the house offsets
        in SPECIAL_ASPECTS. Here "its own position" is the transiting
        planet's current rashi, and the aspected rashi is checked against
        each natal planet's natal rashi — a cross-chart version of the same
        whole-sign house-counting aspect_engine.py already uses within one
        chart.

        *orb* is applied to how close the transiting planet is to the exact
        aspected-house cusp (0° = planet is exactly at its own rashi's
        start once counted onto the target sign), the same "orb within the
        aspected sign" convention aspect_engine.py uses, not a Ptolemaic
        angle orb — there's no Western angle involved.

        Self-aspects (same planet transit ↔ natal) are excluded — they are
        covered by detect_return_periods instead. Conjunction (offset 1,
        same house) is not a house *aspect* in the classical sense and is
        likewise left to detect_return_periods, matching aspect_engine.py's
        own UNIVERSAL_ASPECT/SPECIAL_ASPECTS tables, which never include
        offset 1 either.
        """
        aspects: list[TransitAspectInfo] = []
        classify = AspectEngine().classify

        for tp in _ALL_PLANETS:
            t_lon = self._sidereal_lon(tp, jd)
            t_rashi, t_rashi_deg = longitude_to_rashi(t_lon)
            t_rashi_idx = _RASHI_LIST.index(t_rashi)

            aspect_offsets = {UNIVERSAL_ASPECT} | SPECIAL_ASPECTS.get(tp, set())

            for offset in aspect_offsets:
                aspected_idx = (t_rashi_idx + offset - 1) % 12
                aspected_rashi = _RASHI_LIST[aspected_idx]
                aspect_type = classify(offset)

                for np in _ALL_PLANETS:
                    if tp == np:
                        continue

                    n_lon = self._natal_lon(natal_chart, np)
                    if n_lon is None:
                        continue

                    n_rashi, n_rashi_deg = longitude_to_rashi(n_lon)
                    if n_rashi != aspected_rashi:
                        continue

                    # Orb within the aspected sign — same convention as
                    # aspect_engine.py's compute(): how far the transiting
                    # planet's own in-sign degree is from the natal planet's
                    # in-sign degree, using the shorter of the two possible
                    # wrap-arounds within a 30° sign.
                    asp_orb = abs(t_rashi_deg - n_rashi_deg)
                    if asp_orb > 15:
                        asp_orb = 30 - asp_orb
                    if asp_orb > orb:
                        continue

                    aspects.append(TransitAspectInfo(
                        aspect_type=aspect_type,
                        transiting_planet=tp,
                        natal_planet=np,
                        orb=round(asp_orb, 4),
                        transit_longitude=t_lon,
                        natal_longitude=n_lon,
                    ))

        return aspects

    # -- Main entry point ----------------------------------------------------

    def detect_patterns(
        self,
        natal_chart: D1Chart,
        transit_datetime_utc: datetime,
        aspect_orb: float = 6.0,
        return_orb: float = 3.0,
    ) -> TransitPatternResult:
        """
        All classical transit patterns for *transit_datetime_utc* against
        *natal_chart*.

        Args:
            natal_chart: Pre-computed natal D1 chart.
            transit_datetime_utc: The moment to check.
            aspect_orb: Max orb in degrees for aspect detection (default 6).
            return_orb: Max orb in degrees for return detection (default 3).

        Returns:
            TransitPatternResult with sade_sati, ashtama_shani,
            return_periods, and aspects.
        """
        jd = datetime_to_jd(transit_datetime_utc)

        moon_rashi = next(p.rashi for p in natal_chart.planets if p.planet == "moon")

        return TransitPatternResult(
            transit_datetime_utc=transit_datetime_utc,
            natal_moon_rashi=moon_rashi,
            sade_sati=self.detect_sade_sati(natal_chart, jd),
            ashtama_shani=self.detect_ashtama_shani(natal_chart, jd),
            return_periods=self.detect_return_periods(natal_chart, jd, orb=return_orb),
            aspects=self.detect_aspects(natal_chart, jd, orb=aspect_orb),
        )
