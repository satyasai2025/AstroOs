"""
AstroOS — Tri-Lifespan (Ayurdaya) & Maraka Synthesis Engine
============================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 3A)
Source: Brihat Parashara Hora Shastra (BPHS) Chapters 43-45 (Pindayu, Nisargayu, Amshayu)

Key Siddhantic Rules Enforced:
1. Three Mathematical Lifespan Models:
   - Pindayu (Planetary degree arc from deep exaltation/debilitation).
   - Nisargayu (Natural planetary allotment).
   - Amshayu (Navamsha elapsed arc).
2. Four Classical Rectifications (Harana & Bharana):
   - Shatrukshetra Harana (Enemy Sign: 1/3 reduction, unless retrograde).
   - Astangata Harana (Combustion: 1/2 reduction, Venus & Saturn exempted per BPHS 43.23).
   - Chakrapata / Dwadashabhava Harana (Visible half reduction based on houses 12, 11, 10, 9, 8, 7).
   - Bharana (Exaltation doubling, Vargottama increase).
3. Maraka & Vulnerability Synthesis:
   - Primary Marakas: Lords of 2nd & 7th houses + occupants.
   - Secondary Marakas: Lords of 3rd, 8th, 12th, 6th + Badhaka.
   - D30 Trishamsha affliction cross-check.
   - Saturn Maraka Absorption: Saturn aspecting or conjunct a Maraka absorbs Maraka shakti.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.services.badhaka_maraka_engine import BadhakaMarakaEngine, BadhakaMarakaResult
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import SIGN_LORDS
from packages.shared.enums import AyanamsaSystem, Rashi

# Deep Exaltation & Debilitation Degrees (BPHS 3.49-50)
_DEEP_EXALTATION: Dict[str, float] = {
    "sun": 10.0,       # Aries 10° (Abs: 10.0)
    "moon": 33.0,      # Taurus 3° (Abs: 33.0)
    "mars": 298.0,     # Capricorn 28° (Abs: 298.0)
    "mercury": 165.0,  # Virgo 15° (Abs: 165.0)
    "jupiter": 95.0,   # Cancer 5° (Abs: 95.0)
    "venus": 357.0,    # Pisces 27° (Abs: 357.0)
    "saturn": 200.0,   # Libra 20° (Abs: 200.0)
}

_DEEP_DEBILITATION: Dict[str, float] = {
    "sun": 190.0,      # Libra 10°
    "moon": 213.0,     # Scorpio 3°
    "mars": 118.0,     # Cancer 28°
    "mercury": 345.0,  # Pisces 15°
    "jupiter": 275.0,  # Capricorn 5°
    "venus": 177.0,    # Virgo 27°
    "saturn": 20.0,    # Aries 20°
}

# Maximum Pindayu Allotment (in Years) at Deep Exaltation (BPHS 43.4-5)
_PINDAYU_MAX_YEARS: Dict[str, float] = {
    "sun": 19.0,
    "moon": 25.0,
    "mars": 15.0,
    "mercury": 12.0,
    "jupiter": 15.0,
    "venus": 21.0,
    "saturn": 20.0,
}

# Nisargayu Natural Planetary Allotments (in Years) (BPHS 43.15-16)
_NISARGAYU_MAX_YEARS: Dict[str, float] = {
    "moon": 1.0,
    "mars": 2.0,
    "mercury": 9.0,
    "venus": 20.0,
    "jupiter": 18.0,
    "sun": 20.0,
    "saturn": 50.0,
}

_RASHI_NAMES = [r.value for r in Rashi]

# Planetary Natural Friends, Neutrals, Enemies (BPHS)
_NATURAL_RELATIONS: Dict[str, Dict[str, str]] = {
    "sun": {"friends": ["moon", "mars", "jupiter"], "neutrals": ["mercury"], "enemies": ["venus", "saturn"]},
    "moon": {"friends": ["sun", "mercury"], "neutrals": ["mars", "jupiter", "venus", "saturn"], "enemies": []},
    "mars": {"friends": ["sun", "moon", "jupiter"], "neutrals": ["venus", "saturn"], "enemies": ["mercury"]},
    "mercury": {"friends": ["sun", "venus"], "neutrals": ["mars", "jupiter", "saturn"], "enemies": ["moon"]},
    "jupiter": {"friends": ["sun", "moon", "mars"], "neutrals": ["saturn"], "enemies": ["mercury", "venus"]},
    "venus": {"friends": ["mercury", "saturn"], "neutrals": ["mars", "jupiter"], "enemies": ["sun", "moon"]},
    "saturn": {"friends": ["mercury", "venus"], "neutrals": ["jupiter"], "enemies": ["sun", "moon", "mars"]},
}

_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
_MALEFICS = {"saturn", "mars", "sun", "rahu", "ketu"}


@dataclass(frozen=True)
class PlanetaryAyurContribution:
    """Individual planet's lifespan contribution under a specific method."""
    planet: str
    base_years: float
    shatrukshetra_reduction: float
    astangata_reduction: float
    chakrapata_reduction: float
    bharana_enhancement: float
    net_years: float


