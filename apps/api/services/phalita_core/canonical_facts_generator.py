"""
AstroOS — Canonical Facts Generator
====================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md
MANDATORY DIRECTIVE: Calculation-Only Layer.
- Contains PURE astronomical, mathematical, and Ephemeris calculations.
- ZERO prediction, ZERO interpretation, and ZERO rule weighting permitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.dasha import DashaTree
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.bhavachalita_engine import VishamabhavaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import DivisionalEngine, compute_varga_sign
from apps.api.services.divisional_vimshottari_engine import (
    DivisionalDashaActiveLords,
    DivisionalVimshottariEngine,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.intelligence.strength_model import DignityScore, StrengthModel
from apps.api.services.phalita_core.bhavottama_engine import BhavottamaEngine, BhavottamaStatus
from apps.api.services.phalita_core.karakamsha_synthesis_engine import (
    CharaKarakaAssignment,
    KarakamshaSynthesisEngine,
    KarakamshaSynthesisResult,
)
from apps.api.services.phalita_core.varga_strength_fusion import (
    PlanetVargaStrengthDetail,
    VargaStrengthFusionEngine,
)
from apps.api.services.upagraha_engine import UpagrahaEngine, UpagrahaReport
from packages.shared.constants import KALACHAKRA_SAVYA_SIGNS, SIGN_LORDS


@dataclass(frozen=True)
class PlanetCanonicalFact:
    planet: str
    sidereal_longitude: float
    rashi_name: str
    rashi_index: int
    rashi_degree: float
    speed_deg_per_day: float
    is_retrograde: bool
    dignity_score: int         # 1 to 9 discrete dignity score
    dignity_label: str
    is_debilitation_cancelled: bool
    house_from_lagna: int
    house_from_chandra: int
    bhavachalita_house: int


@dataclass(frozen=True)
class BhavaCanonicalFact:
    house_number: int
    starting_cusp: float
    middle_cusp: float
    ending_cusp: float
    rashi_at_middle: str
    rashi_index: int
    bhava_lord: str
    occupants: Tuple[str, ...]


@dataclass(frozen=True)
class VargaPlanetFact:
    planet: str
    varga_code: str
    varga_number: int
    rashi_name: str
    rashi_index: int
    rashi_degree: float
    house_number: int
    is_bhavottama: bool


@dataclass(frozen=True)
class UpagrahaFact:
    name: str
    sidereal_longitude: float
    rashi_name: str
    rashi_index: int
    rashi_degree: float
    house_number: int


@dataclass(frozen=True)
class CanonicalFacts:
    """
    Immutable, pure calculation-only ground truth representation of a nativity.
    """
    birth_datetime_utc: datetime
    latitude: float
    longitude: float
    ayanamsa: str
    target_evaluation_date: date

    # Coordinates & Positions
    ascendant_longitude: float
    ascendant_rashi: str
    ascendant_rashi_idx: int
    ascendant_degree: float

    chandra_longitude: float
    chandra_rashi: str
    chandra_rashi_idx: int

    planets: Tuple[PlanetCanonicalFact, ...]
    bhavachalita_houses: Tuple[BhavaCanonicalFact, ...]
    vargas: Tuple[VargaPlanetFact, ...]
    chara_karakas: Tuple[CharaKarakaAssignment, ...]
    karakamsha_lagna_rashi: str
    karakamsha_lagna_rashi_idx: int
    upagrahas: Tuple[UpagrahaFact, ...]

    # Ashtakavarga Rekhas
    sarvashtakavarga_rekhas: Tuple[int, ...]     # 12 elements (House 1..12 or Sign 0..11)
    bhinnashtakavarga_matrix: Dict[str, Tuple[int, ...]]

    # Active 5-Level Dasha Periods at target date
    active_d1_dasha: Dict[str, str]              # {"MD": ..., "AD": ..., "PD": ..., "Sookshma": ..., "Praana": ...}
    active_divisional_dashas: Dict[int, DivisionalDashaActiveLords]


class CanonicalFactsGenerator:
    """
    Strict calculation-only engine producing deterministic CanonicalFacts.
    """

    CORE_VARGAS = (1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)

    def __init__(self, ephem_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephem_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horo_engine = HoroscopeEngine(self._wrapper)
        self._dasha_engine = DashaEngine(self._wrapper)
        self._div_dasha_engine = DivisionalVimshottariEngine(self._wrapper)
        self._upagraha_engine = UpagrahaEngine(self._wrapper)
        self._ashtakavarga_engine = AshtakavargaEngine()
        self._bhavachalita_engine = VishamabhavaEngine(self._wrapper)



    def generate_facts(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        target_date: Optional[date] = None,
        ayanamsa: str = "lahiri",
    ) -> CanonicalFacts:
        """
        Produces pure calculation-only CanonicalFacts.
        """
        if birth_datetime.tzinfo is None:
            birth_datetime = birth_datetime.replace(tzinfo=timezone.utc)

        t_date = target_date or birth_datetime.date()

        # 1. Ephemeris & D1 Chart
        calc_res = self._wrapper.calculate(
            dt=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        asc_lon = getattr(calc_res.ascendant, "sidereal_longitude", getattr(calc_res.ascendant, "longitude", 0.0))
        lagna_rashi_idx = int(asc_lon / 30.0) % 12
        lagna_deg = asc_lon % 30.0
        lagna_rashi_name = KALACHAKRA_SAVYA_SIGNS[lagna_rashi_idx].capitalize()

        # 2. Bhavachalita Calculation
        self._bhavachalita_engine = VishamabhavaEngine(self._wrapper)
        bhava_chart = self._bhavachalita_engine.compute_bhavachalita(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        bhava_facts: List[BhavaCanonicalFact] = []
        bhava_occupants: Dict[int, List[str]] = {h: [] for h in range(1, 13)}

        # 3. Planet Longitudes & Dignities
        planet_lons: Dict[str, float] = {}
        planet_facts: List[PlanetCanonicalFact] = []
        chandra_lon = 0.0
        chandra_rashi_idx = 0

        # Sign Occupants for Neecha Bhanga evaluation
        sign_occupants: Dict[int, List[str]] = {i: [] for i in range(12)}
        for p in calc_res.planet_positions:
            p_name = p.planet.lower()
            p_lon = getattr(p, "sidereal_longitude", getattr(p, "longitude", 0.0))
            planet_lons[p_name] = p_lon
            r_idx = int(p_lon / 30.0) % 12
            sign_occupants[r_idx].append(p_name)
            if p_name == "moon":
                chandra_lon = p_lon
                chandra_rashi_idx = r_idx

        # Calculate Bhavachalita house for each planet
        planet_bhava_map: Dict[str, int] = {}
        for p_name in planet_lons.keys():
            b_house = bhava_chart.planet_bhava_placements.get(p_name.capitalize(), bhava_chart.planet_bhava_placements.get(p_name, 1))
            planet_bhava_map[p_name] = b_house
            bhava_occupants[b_house].append(p_name.capitalize())

        # Construct BhavaCanonicalFacts
        for h_num in range(1, 13):
            cusp_info = bhava_chart.houses[h_num - 1]
            m_rashi_idx = int(cusp_info.madhya / 30.0) % 12
            bhava_facts.append(
                BhavaCanonicalFact(
                    house_number=h_num,
                    starting_cusp=round(cusp_info.start_sandhi, 4),
                    middle_cusp=round(cusp_info.madhya, 4),
                    ending_cusp=round(cusp_info.end_sandhi, 4),
                    rashi_at_middle=cusp_info.primary_rashi.capitalize(),
                    rashi_index=m_rashi_idx,
                    bhava_lord=cusp_info.primary_lord.capitalize(),
                    occupants=tuple(bhava_occupants[h_num]),
                )
            )


        for p in calc_res.planet_positions:
            p_name = p.planet.lower()
            p_lon = planet_lons[p_name]
            r_idx = int(p_lon / 30.0) % 12
            r_deg = p_lon % 30.0
            r_name = KALACHAKRA_SAVYA_SIGNS[r_idx].capitalize()

            h_lagna = ((r_idx - lagna_rashi_idx) % 12) + 1
            h_chandra = ((r_idx - chandra_rashi_idx) % 12) + 1
            b_house = planet_bhava_map.get(p_name, h_lagna)

            # Dignity & Debilitation Cancellation
            strength_det = VargaStrengthFusionEngine.evaluate_planet_varga_strength(
                planet=p_name,
                varga_number=1,
                sign_index=r_idx,
                sign_occupants=tuple(sign_occupants[r_idx]),
            )

            planet_facts.append(
                PlanetCanonicalFact(
                    planet=p.planet.capitalize(),
                    sidereal_longitude=round(p_lon, 4),
                    rashi_name=r_name,
                    rashi_index=r_idx,
                    rashi_degree=round(r_deg, 4),
                    speed_deg_per_day=round(getattr(p, "speed", 1.0), 4),
                    is_retrograde=getattr(p, "is_retrograde", False),
                    dignity_score=strength_det.dignity_score,
                    dignity_label=strength_det.dignity_label,
                    is_debilitation_cancelled=strength_det.is_debilitation_cancelled,
                    house_from_lagna=h_lagna,
                    house_from_chandra=h_chandra,
                    bhavachalita_house=b_house,
                )
            )

        # 4. Vargas Calculation ($D_1$ to $D_{60}$)
        varga_facts: List[VargaPlanetFact] = []
        d1_house_map = {p.planet.lower(): p.house_from_lagna for p in planet_facts}

        for v_num in self.CORE_VARGAS:
            v_code = f"D{v_num}"
            # Varga Lagna
            v_lagna_rashi, _ = compute_varga_sign(v_code, asc_lon)
            v_lagna_r_idx = KALACHAKRA_SAVYA_SIGNS.index(v_lagna_rashi.lower()) if v_lagna_rashi.lower() in KALACHAKRA_SAVYA_SIGNS else 0

            for p_name, p_lon in planet_lons.items():
                vr_name, vr_deg = compute_varga_sign(v_code, p_lon)
                vr_idx = KALACHAKRA_SAVYA_SIGNS.index(vr_name.lower()) if vr_name.lower() in KALACHAKRA_SAVYA_SIGNS else 0
                v_house = ((vr_idx - v_lagna_r_idx) % 12) + 1
                is_bhav = (v_house == d1_house_map.get(p_name, 1))

                varga_facts.append(
                    VargaPlanetFact(
                        planet=p_name.capitalize(),
                        varga_code=v_code,
                        varga_number=v_num,
                        rashi_name=vr_name.capitalize(),
                        rashi_index=vr_idx,
                        rashi_degree=round(vr_deg, 4),
                        house_number=v_house,
                        is_bhavottama=is_bhav,
                    )
                )

        # 5. 7 Chara Karakas & Karakamsha Lagna
        karaka_res = KarakamshaSynthesisEngine.compute_synthesis(
            d1_planet_longitudes=planet_lons,
            d1_lagna_lon=asc_lon,
        )

        # 6. Upagrahas
        upagraha_rep = self._upagraha_engine.compute_upagrahas(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        upagraha_facts: List[UpagrahaFact] = []
        upa_positions = [
            upagraha_rep.dhooma,
            upagraha_rep.vyatipata,
            upagraha_rep.parivesha,
            upagraha_rep.indrachapa,
            upagraha_rep.upaketu,
            upagraha_rep.gulika,
        ]
        for u in upa_positions:
            upagraha_facts.append(
                UpagrahaFact(
                    name=u.name,
                    sidereal_longitude=round(u.longitude, 4),
                    rashi_name=u.rashi.capitalize(),
                    rashi_index=u.rashi_idx,
                    rashi_degree=round(u.degree_in_rashi, 4),
                    house_number=u.house_from_lagna,
                )
            )


        # 7. Ashtakavarga Rekhas
        d1_chart_obj = self._horo_engine.generate_d1(
            birth_datetime_utc=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        bhinna_results = self._ashtakavarga_engine.compute_bhinnashtakavarga(d1_chart_obj)
        sarva_res = self._ashtakavarga_engine.compute_sarvashtakavarga(d1_chart_obj, bhinna_results)

        sav_rekhas = sarva_res.bindus_by_rashi
        bav_matrix = {
            res.target_planet: tuple(res.bindus_by_rashi)
            for res in bhinna_results
        }



        # 8. Active D1 Vimshottari 5-Level Lords
        d1_tree = self._dasha_engine.compute_vimshottari(
            birth_datetime_utc=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            max_depth=5,
        )
        active_d1_map = {"MD": "Sun", "AD": "Sun", "PD": "Sun", "Sookshma": "Sun", "Praana": "Sun"}
        for md in d1_tree.mahadashas:
            if md.contains(t_date):
                active_d1_map["MD"] = md.lord.capitalize()
                for ad in md.sub_periods:
                    if ad.contains(t_date):
                        active_d1_map["AD"] = ad.lord.capitalize()
                        for pd in ad.sub_periods:
                            if pd.contains(t_date):
                                active_d1_map["PD"] = pd.lord.capitalize()
                                for sk in pd.sub_periods:
                                    if sk.contains(t_date):
                                        active_d1_map["Sookshma"] = sk.lord.capitalize()
                                        for pr in sk.sub_periods:
                                            if pr.contains(t_date):
                                                active_d1_map["Praana"] = pr.lord.capitalize()
                                                break
                                        break
                                break
                        break
                break

        # 9. Active Divisional Vimshottari Lords ($D_9, D_{10}, D_7, D_4$)
        active_div_map: Dict[int, DivisionalDashaActiveLords] = {}
        for v_num in (9, 10, 7, 4, 3, 12, 30):
            v_tree = self._div_dasha_engine.compute_divisional_vimshottari(
                birth_datetime=birth_datetime,
                latitude=latitude,
                longitude=longitude,
                varga_number=v_num,
                max_depth=3,
            )
            act_lords = self._div_dasha_engine.get_active_lords_at_date(
                tree=v_tree,
                target_date=t_date,
                varga_number=v_num,
            )
            active_div_map[v_num] = act_lords

        return CanonicalFacts(
            birth_datetime_utc=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            target_evaluation_date=t_date,
            ascendant_longitude=round(asc_lon, 4),
            ascendant_rashi=lagna_rashi_name,
            ascendant_rashi_idx=lagna_rashi_idx,
            ascendant_degree=round(lagna_deg, 4),
            chandra_longitude=round(chandra_lon, 4),
            chandra_rashi=KALACHAKRA_SAVYA_SIGNS[chandra_rashi_idx].capitalize(),
            chandra_rashi_idx=chandra_rashi_idx,
            planets=tuple(planet_facts),
            bhavachalita_houses=tuple(bhava_facts),
            vargas=tuple(varga_facts),
            chara_karakas=karaka_res.chara_karakas,
            karakamsha_lagna_rashi=karaka_res.karakamsha_rashi,
            karakamsha_lagna_rashi_idx=karaka_res.karakamsha_rashi_idx,
            upagrahas=tuple(upagraha_facts),
            sarvashtakavarga_rekhas=sav_rekhas,
            bhinnashtakavarga_matrix=bav_matrix,
            active_d1_dasha=active_d1_map,
            active_divisional_dashas=active_div_map,
        )
