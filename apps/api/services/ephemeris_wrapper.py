"""
AstroOS — Swiss Ephemeris Wrapper (Task 3)

Full Vedic astrology calculation wrapper around pyswisseph.

Features:
  - Planet Positions (all 9 Grahas including Rahu/Ketu)
  - Ascendant (Lagna)
  - House Cusps (Whole Sign and Placidus)
  - Nakshatra and Pada for any longitude
  - Retrograde detection
  - Combustion detection
  - Tithi (lunar day)
  - Yoga (Sun+Moon sum)
  - Karana (half-tithi)
  - Vara (weekday)
  - Ayanamsa calculation

All calculations are deterministic given the same inputs.
All returned objects are frozen dataclasses (immutable).
"""

import logging
import math
import threading
from datetime import datetime, timezone
from typing import Optional

import swisseph as swe

from apps.api.domain.ephemeris import (
    Ascendant,
    EphemerisResult,
    HouseCusp,
    KaranaInfo,
    NakshatraInfo,
    PanchangaResult,
    PlanetPosition,
    SiderealPosition,
    TithiInfo,
    VaraInfo,
    YogaInfo,
    DignityType,
)
from packages.shared.constants import (
    DEGREES_PER_NAKSHATRA,
    DEGREES_PER_RASHI,
    PADAS_PER_NAKSHATRA,
    SWEPH_PLANET_IDS,
    TOTAL_NAKSHATRAS,
)
from packages.shared.dignity import compute_dignity_value
from packages.shared.enums import AyanamsaSystem, Graha, Nakshatra, Rashi

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RASHI_LIST: list[str] = [r.value for r in Rashi]
_NAKSHATRA_LIST: list[str] = [n.value for n in Nakshatra]

_NAKSHATRA_LORDS: list[str] = [
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter",
    "saturn", "mercury", "ketu", "venus", "sun", "moon", "mars",
    "rahu", "jupiter", "saturn", "mercury", "ketu", "venus", "sun",
    "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
]

_YOGA_NAMES: list[str] = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shula", "Ganda", "Vriddhi",
    "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
    "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti",
]

_KARANA_NAMES: list[str] = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    # Fixed karanas
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
]

_FIXED_KARANAS = {"Shakuni", "Chatushpada", "Naga", "Kimstughna"}

_VARA_NAMES: list[str] = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday",
]

_VARA_LORDS: list[str] = [
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
]

# Combustion orb limits (degrees) from Sun — classical Vedic values
_COMBUSTION_ORBS: dict[str, float] = {
    "moon":    12.0,
    "mars":     17.0,
    "mercury":  14.0,   # 12° when direct
    "jupiter":  11.0,
    "venus":    10.0,
    "saturn":   15.0,
}