@dataclass(frozen=True)
class MethodLifespanResult:
    """Calculated lifespan under a single classical methodology."""
    method_name: str          # "Pindayu" | "Amshayu" | "Nisargayu"
    planetary_contributions: Tuple[PlanetaryAyurContribution, ...]
    lagna_contribution: float
    total_years: float
    category: str             # "ALPAYU" (<32) | "MADHYAYU" (32-64) | "PURNAYU" (>64)


@dataclass(frozen=True)
class MarakaVulnerabilityAssessment:
    """Maraka, Badhaka and D30 Trishamsha mortality factors."""
    primary_maraka_lords: Tuple[str, ...]
    secondary_maraka_lords: Tuple[str, ...]
    badhaka_lord: str
    badhaka_house: int
    is_saturn_maraka_absorber: bool
    saturn_maraka_reason: str
    d30_afflicted_planets: Tuple[str, ...]
    high_risk_dasha_lords: Tuple[str, ...]
    vulnerability_index: float  # 0.0 to 10.0 scale


@dataclass(frozen=True)
class TriLifespanSynthesisResult:
    """Comprehensive 3-method lifespan synthesis and Maraka timing assessment."""
    pindayu: MethodLifespanResult
    amshayu: MethodLifespanResult
    nisargayu: MethodLifespanResult
    mean_lifespan_years: float
    consensus_category: str     # "ALPAYU" | "MADHYAYU" | "PURNAYU"
    maraka_assessment: MarakaVulnerabilityAssessment
    shastric_notes: Tuple[str, ...]


