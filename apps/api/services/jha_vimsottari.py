"""
AstroOS — Vinay Jha Per-Varga Independent Vimshottari Dasha Engine (Step 2 & Step 4)
===================================================================================
Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Step 2 & Step 4)
Source: BPHS Dashaphala-adhyaya & Jha's "How To Make Correct Predictions"

Key Siddhantic Rules Enforced:
  1. Divisional Vimshottari is computed independently for each divisional chart:
     - D9 (Navamsha) — Marriage & Dharma
     - D10 (Dashamsha) — Career, Power & Status
     - D7 (Saptamsha) — Children & Progeny
     - D4 (Chaturthamsha) — Property & Vehicles
     - D30 (Trishamsha) — Disease, Crises & Misfortunes
     - D24 (Chaturvimshamsha) — Education & Knowledge
     - D12 (Dwadashamsha) — Parents & Ancestry
     - D3 (Drekkana) — Siblings, Valour & Longevity
     - D60 (Shashtiamsha) — Subtle Karma (if birth time BTR verified)
  2. The Varga Vimshottari is seeded from the Varga-projected Moon longitude.
  3. 5-Level Dasha Hierarchy:
     Mahadasha (MD) -> Antardasha (AD) -> Pratyantardasha (PD) -> Sookshma (SD) -> Praana (PAD)
  4. Final Strength Comparison Rule:
     "Divisional charts should NOT override D1 prediction unless their current
      Vimshottari planet's Final Strength exceeds D1's."
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.services.dasha_engine import (
    DashaEngine,
    _build_nakshatra_periods,
)
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    longitude_to_nakshatra,
)
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jha_dignity_engine import JhaDignityEngine, JhaDignityResult
from packages.shared.constants import (
    DAYS_PER_JULIAN_YEAR,
    DEGREES_PER_NAKSHATRA,
    KALACHAKRA_SAVYA_SIGNS,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
)

# Vimshopaka weights out of 20 (Jha Step 4)
VIMSHOPAKA_WEIGHTS: dict[str, float] = {
    "D1": 6.0,
    "D9": 3.0,
    "D10": 1.5,
    "D7": 1.0,
    "D4": 1.0,
    "D30": 1.0,
    "D12": 0.5,
    "D24": 0.5,
    "D3": 1.0,
    "D60": 4.0,
}

# ── Canonical Freeze Constants (BPHS + Jha Doctrine) ─────────────────────────
VIMSOTTARI_ORDER: list[tuple[str, int]] = [
    ("ketu",     7),
    ("venus",   20),
    ("sun",      6),
    ("moon",    10),
    ("mars",     7),
    ("rahu",    18),
    ("jupiter", 16),
    ("saturn",  19),
    ("mercury", 17),
]
TOTAL_YEARS: int = 120
NAKSHATRA_SPAN_MIN: float = 800.0  # 13°20′ = 800 arcminutes
NAKSHATRA_LORDS: list[tuple[str, int]] = VIMSOTTARI_ORDER * 3  # 27 nakshatras: Ashwini(0)=ketu ... Revati(26)=mercury

# Supported Year Conventions in Vedic Astrology
YEAR_LENGTHS: dict[str, float] = {
    "surya_siddhanta_solar": 365.25,    # सूर्यसिद्धांत सौर वर्ष (कैनन डिफ़ॉल्ट)
    "chaandra_tithi":        354.367,   # 360 तिथियों का चांद्र वर्ष (झा शोध कैनन)
    "365.25_solar":          365.25,    # Alias
    "354.367_chandra":       354.367,   # Alias
    "365.2422_tropical":     365.2422,  # Tropical year
    "360.0_savana":          360.0,     # 360-day savana year (Lahiri convention)
}
DEFAULT_YEAR_KEY: str = "surya_siddhanta_solar"
DASHA_DAYS: dict[str, float] = {
    lord: yrs * YEAR_LENGTHS[DEFAULT_YEAR_KEY] for lord, yrs in VIMSOTTARI_ORDER
}


def birth_dasha(longitude_moon_arcmin: float) -> tuple[str, float, float]:
    """
    जन्म-चंद्र की स्थिति (मेष 0° से आर्क-मिनट में) → (जन्म-दशा-स्वामी, शेष-अंश 0..1, शेष-वर्ष).
    """
    idx = int(longitude_moon_arcmin // NAKSHATRA_SPAN_MIN) % 27
    elapsed_in_nak = longitude_moon_arcmin % NAKSHATRA_SPAN_MIN
    fraction_elapsed = elapsed_in_nak / NAKSHATRA_SPAN_MIN
    lord = NAKSHATRA_LORDS[idx][0]
    years = dict(VIMSOTTARI_ORDER)[lord]
    balance = 1.0 - fraction_elapsed
    return lord, balance, balance * years


def antardasha_spans(maha_lord: str) -> list[tuple[str, float]]:
    """
    महादशा-स्वामी से आगे क्रमशः 9 अंतर्दशा; अवधि = महा-वर्ष × (अंतर्दशा-वर्ष / 120).
    """
    years = dict(VIMSOTTARI_ORDER)
    order = [l for l, _ in VIMSOTTARI_ORDER]
    start = order.index(maha_lord)
    maha_years = years[maha_lord]
    return [
        (order[(start + i) % 9], maha_years * years[order[(start + i) % 9]] / 120.0)
        for i in range(9)
    ]


def pratyantardasha_spans(maha_lord: str, antar_lord: str) -> list[tuple[str, float]]:
    """
    प्रत्यंतर्दशा: अवधि = अंतर्दशा-वर्ष × (प्रत्यंतर्दशा-वर्ष / 120).
    """
    years = dict(VIMSOTTARI_ORDER)
    order = [l for l, _ in VIMSOTTARI_ORDER]
    start = order.index(antar_lord)
    ad_spans = dict(antardasha_spans(maha_lord))
    ad_years = ad_spans[antar_lord]
    return [
        (order[(start + i) % 9], ad_years * years[order[(start + i) % 9]] / 120.0)
        for i in range(9)
    ]


@dataclass(frozen=True)
class JhaActiveVargaDasha:
    """Active 5-level Vimshottari lords for a divisional chart at an evaluation date."""
    varga_code: str
    evaluation_date: date
    mahadasha_lord: str
    antardasha_lord: str
    pratyantardasha_lord: str
    sookshma_lord: str
    praana_lord: str
    dasha_chain: Tuple[str, ...]
    md_start_date: date
    md_end_date: date
    ad_start_date: date
    ad_end_date: date
    is_dasha_sandhi: bool = False
    is_dasha_chhidra: bool = False
    days_to_md_end: int = 0
    sandhi_notes: str = ""


@dataclass(frozen=True)
class JhaDashaStrengthComparison:
    """
    Compares D1 active Vimshottari lord vs Varga active Vimshottari lord
    to determine if the Divisional chart has permission to override D1.
    """
    varga_code: str
    evaluation_date: date
    d1_active_lord: str
    d1_main_strength: float
    d1_final_strength: float
    varga_active_lord: str
    varga_main_strength: float
    varga_final_strength: float
    varga_overrides_d1: bool
    verdict_explanation: str


class JhaVimsottariEngine:
    """
    Computes independent Vimshottari Dasha hierarchies seeded for any Varga chart
    and evaluates Jha's Shastric D1 vs Varga Strength Override Rule.
    """

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horoscope_engine = HoroscopeEngine(self._wrapper)

    def compute_varga_moon_longitude(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_code: str = "D10",
        ayanamsa: str = "lahiri",
    ) -> float:
        """
        Calculates the exact sidereal longitude of the Moon projected into the target Varga.
        """
        v_clean = varga_code.upper().strip()
        calc_res = self._wrapper.calculate(
            dt=birth_datetime, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa
        )
        moon_pos = next(p for p in calc_res.planet_positions if p.planet.lower() == "moon")
        d1_lon = moon_pos.sidereal_longitude

        if v_clean == "D1":
            return d1_lon

        varga_rashi, varga_rashi_deg = compute_varga_sign(v_clean, d1_lon)
        rashi_name_clean = varga_rashi.lower()
        if rashi_name_clean in KALACHAKRA_SAVYA_SIGNS:
            varga_sign_idx = KALACHAKRA_SAVYA_SIGNS.index(rashi_name_clean)
        else:
            varga_sign_idx = 0

        varga_lon = (float(varga_sign_idx) * 30.0 + varga_rashi_deg) % 360.0
        return varga_lon

    def compute_varga_dasha_tree(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_code: str = "D10",
        max_depth: int = 5,
        num_cycles: int = 1,
        ayanamsa: str = "lahiri",
        year_convention: str = "365.25_solar",
        arsha_mode: str = "standard",
    ) -> DashaTree:
        """
        Generates full independent Vimshottari Dasha tree for the specified Varga.
        arsha_mode: "standard" (popular Ashwinyadi method) or "ardradi" (Arsha Rishi method
                    prescribed in BPHS/Kundalee chkArsh when Lagna in Sun's Hora & Krishna Paksha).
        """
        v_clean = varga_code.upper().strip()
        days_per_year = YEAR_LENGTHS.get(year_convention, 365.25)
        varga_moon_lon = self.compute_varga_moon_longitude(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            varga_code=v_clean,
            ayanamsa=ayanamsa,
        )

        nak_info = longitude_to_nakshatra(varga_moon_lon)
        if arsha_mode.lower() == "ardradi":
            # Arsha reckoning: counted from Ardra (Nakshatra 6)
            offset_from_ardra = (nak_info.nakshatra_number - 6) % 27
            start_seq_idx = offset_from_ardra % len(VIMSHOTTARI_SEQUENCE)
            start_lord = VIMSHOTTARI_SEQUENCE[start_seq_idx]
        else:
            start_lord = nak_info.lord.lower()
            start_seq_idx = VIMSHOTTARI_SEQUENCE.index(start_lord)

        fraction_elapsed = nak_info.degree_in_nakshatra / DEGREES_PER_NAKSHATRA
        total_lord_years = VIMSHOTTARI_DASHA_YEARS[start_lord]
        remaining_fraction = 1.0 - fraction_elapsed
        balance_years = remaining_fraction * float(total_lord_years)
        balance_days = round(balance_years * days_per_year)

        b_date = birth_datetime.date()
        first_end_date = b_date + timedelta(days=balance_days)

        mahadashas: list[DashaPeriod] = []

        # 1. First (partial) Mahadasha
        first_subs = _build_nakshatra_periods(
            start_lord=start_lord,
            sequence=VIMSHOTTARI_SEQUENCE,
            period_years=VIMSHOTTARI_DASHA_YEARS,
            total_years=VIMSHOTTARI_TOTAL_YEARS,
            start_date=b_date,
            end_date=first_end_date,
            level=2,
            max_depth=max_depth,
        )
        mahadashas.append(
            DashaPeriod(
                lord=start_lord,
                start_date=b_date,
                end_date=first_end_date,
                duration_days=balance_days,
                level=1,
                sub_periods=first_subs,
            )
        )

        # 2. Subsequent Mahadashas
        current_start = first_end_date
        total_mds = len(VIMSHOTTARI_SEQUENCE) * num_cycles
        for i in range(1, total_mds):
            lord = VIMSHOTTARI_SEQUENCE[(start_seq_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
            md_years = VIMSHOTTARI_DASHA_YEARS[lord]
            md_days = round(md_years * days_per_year)
            current_end = current_start + timedelta(days=md_days)

            subs = _build_nakshatra_periods(
                start_lord=lord,
                sequence=VIMSHOTTARI_SEQUENCE,
                period_years=VIMSHOTTARI_DASHA_YEARS,
                total_years=VIMSHOTTARI_TOTAL_YEARS,
                start_date=current_start,
                end_date=current_end,
                level=2,
                max_depth=max_depth,
            )
            mahadashas.append(
                DashaPeriod(
                    lord=lord,
                    start_date=current_start,
                    end_date=current_end,
                    duration_days=md_days,
                    level=1,
                    sub_periods=subs,
                )
            )
            current_start = current_end

        return DashaTree(
            system="vimshottari",
            birth_date=b_date,
            trigger_planet=start_lord,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=tuple(mahadashas),
            max_depth=max_depth,
            total_cycle_years=VIMSHOTTARI_TOTAL_YEARS,
            year_convention=year_convention,
            balance_at_birth=balance_years,
            moon_longitude_at_trigger=varga_moon_lon,
        )

    def get_active_varga_dasha(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_code: str,
        target_date: date,
        max_depth: int = 5,
        ayanamsa: str = "lahiri",
        year_convention: str = "365.25_solar",
        arsha_mode: str = "standard",
    ) -> JhaActiveVargaDasha:
        """Retrieves active 5-level Vimshottari lords and sandhi/chhidra flags at target date."""
        v_clean = varga_code.upper().strip()
        tree = self.compute_varga_dasha_tree(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            varga_code=v_clean,
            max_depth=max_depth,
            ayanamsa=ayanamsa,
            year_convention=year_convention,
            arsha_mode=arsha_mode,
        )
        active_nodes = find_active_dasha_chain(tree, target_date)
        lords = [n.lord.lower() for n in active_nodes]

        # Fill up to 5 levels
        md_lord = lords[0] if len(lords) > 0 else "ketu"
        ad_lord = lords[1] if len(lords) > 1 else md_lord
        pd_lord = lords[2] if len(lords) > 2 else ad_lord
        sd_lord = lords[3] if len(lords) > 3 else pd_lord
        pad_lord = lords[4] if len(lords) > 4 else sd_lord

        md_node = active_nodes[0] if len(active_nodes) > 0 else None
        ad_node = active_nodes[1] if len(active_nodes) > 1 else None

        # Dasha Sandhi & Chhidra evaluation
        is_sandhi = False
        is_chhidra = False
        days_to_end = 0
        sandhi_reasons = []

        if md_node and md_node.start_date and md_node.end_date:
            md_start = md_node.start_date if isinstance(md_node.start_date, date) else md_node.start_date.date()
            md_end = md_node.end_date if isinstance(md_node.end_date, date) else md_node.end_date.date()
            days_to_end = (md_end - target_date).days
            days_from_start = (target_date - md_start).days

            # 180-day transition junction buffer
            if 0 <= days_to_end <= 180:
                is_sandhi = True
                sandhi_reasons.append(f"Terminal Sandhi: {days_to_end} days remaining in {md_lord.capitalize()} Mahadasha.")
            elif 0 <= days_from_start <= 180:
                is_sandhi = True
                sandhi_reasons.append(f"Entry Sandhi: {days_from_start} days elapsed into {md_lord.capitalize()} Mahadasha.")

        # Dasha Chhidra: last Antardasha of Mahadasha (9th sub-period)
        if md_lord in VIMSHOTTARI_SEQUENCE and ad_lord in VIMSHOTTARI_SEQUENCE:
            md_idx = VIMSHOTTARI_SEQUENCE.index(md_lord)
            last_ad_lord = VIMSHOTTARI_SEQUENCE[(md_idx + 8) % 9]
            if ad_lord == last_ad_lord:
                is_chhidra = True
                sandhi_reasons.append(f"Dasha Chhidra: {ad_lord.capitalize()} is the terminal Antardasha of {md_lord.capitalize()} MD.")

        notes = "; ".join(sandhi_reasons) if sandhi_reasons else "Normal operating dasha window."

        return JhaActiveVargaDasha(
            varga_code=v_clean,
            evaluation_date=target_date,
            mahadasha_lord=md_lord,
            antardasha_lord=ad_lord,
            pratyantardasha_lord=pd_lord,
            sookshma_lord=sd_lord,
            praana_lord=pad_lord,
            dasha_chain=tuple(lords),
            md_start_date=md_node.start_date if md_node else target_date,
            md_end_date=md_node.end_date if md_node else target_date,
            ad_start_date=ad_node.start_date if ad_node else target_date,
            ad_end_date=ad_node.end_date if ad_node else target_date,
            is_dasha_sandhi=is_sandhi,
            is_dasha_chhidra=is_chhidra,
            days_to_md_end=max(0, days_to_end),
            sandhi_notes=notes,
        )

    def compare_d1_and_varga_strength(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_code: str,
        target_date: date,
        ayanamsa: str = "lahiri",
        year_convention: str = "365.25_solar",
        arsha_mode: str = "standard",
    ) -> JhaDashaStrengthComparison:
        """
        Implements Jha's exact Shastric Rule:
        "Divisional charts should NOT override D1 prediction unless their current
         Vimshottari planet's Final Strength exceeds D1's."
        """
        v_clean = varga_code.upper().strip()

        # 1. Get active lords
        d1_active = self.get_active_varga_dasha(
            birth_datetime, latitude, longitude, "D1", target_date, ayanamsa=ayanamsa, year_convention=year_convention, arsha_mode=arsha_mode
        )
        varga_active = self.get_active_varga_dasha(
            birth_datetime, latitude, longitude, v_clean, target_date, ayanamsa=ayanamsa, year_convention=year_convention, arsha_mode=arsha_mode
        )

        d1_lord = d1_active.antardasha_lord
        varga_lord = varga_active.antardasha_lord

        # 2. Get chart positions
        d1_chart = self._horoscope_engine.generate_d1(birth_datetime, latitude, longitude, ayanamsa=ayanamsa)
        chart_positions = {p.planet: p.sidereal_longitude for p in d1_chart.planets}

        # 3. Calculate D1 Lord Strength
        d1_p_lon = chart_positions.get(d1_lord, 0.0)
        d1_dignity = JhaDignityEngine.evaluate_planet_dignity(
            planet=d1_lord,
            sidereal_lon=d1_p_lon,
            chart_planet_positions=chart_positions,
            varga_code="D1",
            vimshopaka_weight=VIMSHOPAKA_WEIGHTS.get("D1", 6.0),
        )

        # 4. Calculate Varga Lord Strength
        varga_weight = VIMSHOPAKA_WEIGHTS.get(v_clean, 1.5)
        varga_p_lon = chart_positions.get(varga_lord, 0.0)
        varga_dignity = JhaDignityEngine.evaluate_planet_dignity(
            planet=varga_lord,
            sidereal_lon=varga_p_lon,
            chart_planet_positions=chart_positions,
            varga_code=v_clean,
            vimshopaka_weight=varga_weight,
        )

        # 5. Shastric Override Test
        can_override = varga_dignity.final_varga_strength > d1_dignity.final_varga_strength

        if can_override:
            explanation = (
                f"Varga {v_clean} active lord {varga_lord.capitalize()} Final Strength ({varga_dignity.final_varga_strength:.2f}) "
                f"exceeds D1 active lord {d1_lord.capitalize()} Final Strength ({d1_dignity.final_varga_strength:.2f}). "
                f"Varga {v_clean} has Shastric authority to override D1."
            )
        else:
            explanation = (
                f"D1 active lord {d1_lord.capitalize()} Final Strength ({d1_dignity.final_varga_strength:.2f}) "
                f"is dominant over {v_clean} active lord {varga_lord.capitalize()} Final Strength ({varga_dignity.final_varga_strength:.2f}). "
                f"Varga {v_clean} cannot override D1 natal promise."
            )

        return JhaDashaStrengthComparison(
            varga_code=v_clean,
            evaluation_date=target_date,
            d1_active_lord=d1_lord,
            d1_main_strength=d1_dignity.main_strength,
            d1_final_strength=d1_dignity.final_varga_strength,
            varga_active_lord=varga_lord,
            varga_main_strength=varga_dignity.main_strength,
            varga_final_strength=varga_dignity.final_varga_strength,
            varga_overrides_d1=can_override,
            verdict_explanation=explanation,
        )