# Ayanamsa IDs for pyswisseph
_AYANAMSA_IDS: dict[str, int] = {
    AyanamsaSystem.LAHIRI.value:         swe.SIDM_LAHIRI,
    AyanamsaSystem.KRISHNAMURTI.value:   swe.SIDM_KRISHNAMURTI,
    AyanamsaSystem.RAMAN.value:          swe.SIDM_RAMAN,
    AyanamsaSystem.YUKTESHWAR.value:     swe.SIDM_YUKTESHWAR,
    AyanamsaSystem.FAGAN_BRADLEY.value:  swe.SIDM_FAGAN_BRADLEY,
    AyanamsaSystem.TRUE_CHITRA.value:    swe.SIDM_TRUE_CITRA,
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _normalize(deg: float) -> float:
    """Normalise any degree value to [0, 360)."""
    return deg % 360.0


def datetime_to_jd(dt: datetime) -> float:
    """
    Convert a UTC-aware datetime to Julian Day Number.

    Swiss Ephemeris expects Universal Time (UT) which is essentially UTC
    for dates after 1972. Pre-1972 dates require ΔT correction — not
    implemented here; use swe.utc_to_jd for those.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC expected)")
    utc = dt.astimezone(timezone.utc)
    jd, _ = swe.utc_to_jd(
        utc.year, utc.month, utc.day,
        utc.hour, utc.minute, utc.second + utc.microsecond / 1e6,
        swe.GREG_CAL,
    )
    return jd


def longitude_to_rashi(lon: float) -> tuple[str, float]:
    """
    Convert a sidereal ecliptic longitude to (rashi_name, degrees_in_rashi).

    Args:
        lon: Sidereal longitude in degrees [0, 360)

    Returns:
        Tuple of (Rashi enum value string, position within rashi [0, 30))
    """
    lon = _normalize(lon)
    rashi_index = int(lon / DEGREES_PER_RASHI)
    rashi_deg = lon - rashi_index * DEGREES_PER_RASHI
    return _RASHI_LIST[rashi_index], rashi_deg


def longitude_to_nakshatra(lon: float) -> NakshatraInfo:
    """
    Convert a sidereal ecliptic longitude to a NakshatraInfo.

    Each nakshatra spans 13°20' = 360/27 degrees.
    Each pada spans 3°20' = 360/108 degrees.
    """
    lon = _normalize(lon)
    nak_index = int(lon / DEGREES_PER_NAKSHATRA)
    nak_deg = lon - nak_index * DEGREES_PER_NAKSHATRA
    pada = int(nak_deg / (DEGREES_PER_NAKSHATRA / PADAS_PER_NAKSHATRA)) + 1
    pada = min(pada, 4)  # guard against floating point edge

    deg_in_pada = nak_deg - (pada - 1) * (DEGREES_PER_NAKSHATRA / PADAS_PER_NAKSHATRA)

    return NakshatraInfo(
        nakshatra=_NAKSHATRA_LIST[nak_index],
        nakshatra_number=nak_index + 1,
        pada=pada,
        lord=_NAKSHATRA_LORDS[nak_index],
        degree_in_nakshatra=nak_deg,
        degree_in_pada=deg_in_pada,
    )


def _angular_distance(a: float, b: float) -> float:
    """Shortest angular distance between two longitudes (0–180°)."""
    diff = abs(_normalize(a) - _normalize(b))
    return min(diff, 360.0 - diff)


def _compute_dignity(planet: str, rashi: str, rashi_deg: float) -> Optional[DignityType]:
    """
    Compute classical Vedic dignity for a planet in a sign.

    As of Module 9 Phase 2, this is a thin wrapper over
    packages.shared.dignity.compute_dignity_value() — the actual logic
    was extracted there so GrahaEngine (and, going forward, Saptavargaja
    Bala's divisional-chart dignity) can reuse the same pure function
    instead of a second, separate implementation. Behavior is byte-for-
    byte unchanged; see that module's docstring for the full rationale.
    """
    value = compute_dignity_value(planet, rashi, rashi_deg)
    return DignityType(value) if value is not None else None


# ---------------------------------------------------------------------------
# Core wrapper class
# ---------------------------------------------------------------------------

class EphemerisWrapper:
    """
    Full Swiss Ephemeris calculation wrapper for Vedic astrology.

    Lifecycle:
      - Instantiated exactly ONCE per process and reused for every request
        (enforced by DI — see apps.api.dependencies.get_ephemeris_wrapper).
        pyswisseph's C library holds process-global state (ephemeris file
        path, sidereal mode via swe.set_sid_mode), so re-instantiating this
        class per-request does NOT give request isolation — it only adds
        redundant syscalls while the underlying global state is still shared.
      - set_ayanamsa() must be called before any sidereal calculation.
      - calculate() is the primary entry point.

    Thread-safety:
      - `calculate()` acquires `self._lock` for its full duration, and
        `_calculate_locked()` unconditionally re-runs `swe.set_ephe_path()`
        and `swe.set_sid_mode()` at its start on every call. Both are
        necessary: pyswisseph's C-level state from these calls is
        documented as process-global, but is empirically NOT reliably
        visible across OS threads — a calculation running on a different
        thread than whichever one last called them (e.g. via
        `asyncio.to_thread`, which uses a worker thread pool distinct from
        wherever this wrapper was constructed) can silently lose
        precision, with no exception raised. Re-running both calls is
        cheap and removes the dependency on cross-thread visibility
        entirely, rather than trying to reason about which thread "owns"
        the correct state.
      - Callers on the async side should still run `calculate()` via
        `asyncio.to_thread(...)` so this lock does not block the event
        loop — see the router DI helpers for the required pattern.
    """

    def __init__(self, ephemeris_path: str, ayanamsa: str = AyanamsaSystem.LAHIRI.value) -> None:
        import os
        self._path = os.path.abspath(ephemeris_path)
        self._ayanamsa = ayanamsa
        self._lock = threading.Lock()
        swe.set_ephe_path(self._path)
        self._set_ayanamsa(ayanamsa)

    # ── Ayanamsa ──────────────────────────────────────────────────────────────

    def _set_ayanamsa(self, ayanamsa: str) -> None:
        """Configure the sidereal mode for Swiss Ephemeris."""
        sid_id = _AYANAMSA_IDS.get(ayanamsa, swe.SIDM_LAHIRI)
        swe.set_sid_mode(sid_id, 0, 0)
        self._ayanamsa = ayanamsa

    def get_ayanamsa(self, jd: float) -> float:
        """Return ayanamsa value in degrees for the given Julian Day."""
        return swe.get_ayanamsa_ut(jd)

    # ── Planet positions ───────────────────────────────────────────────────────

    def get_planet_position(self, planet: str, jd: float) -> PlanetPosition:
        """
        Calculate tropical ecliptic position for one Graha.

        Ketu is derived from Rahu (True Node) + 180°.
        """
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED

        if planet == "ketu":
            rahu_pos = self._calc_planet("rahu", jd, flags)
            longitude = _normalize(rahu_pos[0] + 180.0)
            return PlanetPosition(
                planet="ketu",
                longitude=longitude,
                latitude=-rahu_pos[1],
                distance_au=rahu_pos[2],
                speed_deg_per_day=rahu_pos[3],
                is_retrograde=True,  # Ketu is always considered retrograde
            )

        xx = self._calc_planet(planet, jd, flags)
        return PlanetPosition(
            planet=planet,
            longitude=_normalize(xx[0]),
            latitude=xx[1],
            distance_au=xx[2],
            speed_deg_per_day=xx[3],
            is_retrograde=xx[3] < 0,
        )

    def _calc_planet(self, planet: str, jd: float, flags: int) -> tuple:
        """Internal: call swe.calc_ut with the correct planet ID."""
        planet_id = SWEPH_PLANET_IDS[planet]
        xx, retflag = swe.calc_ut(jd, planet_id, flags)
        if retflag < 0:
            raise RuntimeError(
                f"Swiss Ephemeris calculation error for {planet}: retflag={retflag}"
            )
        return xx

    def get_all_planet_positions(self, jd: float) -> dict[str, PlanetPosition]:
        """Calculate tropical positions for all 9 Grahas."""
        return {
            planet: self.get_planet_position(planet, jd)
            for planet in SWEPH_PLANET_IDS
        }

    # ── Sunrise / sunset (Module 9 Phase 0 — Foundation Extension) ────────────
    #
    # Added specifically for Kala Bala's Nathonnata/Ayana/Tribhaga
    # sub-components (Shadbala, Module 9), which need precise day/night
    # timing relative to sunrise/sunset, not just a rough estimate.

    def get_sunrise_sunset(
        self,
        jd: float,
        latitude: float,
        longitude: float,
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Sunrise and sunset Julian Days (UT) bracketing the given moment,
        at the given location.

        Searches for sunrise starting one day before `jd` (safe margin —
        the solar day is ~1 day everywhere except near the poles), then
        searches for sunset starting FROM that sunrise result — not from
        the same starting point again — so the returned sunset is the one
        immediately following that sunrise (the same local day), not the
        previous day's sunset. Searching both from the same start point
        is a common mistake here: rise_trans returns the NEXT event at or
        after the given time, and starting sunset's search too early can
        return a sunset from before the sunrise it's supposed to pair with.

        Returns (None, None) if the location is circumpolar at this date
        (no sunrise/sunset — polar day or night) rather than raising, so
        callers can degrade gracefully (e.g. Kala Bala components that
        need this can report "not computable at this latitude" instead of
        crashing).
        """
        geopos = (longitude, latitude, 0.0)

        rise_result, rise_data = swe.rise_trans(jd - 1.0, swe.SUN, swe.CALC_RISE, geopos)
        if rise_result != 0:
            return None, None
        sunrise_jd = rise_data[0]

        set_result, set_data = swe.rise_trans(sunrise_jd, swe.SUN, swe.CALC_SET, geopos)
        if set_result != 0:
            return sunrise_jd, None
        sunset_jd = set_data[0]

        return sunrise_jd, sunset_jd

    def get_declination(self, planet: str, jd: float) -> float:
        """
        Equatorial declination (degrees) for a Graha — needed for Ayana
        Bala (Shadbala, Module 9). Ketu is derived from Rahu (True Node)
        with declination sign flipped, mirroring get_planet_position's
        existing Ketu-from-Rahu convention.
        """
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_EQUATORIAL

        if planet == "ketu":
            rahu_id = SWEPH_PLANET_IDS["rahu"]
            xx, retflag = swe.calc_ut(jd, rahu_id, flags)
            if retflag < 0:
                raise RuntimeError(f"Swiss Ephemeris calculation error for ketu: retflag={retflag}")
            return -xx[1]

        planet_id = SWEPH_PLANET_IDS[planet]
        xx, retflag = swe.calc_ut(jd, planet_id, flags)
        if retflag < 0:
            raise RuntimeError(f"Swiss Ephemeris calculation error for {planet}: retflag={retflag}")
        return xx[1]  # xx[1] is declination when FLG_EQUATORIAL is set

    # ── Ascendant and houses ───────────────────────────────────────────────────

    def get_ascendant_and_cusps(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        house_system: str = "W",   # W = Whole Sign
    ) -> tuple[float, list[float]]:
        """
        Calculate ascendant and 12 house cusps.

        Returns:
            (ascendant_longitude, [cusp1, cusp2, ..., cusp12])
            All values are tropical ecliptic longitudes.

        House system codes (single char):
            'W' = Whole Sign, 'P' = Placidus, 'K' = Koch, 'E' = Equal
        """
        cusps, ascmc = swe.houses(jd, latitude, longitude, house_system.encode())
        # pyswisseph returns cusps as a 12-element 0-indexed tuple: cusps[0]=H1 … cusps[11]=H12
        # ascmc[0] = Ascendant (same as cusps[0] for most systems)
        asc = ascmc[0]
        house_cusps = list(cusps[0:12])  # 12 house cusps, 0-indexed
        return asc, house_cusps

    # ── Sidereal conversion ────────────────────────────────────────────────────

    def to_sidereal(self, tropical_lon: float, ayanamsa_val: float) -> float:
        """Subtract ayanamsa to convert tropical → sidereal longitude."""
        return _normalize(tropical_lon - ayanamsa_val)

    # ── Combustion ────────────────────────────────────────────────────────────

    def is_combust(
        self,
        planet: str,
        planet_lon: float,
        sun_lon: float,
    ) -> tuple[bool, Optional[float]]:
        """
        Check if a planet is combust (within combustion orb of Sun).

        Returns (is_combust, orb_degrees).
        Sun and nodes are never combust.
        """
        if planet in ("sun", "rahu", "ketu"):
            return False, None
        orb_limit = _COMBUSTION_ORBS.get(planet)
        if orb_limit is None:
            return False, None
        orb = _angular_distance(planet_lon, sun_lon)
        return orb <= orb_limit, round(orb, 6)

    # ── Panchanga ─────────────────────────────────────────────────────────────

    def get_tithi(self, moon_lon: float, sun_lon: float) -> TithiInfo:
        """
        Calculate the lunar Tithi.

        Tithi = (Moon longitude − Sun longitude) / 12°
        """
        diff = _normalize(moon_lon - sun_lon)
        tithi_number = int(diff / 12.0) + 1   # 1–30
        completion = ((diff % 12.0) / 12.0) * 100.0

        if tithi_number <= 15:
            paksha = "shukla"
            display_number = tithi_number
        else:
            paksha = "krishna"
            display_number = tithi_number - 15

        _TITHI_NAMES = [
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya",
        ]
        name = _TITHI_NAMES[display_number - 1]

        return TithiInfo(
            number=tithi_number,
            name=name,
            paksha=paksha,
            completion_percent=round(completion, 4),
        )

    def get_yoga(self, moon_sid_lon: float, sun_sid_lon: float) -> YogaInfo:
        """
        Calculate Nithya Yoga.

        Yoga = (Sun sidereal + Moon sidereal) mod 360 / (360/27)
        """
        combined = _normalize(moon_sid_lon + sun_sid_lon)
        yoga_index = int(combined / DEGREES_PER_NAKSHATRA)
        completion = ((combined % DEGREES_PER_NAKSHATRA) / DEGREES_PER_NAKSHATRA) * 100.0

        return YogaInfo(
            number=yoga_index + 1,
            name=_YOGA_NAMES[yoga_index],
            completion_percent=round(completion, 4),
        )

    def get_karana(self, tithi_info: TithiInfo) -> KaranaInfo:
        """
        Calculate Karana (half-tithi).

        The first Karana of Shukla Pratipada is Kimstughna (fixed).
        Then 7 movable karanas repeat 8 times (karanas 2–57).
        The last 4 are fixed: Shakuni, Chatushpada, Naga, Kimstughna.
        """
        tithi_num = tithi_info.number
        completion = tithi_info.completion_percent

        # Each tithi has 2 karanas
        # First half = karana at (tithi-1)*2 + 1, second = (tithi-1)*2 + 2
        half = 0 if completion < 50 else 1
        karana_seq = (tithi_num - 1) * 2 + half  # 0-indexed, 0–59

        if karana_seq == 0:
            name = "Kimstughna"
            is_fixed = True
        elif 1 <= karana_seq <= 56:
            movable_index = (karana_seq - 1) % 7
            _MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
            name = _MOVABLE[movable_index]
            is_fixed = False
        else:
            fixed_idx = karana_seq - 57
            _FIXED = ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]
            name = _FIXED[min(fixed_idx, 3)]
            is_fixed = True

        return KaranaInfo(
            number=karana_seq + 1,
            name=name,
            is_fixed=is_fixed,
        )

    def get_vara(self, jd: float) -> VaraInfo:
        """
        Calculate the Vedic weekday (Vara).

        JD 0.0 = Monday noon. Day starts at local sunrise in classical Vedic,
        but here we use the calendar day (UTC midnight-based).
        Julian Day modulo 7 gives: 0=Monday … 6=Sunday in Swiss Ephemeris.
        We re-map to Sunday=0 … Saturday=6.
        """
        # swe.day_of_week returns 0=Monday…6=Sunday
        dow_swe = swe.day_of_week(jd)
        # Convert to Sunday=0 … Saturday=6
        dow_sun_first = (dow_swe + 1) % 7

        return VaraInfo(
            number=dow_sun_first,
            name=_VARA_NAMES[dow_sun_first],
            lord=_VARA_LORDS[dow_sun_first],
        )

    # ── Full calculation ───────────────────────────────────────────────────────

    def calculate(
        self,
        dt: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = AyanamsaSystem.LAHIRI.value,
        house_system: str = "W",
    ) -> EphemerisResult:
        """
        Perform a full ephemeris calculation for a given moment and location.

        Public entry point — acquires `self._lock` for the entire duration
        of the calculation so that concurrent calls (e.g. two requests with
        different ayanamsas) cannot interleave the check-set-calculate
        sequence and corrupt each other's results via pyswisseph's
        process-global sidereal mode.

        Call this via `asyncio.to_thread(wrapper.calculate, ...)` from async
        route handlers — it is a blocking call and will hold the lock for
        its full duration.

        Args:
            dt: UTC-aware datetime of the birth/event.
            latitude: Geographic latitude in decimal degrees (+N, -S).
            longitude: Geographic longitude in decimal degrees (+E, -W).
            ayanamsa: Ayanamsa system key (default: Lahiri).
            house_system: Swiss Ephemeris house system code (default: W = Whole Sign).

        Returns:
            EphemerisResult with all positions and panchanga elements.
        """
        with self._lock:
            return self._calculate_locked(dt, latitude, longitude, ayanamsa, house_system)

    def _calculate_locked(
        self,
        dt: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str,
        house_system: str,
    ) -> EphemerisResult:
        """
        Unlocked calculation body. Only call while holding `self._lock` —
        use `calculate()` instead of calling this directly.

        Root-cause fix (found via live smoke testing, reproduced and
        isolated in isolation — see tests/integration/
        test_ephemeris_wrapper_concurrency.py): pyswisseph's
        `swe.set_ephe_path()` and `swe.set_sid_mode()` are documented as
        setting process-global C state, but empirically that state is NOT
        reliably visible to a thread other than the one that called them.
        `__init__` calls both exactly once, from whichever thread
        constructs this wrapper (normally the main thread at process
        startup) — every real calculation, though, runs via
        `asyncio.to_thread(...)` on a worker thread from Python's default
        executor pool, which is a DIFFERENT OS thread. Empirically, a
        calculation from such a worker thread that never re-establishes
        this state itself silently loses precision (in one isolated
        reproduction, by ~0.88 degrees — nowhere near acceptable for real
        use) even though nothing raises an error. Both calls are cheap
        (a path string assignment and a mode flag), so both are redone
        unconditionally at the top of every locked calculation rather than
        only when `ayanamsa` changes — the previous conditional-only-on-
        change logic is exactly what let a fresh worker thread's first
        calculation silently skip re-establishing this state.
        """
        swe.set_ephe_path(self._path)
        self._set_ayanamsa(ayanamsa)

        jd = datetime_to_jd(dt)
        ayanamsa_val = self.get_ayanamsa(jd)

        # ── Tropical positions ────────────────────────────────────────────────
        tropical_positions = self.get_all_planet_positions(jd)
        asc_tropical, cusp_tropicals = self.get_ascendant_and_cusps(
            jd, latitude, longitude, house_system
        )

        # ── Sidereal ascendant ────────────────────────────────────────────────
        asc_sid = self.to_sidereal(asc_tropical, ayanamsa_val)
        asc_rashi, asc_rashi_deg = longitude_to_rashi(asc_sid)
        asc_nak = longitude_to_nakshatra(asc_sid)

        ascendant = Ascendant(
            longitude=asc_tropical,
            sidereal_longitude=asc_sid,
            rashi=asc_rashi,
            rashi_degree=asc_rashi_deg,
            nakshatra=asc_nak.nakshatra,
            pada=asc_nak.pada,
        )

        # ── Sidereal house cusps ──────────────────────────────────────────────
        # In Whole Sign, house 1 = Lagna sign, each subsequent sign = next house
        if house_system.upper() == "W":
            lagna_rashi_index = _RASHI_LIST.index(asc_rashi)
            house_cusps = [
                HouseCusp(
                    house_number=i + 1,
                    longitude=cusp_tropicals[i] if i < len(cusp_tropicals) else 0.0,
                    sidereal_longitude=_normalize(
                        (lagna_rashi_index + i) * DEGREES_PER_RASHI
                    ),
                    rashi=_RASHI_LIST[(lagna_rashi_index + i) % 12],
                )
                for i in range(12)
            ]
        else:
            house_cusps = [
                HouseCusp(
                    house_number=i + 1,
                    longitude=cusp_tropicals[i],
                    sidereal_longitude=self.to_sidereal(cusp_tropicals[i], ayanamsa_val),
                    rashi=longitude_to_rashi(
                        self.to_sidereal(cusp_tropicals[i], ayanamsa_val)
                    )[0],
                )
                for i in range(12)
            ]

        # ── Sun tropical longitude for combustion ─────────────────────────────
        sun_tropical = tropical_positions["sun"].longitude

        # ── Sidereal planet positions ─────────────────────────────────────────
        lagna_rashi_index = _RASHI_LIST.index(asc_rashi)

        sidereal_positions: list[SiderealPosition] = []
        for planet, trop_pos in tropical_positions.items():
            sid_lon = self.to_sidereal(trop_pos.longitude, ayanamsa_val)
            rashi, rashi_deg = longitude_to_rashi(sid_lon)
            nak_info = longitude_to_nakshatra(sid_lon)

            # House number in Whole Sign
            rashi_idx = _RASHI_LIST.index(rashi)
            house_number = ((rashi_idx - lagna_rashi_index) % 12) + 1

            # Combustion (use tropical longitudes for angular distance)
            combust, comb_orb = self.is_combust(
                planet,
                trop_pos.longitude,
                sun_tropical,
            )

            dignity = _compute_dignity(planet, rashi, rashi_deg)

            # Module 9 Phase 0: latitude/distance/speed were already
            # computed into trop_pos above but previously discarded here.
            # Declination needs one additional equatorial-frame call per
            # planet (Ayana Bala, Shadbala).
            declination = self.get_declination(planet, jd)

            sidereal_positions.append(SiderealPosition(
                planet=planet,
                sidereal_longitude=sid_lon,
                rashi=rashi,
                rashi_degree=rashi_deg,
                house_number=house_number,
                nakshatra=nak_info.nakshatra,
                pada=nak_info.pada,
                is_retrograde=trop_pos.is_retrograde,
                is_combust=combust,
                combustion_orb=comb_orb,
                dignity=dignity,
                latitude_deg=trop_pos.latitude,
                distance_au=trop_pos.distance_au,
                speed_deg_per_day=trop_pos.speed_deg_per_day,
                declination_deg=declination,
            ))

        # ── Panchanga ─────────────────────────────────────────────────────────
        moon_pos = next(p for p in sidereal_positions if p.planet == "moon")
        sun_pos = next(p for p in sidereal_positions if p.planet == "sun")

        moon_sid = moon_pos.sidereal_longitude
        sun_sid = sun_pos.sidereal_longitude

        # Tithi uses tropical for moon-sun difference
        moon_tropical = tropical_positions["moon"].longitude
        sun_tropical_for_tithi = tropical_positions["sun"].longitude
        tithi = self.get_tithi(moon_tropical, sun_tropical_for_tithi)

        yoga = self.get_yoga(moon_sid, sun_sid)
        karana = self.get_karana(tithi)
        vara = self.get_vara(jd)
        moon_nak = longitude_to_nakshatra(moon_sid)

        panchanga = PanchangaResult(
            tithi=tithi,
            nakshatra=moon_nak,
            yoga=yoga,
            karana=karana,
            vara=vara,
            julian_day=jd,
            ayanamsa_deg=ayanamsa_val,
        )

        # Module 9 Phase 0: sunrise/sunset for this birth date/location —
        # needed by Kala Bala's Nathonnata/Ayana/Tribhaga sub-components.
        # None/None at circumpolar latitudes (see get_sunrise_sunset).
        sunrise_jd, sunset_jd = self.get_sunrise_sunset(jd, latitude, longitude)
        is_daytime_birth = (
            sunrise_jd is not None and sunset_jd is not None
            and sunrise_jd <= jd <= sunset_jd
        )

        return EphemerisResult(
            julian_day=jd,
            ayanamsa_value=ayanamsa_val,
            ayanamsa_system=ayanamsa,
            ascendant=ascendant,
            house_cusps=house_cusps,
            planet_positions=sidereal_positions,
            panchanga=panchanga,
            sunrise_jd=sunrise_jd,
            sunset_jd=sunset_jd,
            is_daytime_birth=is_daytime_birth if (sunrise_jd is not None and sunset_jd is not None) else None,
        )

    def close(self) -> None:
        """Release C-library resources."""
        swe.close()
