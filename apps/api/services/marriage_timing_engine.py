"""
AstroOS — Marriage Timing Transit Scanner Engine

Implements the Jupiter (Guru) & Saturn (Shani) Transit Activation Scanner
for predicting marriage timing windows, derived from the Swiss Ephemeris
precision algorithms.

Core Algorithm:
  1. Calculate natal chart (Lahiri Ayanamsa) for a given birth data
  2. Locate natal Venus longitude and 7th house cuspal position
  3. Sweep through target age range (e.g., age 20 to 45) in yearly intervals
  4. For each year, find Jupiter's transit position and check for:
     - 1st house (Conjunction)
     - 5th house (Trine / Trinal aspect)
     - 7th house (Opposition)
     - 9th house (Trine / Trinal aspect)
  5. If Jupiter activates natal Venus, check Saturn's position for:
     - Saturn aspecting natal Venus (1st, 3rd, 7th, 10th house aspect)
     - Saturn aspecting 7th house
     - Saturn aspecting transiting Jupiter (delaying results)
  6. Classify result:
     - Probable (Jupiter triggers Venus, no Saturn delay)
     - Delayed (Jupiter triggers Venus, but Saturn obstructs)
     - Not Indicated (No Jupiter activation)
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False

from packages.shared.rashi_offset import house_offset

# ── Constants ──────────────────────────────────────────────────────────────

# Sidereal Zodiac Signs (Rashis), in order. The scan compares natal and
# transiting positions purely by rashi index, so every rashi name entering the
# engine — natal Venus, the 7th cusp, and the transiting grahas — must come
# from this exact vocabulary.
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

RASHI_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}


@dataclass(frozen=True)
class TransitPositions:
    """
    Jupiter and Saturn positions at one scan epoch.

    Supplied by the caller rather than computed here so the scan can run off
    whichever ephemeris the caller already trusts. Both the HTTP path
    (routers/ai_phase_e.py) and the standalone `analyze()` path build this
    from an EphemerisWrapper instance, which applies the request's own
    ayanamsa under the lock that guards pyswisseph's process-global sidereal
    mode.
    """
    julian_day: float
    jupiter_tropical: float
    jupiter_sidereal: float
    saturn_tropical: float
    saturn_sidereal: float


# Maps a scan epoch (UTC) to the Jupiter/Saturn positions at that moment.
TransitPositionProvider = Callable[[datetime], TransitPositions]


@dataclass
class TransitScanResult:
    year: int
    age_at_year: float
    julian_day: float
    jupiter_tropical: float
    jupiter_sidereal: float
    jupiter_rashi: str
    saturn_tropical: float
    saturn_sidereal: float
    saturn_rashi: str
    venus_natal_sidereal: float
    venus_natal_rashi: str
    status: str  # "probable", "delayed", "not_indicated"
    aspect_details: List[str] = field(default_factory=list)
    saturn_obstruction_details: List[str] = field(default_factory=list)


@dataclass
class MarriageTimingResult:
    birth_datetime_utc: str
    subject_name: str
    scan_start_age: int
    scan_end_age: int
    natal_venus_rashi: str
    natal_venus_longitude: float
    natal_seventh_cusp_rashi: str
    total_years_scanned: int
    probable_windows: int
    delayed_windows: int
    scan_results: List[TransitScanResult] = field(default_factory=list)


class MarriageTimingEngine:
    """
    Calculates marriage timing transit windows using Swiss Ephemeris precision.

    Algorithm scans for Jupiter (Guru) activation of natal Venus across 1st, 5th,
    7th, and 9th houses while checking Saturn (Shani) delay/obstruction factors.
    """

    def __init__(self):
        if SWISSEPH_AVAILABLE:
            swe.set_ephe_path(None)  # Use Swiss Ephemeris built-in data
            swe.set_sid_mode(swe.SIDM_LAHIRI)

    @staticmethod
    def _longitude_to_rashi(sidereal_longitude: float) -> str:
        """Convert sidereal longitude to sidereal Rashi."""
        idx = int(sidereal_longitude / 30.0) % 12
        return SIGNS[idx]

    @staticmethod
    def _rashi_index(rashi: str) -> int:
        return SIGNS.index(rashi)

    @staticmethod
    def _calculate_house_from_rashi(from_rashi: str, to_rashi: str) -> int:
        """Calculate house number from one rashi to another (1-indexed)."""
        from_idx = MarriageTimingEngine._rashi_index(from_rashi)
        to_idx = MarriageTimingEngine._rashi_index(to_rashi)
        return house_offset(from_idx, to_idx)

    @staticmethod
    def _is_aspecting_house(aspect_house: int) -> bool:
        """
        Check if a planet aspects a given house.

        Standard Vedic aspects:
        - 1st (Conjunction)
        - 3rd (3rd aspect for Saturn only)
        - 4th (4th aspect for Jupiter only)
        - 5th (5th aspect for Saturn only)
        - 7th (7th aspect - all planets)
        - 9th (9th aspect for Saturn only)
        - 10th (10th aspect for Jupiter only)
        """
        return aspect_house in (1, 7)  # Universal aspects (Jupiter + Saturn)

    @staticmethod
    def _scan_epoch(birth_dt: datetime, target_year: int) -> datetime:
        """
        The moment sampled for a given scan year: noon UT on the birthday
        anniversary. A 29 February birthday falls back to the 28th in common
        years rather than raising.
        """
        last_day = calendar.monthrange(target_year, birth_dt.month)[1]
        return datetime(
            target_year, birth_dt.month, min(birth_dt.day, last_day),
            12, 0, tzinfo=timezone.utc,
        )

    @classmethod
    def scan(
        cls,
        *,
        birth_dt: datetime,
        natal_venus_sidereal: float,
        natal_venus_rashi: str,
        cusp_7_rashi: str,
        transit_positions: TransitPositionProvider,
        scan_start_age: int = 20,
        scan_end_age: int = 45,
        subject_name: str = "",
    ) -> MarriageTimingResult:
        """
        Scan for marriage timing windows from *already computed* natal data.

        This is the engine's core: it owns the Jupiter/Saturn aspect logic and
        nothing else, taking both the natal positions and the per-year transit
        positions from the caller. That keeps a single copy of the astrology
        while letting the HTTP path stay on the same chart (and the same
        ayanamsa) the rest of the request already used.

        Args:
            birth_dt: Timezone-aware UTC birth datetime.
            natal_venus_sidereal: Natal Venus sidereal longitude, degrees.
            natal_venus_rashi: Natal Venus rashi — must be a name from SIGNS.
            cusp_7_rashi: Rashi of the 7th house cusp — must be a name from SIGNS.
            transit_positions: Callable resolving a scan epoch to Jupiter/Saturn positions.
            scan_start_age: First age to scan (inclusive).
            scan_end_age: Last age to scan (inclusive).
            subject_name: Name of the person, for display purposes.

        Returns:
            MarriageTimingResult with one TransitScanResult per scanned year.
        """
        if birth_dt.tzinfo is None:
            raise ValueError("birth_dt must be timezone-aware (UTC expected)")
        birth_dt = birth_dt.astimezone(timezone.utc)

        # An unrecognised rashi would otherwise blow up mid-loop inside
        # _rashi_index; fail before any ephemeris work instead.
        for label, name in (("natal Venus", natal_venus_rashi), ("7th cusp", cusp_7_rashi)):
            if name not in SIGNS:
                raise ValueError(f"Unrecognised {label} rashi '{name}' — expected one of {SIGNS}")
        if scan_end_age < scan_start_age:
            raise ValueError("scan_end_age must not be earlier than scan_start_age")

        venus_rashi = natal_venus_rashi
        scan_results: List[TransitScanResult] = []

        # Scan through target years
        for target_age in range(scan_start_age, scan_end_age + 1):
            epoch = cls._scan_epoch(birth_dt, birth_dt.year + target_age)
            target_year = epoch.year
            positions = transit_positions(epoch)

            target_jd = positions.julian_day
            jupiter_tropical = positions.jupiter_tropical
            jupiter_sidereal = positions.jupiter_sidereal
            jupiter_rashi = cls._longitude_to_rashi(jupiter_sidereal)

            saturn_tropical = positions.saturn_tropical
            saturn_sidereal = positions.saturn_sidereal
            saturn_rashi = cls._longitude_to_rashi(saturn_sidereal)

            # Check Jupiter activation of natal Venus
            jupiter_house_from_venus = cls._calculate_house_from_rashi(venus_rashi, jupiter_rashi)
            jupiter_activates_venus = jupiter_house_from_venus in (1, 5, 7, 9)

            # Check Saturn obstruction factors
            saturn_details = []
            saturn_obstructs = False

            # Saturn aspect on natal Venus
            saturn_house_from_venus = cls._calculate_house_from_rashi(venus_rashi, saturn_rashi)
            if saturn_house_from_venus in (1, 3, 7, 10):
                saturn_obstructs = True
                saturn_details.append(f"Saturn aspects natal Venus (House {saturn_house_from_venus} from Venus)")

            # Saturn aspect on 7th house
            saturn_house_from_7th = cls._calculate_house_from_rashi(cusp_7_rashi, saturn_rashi)
            if saturn_house_from_7th in (1, 3, 7, 10):
                saturn_obstructs = True
                saturn_details.append(f"Saturn aspects 7th house (House {saturn_house_from_7th} from 7th cusp)")

            # Saturn aspect on transiting Jupiter (if Jupiter is activating)
            if jupiter_activates_venus:
                saturn_house_from_jupiter = cls._calculate_house_from_rashi(jupiter_rashi, saturn_rashi)
                if saturn_house_from_jupiter in (1, 3, 7, 10):
                    saturn_obstructs = True
                    saturn_details.append(f"Saturn aspects transiting Jupiter (House {saturn_house_from_jupiter} from Jupiter)")

            # Determine final status
            aspect_details = []
            if jupiter_activates_venus:
                aspect_details.append(f"Jupiter transits House {jupiter_house_from_venus} from natal Venus")
                if saturn_obstructs:
                    status = "delayed"
                else:
                    status = "probable"
            else:
                status = "not_indicated"

            result = TransitScanResult(
                year=target_year,
                age_at_year=float(target_age),
                julian_day=target_jd,
                jupiter_tropical=jupiter_tropical,
                jupiter_sidereal=jupiter_sidereal,
                jupiter_rashi=jupiter_rashi,
                saturn_tropical=saturn_tropical,
                saturn_sidereal=saturn_sidereal,
                saturn_rashi=saturn_rashi,
                venus_natal_sidereal=natal_venus_sidereal,
                venus_natal_rashi=venus_rashi,
                status=status,
                aspect_details=aspect_details,
                saturn_obstruction_details=saturn_details
            )
            scan_results.append(result)

        probable_count = sum(1 for r in scan_results if r.status == "probable")
        delayed_count = sum(1 for r in scan_results if r.status == "delayed")

        return MarriageTimingResult(
            birth_datetime_utc=birth_dt.isoformat(),
            subject_name=subject_name or "Unnamed",
            scan_start_age=scan_start_age,
            scan_end_age=scan_end_age,
            natal_venus_rashi=venus_rashi,
            natal_venus_longitude=natal_venus_sidereal,
            natal_seventh_cusp_rashi=cusp_7_rashi,
            total_years_scanned=len(scan_results),
            probable_windows=probable_count,
            delayed_windows=delayed_count,
            scan_results=scan_results
        )

    @classmethod
    def analyze(
        cls,
        birth_datetime_utc: str,
        birth_latitude: float,
        birth_longitude: float,
        scan_start_age: int = 20,
        scan_end_age: int = 45,
        subject_name: str = ""
    ) -> MarriageTimingResult:
        """
        Standalone entry point: compute the natal figures via a private
        EphemerisWrapper instance (Lahiri, Placidus cusps) and run `scan`
        over them.

        This goes through the same locked, thread-safe EphemerisWrapper
        calculation surface the HTTP path (routers/ai_phase_e.py) already
        uses to drive `scan` — no direct pyswisseph calls here anymore, so
        there is no separate raw-swisseph computation path to keep in sync.

        Args:
            birth_datetime_utc: ISO 8601 birth datetime (UTC)
            birth_latitude: Birth latitude (decimal degrees)
            birth_longitude: Birth longitude (decimal degrees)
            scan_start_age: Start age for scanning (default 20)
            scan_end_age: End age for scanning (default 45)
            subject_name: Name of the person for display purposes

        Returns:
            MarriageTimingResult with detailed scan results
        """
        if not SWISSEPH_AVAILABLE:
            raise RuntimeError("swisseph Python package is required. Install with: pip install swisseph")

        from apps.api.config import get_settings
        from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd

        wrapper = EphemerisWrapper(ephemeris_path=get_settings().EPHEMERIS_PATH)

        birth_dt = datetime.fromisoformat(birth_datetime_utc.replace('Z', '+00:00'))
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=timezone.utc)
        birth_dt = birth_dt.astimezone(timezone.utc)
        birth_jd = datetime_to_jd(birth_dt)

        # Ayanamsa is read per epoch rather than pinned to a J2000 constant:
        # it drifts ~50" a year, so a fixed value misplaces rashi boundaries
        # across a 25-year scan.
        birth_ayanamsa = wrapper.get_ayanamsa(birth_jd)

        # Natal chart, for Venus and the 7th cusp. Placidus houses (standard
        # for timing work).
        _asc_tropical, cusp_tropicals = wrapper.get_ascendant_and_cusps(
            birth_jd, birth_latitude, birth_longitude, house_system="P"
        )

        venus_tropical = wrapper.get_planet_position("venus", birth_jd).longitude
        venus_sidereal = wrapper.to_sidereal(venus_tropical, birth_ayanamsa)

        cusp_7_tropical = cusp_tropicals[6]  # 7th house cusp (0-indexed)
        cusp_7_sidereal = wrapper.to_sidereal(cusp_7_tropical, birth_ayanamsa)

        def _positions(epoch: datetime) -> TransitPositions:
            jd = datetime_to_jd(epoch)
            ayanamsa = wrapper.get_ayanamsa(jd)
            jupiter_tropical = wrapper.get_planet_position("jupiter", jd).longitude
            saturn_tropical = wrapper.get_planet_position("saturn", jd).longitude
            return TransitPositions(
                julian_day=jd,
                jupiter_tropical=jupiter_tropical,
                jupiter_sidereal=wrapper.to_sidereal(jupiter_tropical, ayanamsa),
                saturn_tropical=saturn_tropical,
                saturn_sidereal=wrapper.to_sidereal(saturn_tropical, ayanamsa),
            )

        return cls.scan(
            birth_dt=birth_dt,
            natal_venus_sidereal=venus_sidereal,
            natal_venus_rashi=cls._longitude_to_rashi(venus_sidereal),
            cusp_7_rashi=cls._longitude_to_rashi(cusp_7_sidereal),
            transit_positions=_positions,
            scan_start_age=scan_start_age,
            scan_end_age=scan_end_age,
            subject_name=subject_name,
        )
