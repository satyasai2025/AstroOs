"""
AstroOS — Sudarshana Chakra (SC) Engine
=======================================
Implements the canonical Tri-Lagna Sudarshana Chakra synthesis strictly per
Vinay Jha's treatises ("How To Make Correct Predictions"):

  1. Decision Branch:
     - If Sun OR Moon is in Lagna (House 1 of LK) → Use Lagna Kundali (LK) ONLY.
     - Otherwise → Synthesize Tri-Lagna (LK + SK + CK).

  2. Significant Houses in Tri-Lagna:
     - LK (Lagna Kundali): All 12 houses evaluated.
     - SK (Surya Kundali): Only 3 Trikona houses from Sun are significant: {1, 5, 9}.
     - CK (Chandra Kundali): 5 houses from Moon are significant: {1, 2, 4, 9, 11}.

  3. Shastric Functional Score (No arbitrary decimals):
     - Lord of Trikona {1, 5, 9} = +1 (Functional Benefic)
     - Lord of Dusthana {6, 8, 12} = -1 (Functional Malefic)
     - Score = (Count of Benefic Lordships) - (Count of Malefic Lordships)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import SIGN_LORDS

RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

# Shastric functional house sets
FUNC_BENEFIC_HOUSES: Set[int] = {1, 5, 9}
FUNC_MALEFIC_HOUSES: Set[int] = {6, 8, 12}

# SK: only 3 houses significant (Sun ke saath Trikona)
SK_SIGNIFICANT_HOUSES: Set[int] = {1, 5, 9}

# CK: 5 houses significant from Moon (1, 2, 4, 9, 11)
CK_SIGNIFICANT_HOUSES: Set[int] = {1, 2, 4, 9, 11}


@dataclass(frozen=True)
class PlanetSudarshanaProfile:
    """Sudarshana Chakra analysis for a single Graha."""
    planet: str
    lk_houses_owned: Tuple[int, ...]
    sk_houses_owned: Tuple[int, ...]
    ck_houses_owned: Tuple[int, ...]
    lk_functional_score: int
    sk_functional_score: int
    ck_functional_score: int
    net_functional_score: int
    is_functional_benefic: bool  # True if net_score > 0
    is_functional_malefic: bool  # True if net_score < 0


@dataclass
class SudarshanaChakraReport:
    """Comprehensive Tri-Lagna Sudarshana Chakra Synthesis."""
    lagna_rashi: str
    sun_rashi: str
    moon_rashi: str
    sun_in_lagna: bool
    moon_in_lagna: bool
    is_tri_lagna_active: bool  # False if Sun or Moon is in Lagna (LK only per Jha)
    profiles: Dict[str, PlanetSudarshanaProfile]
    # SCD-augmented fields (populated by evaluate_chart when target_datetime provided)
    current_scd: Optional[Any] = None
    active_house_from_lagna: Optional[int] = None
    scd_age_years: Optional[float] = None
    tri_fold_harmony_score: Optional[float] = None

    @property
    def graha_alignments(self) -> list:
        class Alignment:
            def __init__(self, p_name: str, prof: Any):
                self.point_name = p_name
                self.rashi = ""
                self.house_from_lagna = prof.lk_houses_owned[0] if getattr(prof, "lk_houses_owned", None) else 1
                self.house_from_moon = prof.ck_houses_owned[0] if getattr(prof, "ck_houses_owned", None) else 1
                self.house_from_sun = prof.sk_houses_owned[0] if getattr(prof, "sk_houses_owned", None) else 1
                self.tri_fold_auspiciousness = getattr(prof, "net_functional_score", 0)
                self.supporting_lagnas_count = 1 if getattr(prof, "is_functional_benefic", False) else 0
        return [Alignment(p, prof) for p, prof in (self.profiles or {}).items()]



def _get_houses_owned_by_planet(planet: str, lagna_rashi_idx: int) -> List[int]:
    """Finds which houses (1-12) the planet rules from a given lagna index."""
    owned_houses = []
    planet_norm = planet.lower()
    for h in range(1, 13):
        r_idx = (lagna_rashi_idx + h - 1) % 12
        r_name = RASHI_LIST[r_idx]
        lord = SIGN_LORDS.get(r_name, "").lower()
        if lord == planet_norm:
            owned_houses.append(h)
    return owned_houses


def _compute_functional_score(houses: List[int], allowed_significant_houses: Optional[Set[int]] = None) -> int:
    """
    Computes integer functional score:
      +1 for each owned house in {1, 5, 9}
      -1 for each owned house in {6, 8, 12}
    If allowed_significant_houses is provided, only houses in that set are counted.
    """
    benefic = 0
    malefic = 0
    for h in houses:
        if allowed_significant_houses is not None and h not in allowed_significant_houses:
            continue
        if h in FUNC_BENEFIC_HOUSES:
            benefic += 1
        if h in FUNC_MALEFIC_HOUSES:
            malefic += 1
    return benefic - malefic


class SudarshanaChakraEngine:
    """Canonical Sudarshana Chakra engine implementing Jha's exact Tri-Lagna synthesis."""

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)

    def analyze(
        self,
        lagna_deg: float,
        sun_deg: float,
        moon_deg: float,
    ) -> SudarshanaChakraReport:
        """
        Synthesizes LK, SK, and CK for all classical Grahas.
        """
        lagna_rashi_idx = int((lagna_deg % 360.0) / 30.0) % 12
        sun_rashi_idx = int((sun_deg % 360.0) / 30.0) % 12
        moon_rashi_idx = int((moon_deg % 360.0) / 30.0) % 12

        lagna_rashi = RASHI_LIST[lagna_rashi_idx]
        sun_rashi = RASHI_LIST[sun_rashi_idx]
        moon_rashi = RASHI_LIST[moon_rashi_idx]

        sun_in_lagna = (sun_rashi_idx == lagna_rashi_idx)
        moon_in_lagna = (moon_rashi_idx == lagna_rashi_idx)

        # Jha Rule: "If Sun or Moon is in lagna, then only Lagna Chakra should be used"
        tri_lagna_active = not (sun_in_lagna or moon_in_lagna)

        classical_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        profiles: Dict[str, PlanetSudarshanaProfile] = {}

        for p in classical_planets:
            p_cap = p.capitalize()
            lk_houses = _get_houses_owned_by_planet(p, lagna_rashi_idx)
            sk_houses = _get_houses_owned_by_planet(p, sun_rashi_idx)
            ck_houses = _get_houses_owned_by_planet(p, moon_rashi_idx)

            lk_score = _compute_functional_score(lk_houses)  # All 12 houses evaluated in LK

            if tri_lagna_active:
                # SK: only {1, 5, 9} significant
                sk_score = _compute_functional_score(sk_houses, SK_SIGNIFICANT_HOUSES)
                # CK: only {1, 2, 4, 9, 11} significant
                ck_score = _compute_functional_score(ck_houses, CK_SIGNIFICANT_HOUSES)
                net_score = lk_score + sk_score + ck_score
            else:
                sk_score = 0
                ck_score = 0
                net_score = lk_score

            profiles[p_cap] = PlanetSudarshanaProfile(
                planet=p_cap,
                lk_houses_owned=tuple(lk_houses),
                sk_houses_owned=tuple(sk_houses),
                ck_houses_owned=tuple(ck_houses),
                lk_functional_score=lk_score,
                sk_functional_score=sk_score,
                ck_functional_score=ck_score,
                net_functional_score=net_score,
                is_functional_benefic=(net_score > 0),
                is_functional_malefic=(net_score < 0),
            )

        return SudarshanaChakraReport(
            lagna_rashi=lagna_rashi.capitalize(),
            sun_rashi=sun_rashi.capitalize(),
            moon_rashi=moon_rashi.capitalize(),
            sun_in_lagna=sun_in_lagna,
            moon_in_lagna=moon_in_lagna,
            is_tri_lagna_active=tri_lagna_active,
            profiles=profiles,
        )

    def evaluate_chart(
        self,
        chart: 'D1Chart',
        birth_datetime: datetime,
        target_datetime: Optional[datetime] = None,
    ) -> SudarshanaChakraReport:
        """Evaluates Sudarshana Chakra from a D1Chart.

        Extracts lagna/sun/moon degrees from the chart and synthesizes
        the Tri-Lagna report. If target_datetime is provided, also computes
        the active SCD house and tri-fold harmony score.
        """
        from apps.api.domain.horoscope import D1Chart
        from apps.api.services.sudarshana_chakra_dasha_engine import SudarshanaChakraDashaEngine
        from datetime import date

        # Extract degrees from chart
        if hasattr(chart, "lagna_madhya"):
            lagna_deg = chart.lagna_madhya
        elif hasattr(chart, "ascendant"):
            lagna_deg = chart.ascendant.sidereal_longitude if hasattr(chart.ascendant, "sidereal_longitude") else float(chart.ascendant)
        else:
            lagna_deg = 0.0

        if hasattr(chart, "sun") and chart.sun:
            sun_deg = chart.sun.sidereal_longitude
        else:
            planets_list = getattr(chart, "planets", []) or (getattr(chart, "ephemeris", None).planet_positions if hasattr(chart, "ephemeris") else [])
            sun_p = next((p for p in planets_list if getattr(p, "planet", "").lower() == "sun"), None)
            sun_deg = sun_p.sidereal_longitude if sun_p else 0.0

        if hasattr(chart, "moon") and chart.moon:
            moon_deg = chart.moon.sidereal_longitude
        else:
            planets_list = getattr(chart, "planets", []) or (getattr(chart, "ephemeris", None).planet_positions if hasattr(chart, "ephemeris") else [])
            moon_p = next((p for p in planets_list if getattr(p, "planet", "").lower() == "moon"), None)
            moon_deg = moon_p.sidereal_longitude if moon_p else 0.0


        # Base Tri-Lagna synthesis
        report = self.analyze(lagna_deg=lagna_deg, sun_deg=sun_deg, moon_deg=moon_deg)

        # If target_datetime provided, compute SCD progression
        if target_datetime is not None:
            scd_engine = SudarshanaChakraDashaEngine()
            scd_report = scd_engine.compute_scd(
                natal_chart=chart,
                birth_datetime=birth_datetime,
                target_date=target_datetime.date(),
            )
            # Augment report with SCD fields by creating a new report with additional fields
            from dataclasses import replace
            # Note: Since SudarshanaChakraReport is frozen, we create a new instance with extra fields
            # Add SCD-related fields as properties on the report object
            report.current_scd = scd_report
            report.active_house_from_lagna = scd_report.annual_house_offset
            report.scd_age_years = scd_report.native_age_years
            report.tri_fold_harmony_score = self._compute_tri_fold_harmony(scd_report)

        return report

    def _compute_tri_fold_harmony(self, scd_report: 'SudarshanaChakraDashaReport') -> float:
        """Compute tri-fold harmony score from SCD state."""
        # Simple heuristic: based on active house and age cycle
        # Full implementation would integrate LK/CK/SK assessments with SCD
        if scd_report.annual_house_offset in [1, 5, 9]:
            return 1.0  # Benefic alignment
        elif scd_report.annual_house_offset in [10, 11, 12]:
            return -1.0  # Malefic alignment
        else:
            return 0.0  # Neutral

    def compute_scd(self, birth_datetime: Any, target_datetime: Any, *args, **kwargs) -> Any:
        """Compute SCD house and progression helper."""
        from datetime import date, datetime
        birth_d = birth_datetime.date() if isinstance(birth_datetime, datetime) else birth_datetime
        target_d = target_datetime.date() if isinstance(target_datetime, datetime) else target_datetime
        days_diff = (target_d - birth_d).days
        age_years = max(0.0, days_diff / 365.2422)
        annual_house = int(age_years % 12) + 1

        class SCDPeriod:
            def __init__(self, house: int, age: float):
                self.active_house_from_lagna = house
                self.native_age_years = age
                self.annual_house_offset = house

        return SCDPeriod(annual_house, age_years)

