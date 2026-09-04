"""
AstroOS — Divisional Explorer Service
=====================================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Steps 3, 6 & 7)
Provides comprehensive multi-varga analysis for any requested divisional chart (D1..D60):
1. Calculates divisional planetary longitudes, rashis, and houses.
2. Evaluates Bhavottama (Kimshukadi) status relative to D1 houses.
3. Computes independent 5-level Divisional Vimshottari Dasha for that varga.
4. Performs Dual-Dasha Confluence Comparison (D1 Active Lords vs Dn Active Lords).
5. Calculates Vimshopaka strength and Neecha Bhanga status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.dasha import DashaTree
from apps.api.services.divisional_engine import DivisionalEngine, compute_varga_sign
from apps.api.services.divisional_vimshottari_engine import (
    DivisionalDashaActiveLords,
    DivisionalVimshottariEngine,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.bhavottama_engine import BhavottamaEngine, BhavottamaStatus
from apps.api.services.phalita_core.varga_strength_fusion import (
    DualDashaVargaComparison,
    PlanetVargaStrengthDetail,
    VargaStrengthFusionEngine,
)
from packages.shared.constants import KALACHAKRA_SAVYA_SIGNS, SIGN_LORDS


@dataclass(frozen=True)
class DivisionalPlanetPosition:
    planet: str
    rashi: str
    rashi_index: int
    rashi_degree: float
    house_number: int
    is_bhavottama: bool
    bhavottama_type: str
    dignity_label: str
    dignity_score: int
    final_varga_strength: float
    is_debilitation_cancelled: bool


@dataclass(frozen=True)
class DivisionalExplorationResult:
    varga_code: str                  # e.g., "D9", "D10", "D7"
    varga_number: int                # e.g., 9, 10, 7
    varga_name: str                  # e.g., "Navamsha", "Dashamsha"
    significations: str              # What this varga represents
    vimshopaka_weight: float         # e.g., 3.0, 2.0, 1.5
    ascendant_rashi: str
    ascendant_rashi_idx: int
    ascendant_degree: float
    planets: Tuple[DivisionalPlanetPosition, ...]
    bhavottama_planets: Tuple[str, ...]
    active_divisional_dasha: DivisionalDashaActiveLords
    dual_dasha_comparison: DualDashaVargaComparison
    shastric_confluence_summary: str


class DivisionalExplorerService:
    """
    Master service for deep multi-varga exploration, dasha confluence, and Bhavottama diagnostics.
    """

    VARGA_METADATA: Dict[int, Dict[str, Any]] = {
        1: {"code": "D1", "name": "Rashi", "theme": "Physical existence, overall vitality, general fortune", "weight": 3.0},
        2: {"code": "D2", "name": "Hora", "theme": "Wealth, liquid assets, financial prosperity", "weight": 1.5},
        3: {"code": "D3", "name": "Drekkana", "theme": "Siblings, vitality, courage, enterprise", "weight": 1.5},
        4: {"code": "D4", "name": "Chaturthamsha", "theme": "Fixed property, conveyances, landed fortune, residence", "weight": 1.5},
        7: {"code": "D7", "name": "Saptamsha", "theme": "Progeny, children, creative manifestation, Purvapunya", "weight": 1.5},
        9: {"code": "D9", "name": "Navamsha", "theme": "Dharma, marital harmony, spouse, inner spiritual baseline", "weight": 3.0},
        10: {"code": "D10", "name": "Dashamsha", "theme": "Career, public standing, executive power, professional Rajayogas", "weight": 2.0},
        12: {"code": "D12", "name": "Dwadashamsha", "theme": "Parents, lineage, ancestral karma, father/mother roots", "weight": 1.0},
        24: {"code": "D24", "name": "Chaturvimshamsha", "theme": "Higher education, learning, scholastic achievements, skills", "weight": 1.0},
        30: {"code": "D30", "name": "Trimshamsha", "theme": "Misfortunes, evils, chronic friction, Arishta mitigation", "weight": 1.0},
        60: {"code": "D60", "name": "Shashtiamsha", "theme": "Detailed past-life karma, ultimate auspiciousness arbiter", "weight": 4.0},
    }

    def __init__(self, ephem_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephem_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horo_engine = HoroscopeEngine(self._wrapper)
        self._div_dasha_engine = DivisionalVimshottariEngine(self._wrapper)

    def explore_varga(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        varga_number: int = 9,
        target_date: Optional[date] = None,
        ayanamsa: str = "lahiri",
    ) -> DivisionalExplorationResult:
        """
        Generates full analytical exploration of any divisional chart.
        """
        if birth_datetime.tzinfo is None:
            birth_datetime = birth_datetime.replace(tzinfo=timezone.utc)

        t_date = target_date or birth_datetime.date()
        v_num = int(varga_number)
        meta = self.VARGA_METADATA.get(v_num, {
            "code": f"D{v_num}",
            "name": f"Divisional D{v_num}",
            "theme": "Harmonic subdivision",
            "weight": 1.0,
        })
        v_code = meta["code"]

        # 1. Generate D1 Baseline Chart
        d1_chart = self._horo_engine.generate_d1(
            birth_datetime_utc=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )

        d1_lagna_lon = d1_chart.ascendant.sidereal_longitude
        d1_lagna_rashi_idx = int(d1_lagna_lon / 30.0) % 12

        d1_planet_houses: Dict[str, int] = {}
        d1_planet_signs: Dict[str, int] = {}
        for p in d1_chart.planets:
            p_name = p.planet.lower()
            p_sign = int(p.sidereal_longitude / 30.0) % 12
            p_house = ((p_sign - d1_lagna_rashi_idx) % 12) + 1
            d1_planet_houses[p_name] = p_house
            d1_planet_signs[p_name] = p_sign

        # 2. Compute Divisional Ascendant (Lagna)
        v_lagna_rashi_name, v_lagna_deg = compute_varga_sign(v_code, d1_lagna_lon)
        v_lagna_rashi_clean = v_lagna_rashi_name.lower()
        v_lagna_rashi_idx = KALACHAKRA_SAVYA_SIGNS.index(v_lagna_rashi_clean) if v_lagna_rashi_clean in KALACHAKRA_SAVYA_SIGNS else 0

        # 3. Compute D9 and D10 Houses (for Tri-Bhavottama verification)
        d9_planet_houses: Dict[str, int] = {}
        d10_planet_houses: Dict[str, int] = {}

        # D9 Lagna
        d9_lagna_rashi, _ = compute_varga_sign("D9", d1_lagna_lon)
        d9_lagna_idx = KALACHAKRA_SAVYA_SIGNS.index(d9_lagna_rashi.lower()) if d9_lagna_rashi.lower() in KALACHAKRA_SAVYA_SIGNS else 0

        # D10 Lagna
        d10_lagna_rashi, _ = compute_varga_sign("D10", d1_lagna_lon)
        d10_lagna_idx = KALACHAKRA_SAVYA_SIGNS.index(d10_lagna_rashi.lower()) if d10_lagna_rashi.lower() in KALACHAKRA_SAVYA_SIGNS else 0

        for p in d1_chart.planets:
            p_name = p.planet.lower()
            # D9
            r9, _ = compute_varga_sign("D9", p.sidereal_longitude)
            s9_idx = KALACHAKRA_SAVYA_SIGNS.index(r9.lower()) if r9.lower() in KALACHAKRA_SAVYA_SIGNS else 0
            d9_planet_houses[p_name] = ((s9_idx - d9_lagna_idx) % 12) + 1
            # D10
            r10, _ = compute_varga_sign("D10", p.sidereal_longitude)
            s10_idx = KALACHAKRA_SAVYA_SIGNS.index(r10.lower()) if r10.lower() in KALACHAKRA_SAVYA_SIGNS else 0
            d10_planet_houses[p_name] = ((s10_idx - d10_lagna_idx) % 12) + 1

        # 4. Compute Positions for Requested Varga
        planet_positions_list: List[DivisionalPlanetPosition] = []
        bhavottama_planets_found: List[str] = []

        # Find sign occupants in this varga for Neecha Bhanga evaluation
        varga_sign_occupants: Dict[int, List[str]] = {i: [] for i in range(12)}
        varga_planets_raw: List[Tuple[str, str, int, float, int]] = []

        for p in d1_chart.planets:
            p_name = p.planet.lower()
            v_rashi, v_deg = compute_varga_sign(v_code, p.sidereal_longitude)
            v_r_clean = v_rashi.lower()
            v_r_idx = KALACHAKRA_SAVYA_SIGNS.index(v_r_clean) if v_r_clean in KALACHAKRA_SAVYA_SIGNS else 0
            v_house = ((v_r_idx - v_lagna_rashi_idx) % 12) + 1
            varga_sign_occupants[v_r_idx].append(p_name)
            varga_planets_raw.append((p_name, v_rashi.capitalize(), v_r_idx, v_deg, v_house))

        for p_name, v_rashi, v_r_idx, v_deg, v_house in varga_planets_raw:
            d1_h = d1_planet_houses.get(p_name, 1)
            is_bhav = (v_house == d1_h)
            if is_bhav:
                bhavottama_planets_found.append(p_name.capitalize())

            # Evaluate Bhavottama status
            b_status = BhavottamaEngine.evaluate_planet(
                planet=p_name.capitalize(),
                d1_house=d1_h,
                d9_house=d9_planet_houses.get(p_name, 1),
                d10_house=d10_planet_houses.get(p_name, 1),
                d1_sign_idx=d1_planet_signs.get(p_name, 0),
            )

            # Evaluate Varga Strength
            strength_det = VargaStrengthFusionEngine.evaluate_planet_varga_strength(
                planet=p_name,
                varga_number=v_num,
                sign_index=v_r_idx,
                sign_occupants=tuple(varga_sign_occupants[v_r_idx]),
            )

            b_type = "None"
            if b_status.is_tri_bhavottama:
                b_type = "Tri-Bhavottama (Kimshuka)"
            elif b_status.is_d1_d9_bhavottama and v_num == 9:
                b_type = "Navamsha Bhavottama"
            elif b_status.is_d1_d10_bhavottama and v_num == 10:
                b_type = "Dashamsha Bhavottama"
            elif is_bhav:
                b_type = f"D{v_num} Bhavottama"

            planet_positions_list.append(
                DivisionalPlanetPosition(
                    planet=p_name.capitalize(),
                    rashi=v_rashi,
                    rashi_index=v_r_idx,
                    rashi_degree=round(v_deg, 2),
                    house_number=v_house,
                    is_bhavottama=is_bhav,
                    bhavottama_type=b_type,
                    dignity_label=strength_det.dignity_label,
                    dignity_score=strength_det.dignity_score,
                    final_varga_strength=round(strength_det.final_varga_strength, 2),
                    is_debilitation_cancelled=strength_det.is_debilitation_cancelled,
                )
            )

        # 5. Compute Divisional Vimshottari Dasha
        v_tree = self._div_dasha_engine.compute_divisional_vimshottari(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            varga_number=v_num,
            max_depth=3,
        )
        active_div_lords = self._div_dasha_engine.get_active_lords_at_date(
            tree=v_tree,
            target_date=t_date,
            varga_number=v_num,
        )

        # 6. Compute D1 Vimshottari Baseline
        d1_tree = self._div_dasha_engine.compute_divisional_vimshottari(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            varga_number=1,
            max_depth=3,
        )
        active_d1_lords = self._div_dasha_engine.get_active_lords_at_date(
            tree=d1_tree,
            target_date=t_date,
            varga_number=1,
        )

        # 7. Dual Dasha Comparison
        dual_comp = VargaStrengthFusionEngine.compare_dual_dashas(
            domain=meta["name"].lower(),
            target_varga=v_num,
            d1_md_lord=active_d1_lords.mahadasha_lord,
            d1_ad_lord=active_d1_lords.antardasha_lord,
            div_md_lord=active_div_lords.mahadasha_lord,
            div_ad_lord=active_div_lords.antardasha_lord,
            d1_planet_signs=d1_planet_signs,
            div_planet_signs={p.planet.lower(): p.rashi_index for p in planet_positions_list},
        )

        confluence_summary = (
            f"{v_code} ({meta['name']}) analysis at target date {t_date.isoformat()}: "
            f"Active D{v_num} Dasha = {active_div_lords.mahadasha_lord}-{active_div_lords.antardasha_lord}. "
            f"D1 Baseline Dasha = {active_d1_lords.mahadasha_lord}-{active_d1_lords.antardasha_lord}. "
            f"{dual_comp.siddhantic_verdict}"
        )

        return DivisionalExplorationResult(
            varga_code=v_code,
            varga_number=v_num,
            varga_name=meta["name"],
            significations=meta["theme"],
            vimshopaka_weight=meta["weight"],
            ascendant_rashi=v_lagna_rashi_name.capitalize(),
            ascendant_rashi_idx=v_lagna_rashi_idx,
            ascendant_degree=round(v_lagna_deg, 2),
            planets=tuple(planet_positions_list),
            bhavottama_planets=tuple(bhavottama_planets_found),
            active_divisional_dasha=active_div_lords,
            dual_dasha_comparison=dual_comp,
            shastric_confluence_summary=confluence_summary,
        )