class LifespanEngine:
    """
    Computes Pindayu, Amshayu, Nisargayu and performs Maraka & D30 synthesis.
    """

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._badhaka_engine = BadhakaMarakaEngine()

    @staticmethod
    def _angular_diff_360(a: float, b: float) -> float:
        """Normalized difference (a - b) modulo 360."""
        return (a - b) % 360.0

    @classmethod
    def _is_enemy_sign(cls, planet: str, sign_idx: int) -> bool:
        lord = SIGN_LORDS[_RASHI_NAMES[sign_idx]]
        if lord == planet:
            return False
        enemies = _NATURAL_RELATIONS.get(planet, {}).get("enemies", [])
        return lord in enemies

    @classmethod
    def _compute_chakrapata_fraction(cls, house_from_lagna: int, is_benefic: bool) -> float:
        """
        Dwadashabhava (Chakrapata) Harana fraction for visible hemisphere (12H down to 7H).
        Malefics lose full portion; Benefics lose half (BPHS 43.25-28).
        12H: 1 (malefic) / 1/2 (benefic)
        11H: 1/2 / 1/4
        10H: 1/3 / 1/6
        9H:  1/4 / 1/8
        8H:  1/5 / 1/10
        7H:  1/6 / 1/12
        """
        malefic_fractions = {
            12: 1.0,
            11: 1.0 / 2.0,
            10: 1.0 / 3.0,
            9: 1.0 / 4.0,
            8: 1.0 / 5.0,
            7: 1.0 / 6.0,
        }
        frac = malefic_fractions.get(house_from_lagna, 0.0)
        return (frac / 2.0) if is_benefic else frac

    def calculate_pindayu(
        self,
        chart: EphemerisResult,
    ) -> MethodLifespanResult:
        """Calculates Pindayu with Harana and Bharana corrections."""
        planets_map = {p.planet: p for p in chart.planet_positions}
        asc = chart.ascendant
        asc_long = asc.sidereal_longitude
        asc_sign_idx = _RASHI_NAMES.index(asc.rashi)
        sun_long = planets_map["sun"].sidereal_longitude

        contributions: List[PlanetaryAyurContribution] = []
        classical_7 = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

        for pl_name in classical_7:
            pl = planets_map[pl_name]
            p_long = pl.sidereal_longitude
            deb_point = _DEEP_DEBILITATION[pl_name]
            max_years = _PINDAYU_MAX_YEARS[pl_name]

            # Base years from distance from deep debilitation point
            dist_from_deb = self._angular_diff_360(p_long, deb_point)
            if dist_from_deb <= 180.0:
                base_yrs = max_years * (dist_from_deb / 360.0) * 2.0
            else:
                base_yrs = max_years * (1.0 - ((dist_from_deb - 180.0) / 360.0) * 2.0)

            # 1. Bharana (Exaltation doubling / Own sign 1.5x)
            bharana = 0.0
            sign_idx = int(p_long // 30) % 12
            if abs(self._angular_diff_360(p_long, _DEEP_EXALTATION[pl_name])) < 15.0:
                bharana = base_yrs * 1.0  # doubles the contribution
            elif SIGN_LORDS[_RASHI_NAMES[sign_idx]] == pl_name:
                bharana = base_yrs * 0.5

            current_yrs = base_yrs + bharana

            # 2. Shatrukshetra Harana (1/3 reduction if in enemy sign, unless retrograde)
            shatru_red = 0.0
            if self._is_enemy_sign(pl_name, sign_idx) and not pl.is_retrograde:
                shatru_red = current_yrs * (1.0 / 3.0)
            current_yrs -= shatru_red

            # 3. Astangata Harana (Combustion: 1/2 reduction; Venus & Saturn exempted)
            astangata_red = 0.0
            if pl_name not in ("sun", "venus", "saturn"):
                combust_orb = 14.0 if pl_name == "mars" else (12.0 if pl_name == "moon" else 11.0)
                if abs(self._angular_diff_360(p_long, sun_long)) < combust_orb or pl.is_combust:
                    astangata_red = current_yrs * 0.5
            current_yrs -= astangata_red

            # 4. Chakrapata / Dwadashabhava Harana
            house_from_lag = ((sign_idx - asc_sign_idx) % 12) + 1
            is_ben = pl_name in _BENEFICS
            chakrapata_frac = self._compute_chakrapata_fraction(house_from_lag, is_ben)
            chakrapata_red = current_yrs * chakrapata_frac
            net_yrs = max(0.0, current_yrs - chakrapata_red)

            contributions.append(PlanetaryAyurContribution(
                planet=pl_name,
                base_years=round(base_yrs, 3),
                shatrukshetra_reduction=round(shatru_red, 3),
                astangata_reduction=round(astangata_red, 3),
                chakrapata_reduction=round(chakrapata_red, 3),
                bharana_enhancement=round(bharana, 3),
                net_years=round(net_yrs, 3),
            ))

        # Lagna contribution (Navamshas elapsed from Aries / 108 * max_years)
        lagna_navamshas = (asc_long / (360.0 / 108.0))
        lagna_contribution = round(lagna_navamshas / 108.0 * 20.0, 3)

        total_yrs = round(sum(c.net_years for c in contributions) + lagna_contribution, 2)
        category = "ALPAYU" if total_yrs < 32.0 else ("MADHYAYU" if total_yrs <= 64.0 else "PURNAYU")

        return MethodLifespanResult(
            method_name="Pindayu",
            planetary_contributions=tuple(contributions),
            lagna_contribution=lagna_contribution,
            total_years=total_yrs,
            category=category,
        )

    def calculate_nisargayu(
        self,
        chart: EphemerisResult,
    ) -> MethodLifespanResult:
        """Calculates Nisargayu based on natural planetary allotments."""
        planets_map = {p.planet: p for p in chart.planet_positions}
        asc = chart.ascendant
        asc_sign_idx = _RASHI_NAMES.index(asc.rashi)
        sun_long = planets_map["sun"].sidereal_longitude

        contributions: List[PlanetaryAyurContribution] = []
        classical_7 = ("moon", "mars", "mercury", "venus", "jupiter", "sun", "saturn")

        for pl_name in classical_7:
            pl = planets_map[pl_name]
            p_long = pl.sidereal_longitude
            deb_point = _DEEP_DEBILITATION[pl_name]
            max_years = _NISARGAYU_MAX_YEARS[pl_name]

            dist_from_deb = self._angular_diff_360(p_long, deb_point)
            if dist_from_deb <= 180.0:
                base_yrs = max_years * (dist_from_deb / 360.0) * 2.0
            else:
                base_yrs = max_years * (1.0 - ((dist_from_deb - 180.0) / 360.0) * 2.0)

            sign_idx = int(p_long // 30) % 12
            bharana = base_yrs * 0.5 if SIGN_LORDS[_RASHI_NAMES[sign_idx]] == pl_name else 0.0
            current_yrs = base_yrs + bharana

            shatru_red = current_yrs * (1.0 / 3.0) if (self._is_enemy_sign(pl_name, sign_idx) and not pl.is_retrograde) else 0.0
            current_yrs -= shatru_red

            astangata_red = 0.0
            if pl_name not in ("sun", "venus", "saturn") and (pl.is_combust or abs(self._angular_diff_360(p_long, sun_long)) < 11.0):
                astangata_red = current_yrs * 0.5
            current_yrs -= astangata_red

            house_from_lag = ((sign_idx - asc_sign_idx) % 12) + 1
            chakrapata_frac = self._compute_chakrapata_fraction(house_from_lag, pl_name in _BENEFICS)
            chakrapata_red = current_yrs * chakrapata_frac
            net_yrs = max(0.0, current_yrs - chakrapata_red)

            contributions.append(PlanetaryAyurContribution(
                planet=pl_name,
                base_years=round(base_yrs, 3),
                shatrukshetra_reduction=round(shatru_red, 3),
                astangata_reduction=round(astangata_red, 3),
                chakrapata_reduction=round(chakrapata_red, 3),
                bharana_enhancement=round(bharana, 3),
                net_years=round(net_yrs, 3),
            ))

        lagna_contribution = round(asc.sidereal_longitude / 360.0 * 20.0, 3)
        total_yrs = round(sum(c.net_years for c in contributions) + lagna_contribution, 2)
        category = "ALPAYU" if total_yrs < 32.0 else ("MADHYAYU" if total_yrs <= 64.0 else "PURNAYU")

        return MethodLifespanResult(
            method_name="Nisargayu",
            planetary_contributions=tuple(contributions),
            lagna_contribution=lagna_contribution,
            total_years=total_yrs,
            category=category,
        )

    def calculate_amshayu(
        self,
        chart: EphemerisResult,
    ) -> MethodLifespanResult:
        """Calculates Amshayu based on Navamshas elapsed."""
        planets_map = {p.planet: p for p in chart.planet_positions}
        asc = chart.ascendant
        asc_sign_idx = _RASHI_NAMES.index(asc.rashi)
        sun_long = planets_map["sun"].sidereal_longitude

        contributions: List[PlanetaryAyurContribution] = []
        classical_7 = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

        for pl_name in classical_7:
            pl = planets_map[pl_name]
            p_long = pl.sidereal_longitude
            sign_idx = int(p_long // 30) % 12
            deg_in_sign = p_long % 30.0

            # 1 Navamsha = 3°20' (3.3333°). Base years = completed Navamshas in sign
            base_yrs = (deg_in_sign / 3.3333333) + 1.0  # 1 to 9 years per sign

            bharana = base_yrs * 0.5 if SIGN_LORDS[_RASHI_NAMES[sign_idx]] == pl_name else 0.0
            current_yrs = base_yrs + bharana

            shatru_red = current_yrs * (1.0 / 3.0) if (self._is_enemy_sign(pl_name, sign_idx) and not pl.is_retrograde) else 0.0
            current_yrs -= shatru_red

            astangata_red = 0.0
            if pl_name not in ("sun", "venus", "saturn") and (pl.is_combust or abs(self._angular_diff_360(p_long, sun_long)) < 11.0):
                astangata_red = current_yrs * 0.5
            current_yrs -= astangata_red

            house_from_lag = ((sign_idx - asc_sign_idx) % 12) + 1
            chakrapata_frac = self._compute_chakrapata_fraction(house_from_lag, pl_name in _BENEFICS)
            chakrapata_red = current_yrs * chakrapata_frac
            net_yrs = max(0.0, current_yrs - chakrapata_red)

            contributions.append(PlanetaryAyurContribution(
                planet=pl_name,
                base_years=round(base_yrs, 3),
                shatrukshetra_reduction=round(shatru_red, 3),
                astangata_reduction=round(astangata_red, 3),
                chakrapata_reduction=round(chakrapata_red, 3),
                bharana_enhancement=round(bharana, 3),
                net_years=round(net_yrs, 3),
            ))

        lagna_navamshas_in_sign = (asc.rashi_degree / 3.3333333) + 1.0
        lagna_contribution = round(lagna_navamshas_in_sign, 3)

        total_yrs = round(sum(c.net_years for c in contributions) + lagna_contribution, 2)
        category = "ALPAYU" if total_yrs < 32.0 else ("MADHYAYU" if total_yrs <= 64.0 else "PURNAYU")

        return MethodLifespanResult(
            method_name="Amshayu",
            planetary_contributions=tuple(contributions),
            lagna_contribution=lagna_contribution,
            total_years=total_yrs,
            category=category,
        )

    def evaluate_marakas_and_d30(
        self,
        chart: EphemerisResult,
    ) -> MarakaVulnerabilityAssessment:
        """Evaluates Maraka lords, Badhaka, Saturn absorption, and D30 maleficence."""
        planets_map = {p.planet: p for p in chart.planet_positions}
        asc = chart.ascendant
        asc_sign_idx = _RASHI_NAMES.index(asc.rashi)

        # 1. Badhaka & Primary Marakas
        badhaka_house = 11 if asc.rashi in ("aries", "cancer", "libra", "capricorn") else (9 if asc.rashi in ("taurus", "leo", "scorpio", "aquarius") else 7)
        badhaka_sign = _RASHI_NAMES[(asc_sign_idx + badhaka_house - 1) % 12]
        badhaka_lord = SIGN_LORDS[badhaka_sign]

        second_sign = _RASHI_NAMES[(asc_sign_idx + 1) % 12]
        seventh_sign = _RASHI_NAMES[(asc_sign_idx + 6) % 12]
        primary_marakas = tuple(dict.fromkeys([SIGN_LORDS[second_sign], SIGN_LORDS[seventh_sign]]))

        sixth_sign = _RASHI_NAMES[(asc_sign_idx + 5) % 12]
        eighth_sign = _RASHI_NAMES[(asc_sign_idx + 7) % 12]
        twelfth_sign = _RASHI_NAMES[(asc_sign_idx + 11) % 12]
        secondary_marakas = tuple(dict.fromkeys([SIGN_LORDS[sixth_sign], SIGN_LORDS[eighth_sign], SIGN_LORDS[twelfth_sign], badhaka_lord]))

        # 2. Saturn Maraka Absorption (BPHS / Jha Step 3A)
        saturn = planets_map.get("saturn")
        is_saturn_absorber = False
        saturn_reason = "Saturn is free from Maraka conjunction/aspect."

        if saturn:
            sat_sign = _RASHI_NAMES.index(saturn.rashi)
            maraka_signs = {
                int(planets_map[m].sidereal_longitude // 30) % 12
                for m in primary_marakas if m in planets_map
            }
            # Conjunction
            if sat_sign in maraka_signs:
                is_saturn_absorber = True
                saturn_reason = "Saturn is conjunct a primary Maraka lord and absorbs primary killer potency."
            else:
                # Saturn aspects 3rd, 7th, 10th houses from itself
                sat_aspects = {(sat_sign + 2) % 12, (sat_sign + 6) % 12, (sat_sign + 9) % 12}
                if any(ms in sat_aspects for ms in maraka_signs):
                    is_saturn_absorber = True
                    saturn_reason = "Saturn casts Graha Drishti upon a primary Maraka lord, assuming primary killer status."

        # 3. D30 Trishamsha Affliction Check
        # Compute D30 signs for planets
        d30_afflicted: List[str] = []
        for pl_name, pl in planets_map.items():
            deg_in_sign = pl.sidereal_longitude % 30.0
            sign_idx = int(pl.sidereal_longitude // 30) % 12
            is_odd = (sign_idx % 2 == 0)  # Aries=0 (Odd), Taurus=1 (Even)

            # Standard Parashari Trishamsha degrees
            if is_odd:
                d30_rashi = "aries" if deg_in_sign < 5.0 else ("aquarius" if deg_in_sign < 10.0 else ("sagittarius" if deg_in_sign < 18.0 else ("gemini" if deg_in_sign < 25.0 else "libra")))
            else:
                d30_rashi = "taurus" if deg_in_sign < 5.0 else ("virgo" if deg_in_sign < 12.0 else ("pisces" if deg_in_sign < 20.0 else ("capricorn" if deg_in_sign < 25.0 else "scorpio")))

            # Check if planet lands in 6th, 8th, 12th from Lagna in D30
            d30_sign_idx = _RASHI_NAMES.index(d30_rashi)
            d30_house_from_lag = ((d30_sign_idx - asc_sign_idx) % 12) + 1
            if d30_house_from_lag in (6, 8, 12):
                d30_afflicted.append(pl_name)

        high_risk_dashas = list(primary_marakas)
        if is_saturn_absorber and "saturn" not in high_risk_dashas:
            high_risk_dashas.append("saturn")
        for p in d30_afflicted:
            if p not in high_risk_dashas and p in ("mars", "rahu", "ketu", "sun"):
                high_risk_dashas.append(p)

        vuln_index = min(10.0, 2.0 * len(primary_marakas) + (2.5 if is_saturn_absorber else 0.0) + 0.8 * len(d30_afflicted))

        return MarakaVulnerabilityAssessment(
            primary_maraka_lords=primary_marakas,
            secondary_maraka_lords=secondary_marakas,
            badhaka_lord=badhaka_lord,
            badhaka_house=badhaka_house,
            is_saturn_maraka_absorber=is_saturn_absorber,
            saturn_maraka_reason=saturn_reason,
            d30_afflicted_planets=tuple(d30_afflicted),
            high_risk_dasha_lords=tuple(high_risk_dashas),
            vulnerability_index=round(vuln_index, 2),
        )

    def calculate_tri_lifespan_synthesis(
        self,
        chart: EphemerisResult,
    ) -> TriLifespanSynthesisResult:
        """Synthesizes Pindayu, Amshayu, Nisargayu and Maraka assessment."""
        pindayu = self.calculate_pindayu(chart)
        nisargayu = self.calculate_nisargayu(chart)
        amshayu = self.calculate_amshayu(chart)
        maraka_eval = self.evaluate_marakas_and_d30(chart)

        mean_yrs = round((pindayu.total_years + nisargayu.total_years + amshayu.total_years) / 3.0, 2)
        consensus_cat = "ALPAYU" if mean_yrs < 32.0 else ("MADHYAYU" if mean_yrs <= 64.0 else "PURNAYU")

        notes = (
            f"Tri-Lifespan Synthesis: Pindayu ({pindayu.total_years}y), Nisargayu ({nisargayu.total_years}y), Amshayu ({amshayu.total_years}y).",
            f"Consensus Category: {consensus_cat} with an average span of {mean_yrs} years.",
            f"Primary Maraka Lords: {', '.join(maraka_eval.primary_maraka_lords)}.",
            maraka_eval.saturn_maraka_reason,
            f"High-Risk Dasha Lords: {', '.join(maraka_eval.high_risk_dasha_lords)}.",
        )

        return TriLifespanSynthesisResult(
            pindayu=pindayu,
            amshayu=amshayu,
            nisargayu=nisargayu,
            mean_lifespan_years=mean_yrs,
            consensus_category=consensus_cat,
            maraka_assessment=maraka_eval,
            shastric_notes=notes,
        )
