"""
AstroOS — TPhalitCore Engine
============================
Transforms raw Ganita outputs (longitudes, cusps, speeds) into signed numerical
Phalita features strictly following Vinay Jha's 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - Section 4.2: TPhalitCore feature extraction
  - Section 6: Hierarchical UDT generation (Context, Planet, Bhava, Aspect, Yoga, FeatureVector)
  - Section 7 & 8: Varga & Temporal block aggregation
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Dict, List, Optional, Tuple

import swisseph as swe

from apps.api.domain.tphalit_core import (
    ChartLevelEnum,
    TPhalitAspect,
    TPhalitBhava,
    TPhalitContext,
    TPhalitFeatureVector,
    TPhalitPlanet,
    TPhalitYoga,
)
from apps.api.services.bhavachalita_engine import VishamabhavaEngine
from apps.api.services.divisional_synthesis_engine import DivisionalSynthesisEngine, VimshopakaScheme
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.ishta_kashta_engine import IshtaKashtaEngine
from apps.api.services.sudarshana_chakra_engine import SudarshanaChakraEngine
from packages.shared.constants import SIGN_LORDS

# Planet ID Mapping: 1=Sun, 2=Moon, 3=Mars, 4=Mercury, 5=Jupiter, 6=Venus, 7=Saturn, 8=Rahu, 9=Ketu
PLANET_ID_MAP = {
    "sun": 1, "moon": 2, "mars": 3, "mercury": 4,
    "jupiter": 5, "venus": 6, "saturn": 7, "rahu": 8, "ketu": 9,
}

# Natural Nature: Benefics = +1.0, Malefics = -1.0
NATURAL_NATURE_MAP = {
    "jupiter": 1.0, "venus": 1.0, "moon": 0.5, "mercury": 0.25,
    "sun": -0.25, "mars": -1.0, "saturn": -1.0, "rahu": -1.0, "ketu": -1.0,
}

# Special full aspects in BPHS: (Angle in degrees, Virupas/weight)
# All planets have 7th aspect (180°).
# Mars: 4th (90°), 8th (210°)
# Jupiter: 5th (120°), 9th (240°)
# Saturn: 3rd (60°), 10th (270°)
SPECIAL_ASPECT_ANGLES = {
    "mars": [90.0, 180.0, 210.0],
    "jupiter": [120.0, 180.0, 240.0],
    "saturn": [60.0, 180.0, 270.0],
}


def _angular_distance(p1_deg: float, p2_deg: float) -> float:
    """Forward angular distance from p1 to p2 in [0, 360)."""
    return (p2_deg - p1_deg) % 360.0


def _compute_aspect_orb_strength(dist: float, target_angle: float, max_orb: float = 8.0) -> float:
    """Computes continuous strength [0.0, 1.0] with BPHS 8° classical deeptamsha orb falloff."""
    diff = abs((dist - target_angle + 180.0) % 360.0 - 180.0)
    if diff <= max_orb:
        return 1.0 - (diff / max_orb)
    return 0.0



class TPhalitCoreEngine:
    """Canonical feature extractor implementing Jha's TPhalitCore specification."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        ephemeris_path: str = "data/ephemeris",
    ):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.bhava_engine = VishamabhavaEngine(ephemeris_wrapper=self.wrapper)
        self.sc_engine = SudarshanaChakraEngine(ephemeris_wrapper=self.wrapper)
        self.div_engine = DivisionalSynthesisEngine(ephemeris_wrapper=self.wrapper)

    def extract_features(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        topic_id: int = 1,  # 1 = Jataka
        chart_level: ChartLevelEnum = ChartLevelEnum.ANNUAL,
        varga_id: int = 1,  # D1
        target_value: Optional[float] = None,
    ) -> TPhalitFeatureVector:
        """
        Extracts the full signed numerical feature vector per Section 6 of phalita-moe-ai-model.md.
        """
        # 1. Ephemeris & Vishamabhava Bhaavachalita
        ephem = self.wrapper.calculate(dt=birth_datetime_utc, latitude=latitude, longitude=longitude)
        chart = self.bhava_engine.compute_bhavachalita(
            birth_datetime=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
        )

        # 2. Sudarshana Chakra for Functional Nature
        sun_p = next(p for p in ephem.planet_positions if p.planet.lower() == "sun")
        moon_p = next(p for p in ephem.planet_positions if p.planet.lower() == "moon")
        sc_rep = self.sc_engine.analyze(
            lagna_deg=chart.lagna_madhya,
            sun_deg=sun_p.sidereal_longitude,
            moon_deg=moon_p.sidereal_longitude,
        )

        # 3. TPhalitContext (Section 6.1)
        jd_ut = ephem.julian_day
        dt_str = birth_datetime_utc.isoformat()
        v_weight = self.div_engine.get_varga_weight(varga_id, VimshopakaScheme.SHODASHAVARGA)
        
        context = TPhalitContext(
            TopicID=topic_id,
            TimeJD=jd_ut,
            DateTimeText=dt_str,
            ChartLevel=int(chart_level),
            VargaID=varga_id,
            DegreePoint=round(sun_p.sidereal_longitude, 4),
            TemporalWeight=1.0,
            VargaWeight=v_weight,
            TargetHorizon=365,
        )

        # 4. TPhalitPlanet list (Section 6.2)
        planets_list: List[TPhalitPlanet] = []
        planet_pos_map = {p.planet.lower(): p for p in ephem.planet_positions}
        planet_final_scores: Dict[str, float] = {}

        for p_name, p_id in PLANET_ID_MAP.items():
            pos = planet_pos_map.get(p_name)
            if not pos:
                continue

            house_num = chart.planet_bhava_placements.get(p_name.capitalize(), 1)
            sign_num = int(pos.sidereal_longitude / 30.0) + 1

            nat_nat = NATURAL_NATURE_MAP.get(p_name, 0.0)
            if p_name == "mercury":
                # BPHS Rule: Mercury takes the nature of its conjunctions
                co_occupants = [p.lower() for p, h in chart.planet_bhava_placements.items() if h == house_num and p.lower() != "mercury"]
                malefics = {"sun", "mars", "saturn", "rahu", "ketu"}
                benefics = {"jupiter", "venus", "moon"}
                has_malefic = any(p in malefics for p in co_occupants)
                has_benefic = any(p in benefics for p in co_occupants)
                if has_malefic and not has_benefic:
                    nat_nat = -1.0
                elif has_benefic and not has_malefic:
                    nat_nat = 1.0
                else:
                    nat_nat = 0.5  # Pure benefic when alone or unafflicted

            sc_prof = sc_rep.profiles.get(p_name.capitalize())
            func_nat = float(sc_prof.net_functional_score) if sc_prof else 0.0


            dig_val = pos.dignity.value if pos.dignity else "sama"
            m_str = IshtaKashtaEngine.get_main_strength(dig_val, is_retrograde=pos.is_retrograde)
            dig_raw = float(m_str.main_strength_rank)
            dig_weight = float(m_str.main_strength_score)  # 0 to 60 BPHS score

            # Final signed effect [-1.0, +1.0]
            # Normalizes dignity weight (0 to 60) and combines with functional polarity
            norm_dignity = (dig_weight - 30.0) / 30.0  # [-1.0, +1.0]
            final_effect = round(0.5 * norm_dignity + 0.5 * (func_nat / 3.0 if func_nat != 0 else nat_nat), 4)
            final_effect = max(-1.0, min(1.0, final_effect))
            planet_final_scores[p_name] = final_effect

            planets_list.append(
                TPhalitPlanet(
                    PlanetID=p_id,
                    PlanetName=p_name.capitalize(),
                    NaturalNature=nat_nat,
                    FunctionalNature=func_nat,
                    HouseID=house_num,
                    SignID=sign_num,
                    DignityRaw=dig_raw,
                    DignityWeight=dig_weight,
                    LordshipWeight=1.0,
                    KarakaWeight=1.0,
                    AspectContribution=0.0,
                    YogaContribution=0.0,
                    FinalSignedEffect=final_effect,
                )
            )

        # 5. TPhalitAspect list (Section 6.4)
        aspects_list: List[TPhalitAspect] = []
        aspect_block_total = 0.0

        for p_from_name, p_from_id in PLANET_ID_MAP.items():
            from_pos = planet_pos_map.get(p_from_name)
            if not from_pos or p_from_name in ["rahu", "ketu"]:
                continue

            angles = SPECIAL_ASPECT_ANGLES.get(p_from_name, [180.0])
            for p_to_name, p_to_id in PLANET_ID_MAP.items():
                if p_from_name == p_to_name:
                    continue
                to_pos = planet_pos_map.get(p_to_name)
                if not to_pos:
                    continue

                dist = _angular_distance(from_pos.sidereal_longitude, to_pos.sidereal_longitude)
                for target_ang in angles:
                    str_val = _compute_aspect_orb_strength(dist, target_ang)
                    if str_val > 0.01:
                        signed_force = round(str_val * planet_final_scores.get(p_from_name, 0.0), 4)
                        aspect_block_total += signed_force
                        aspects_list.append(
                            TPhalitAspect(
                                FromPlanet=p_from_id,
                                ToDegree=round(to_pos.sidereal_longitude, 4),
                                AngularDistance=round(dist, 4),
                                AspectType=int(target_ang / 30.0),
                                AspectStrength=round(str_val, 4),
                                SignedEffect=signed_force,
                            )
                        )

        # 6. TPhalitBhava list (Section 6.3)
        bhavas_list: List[TPhalitBhava] = []
        bhava_block_total = 0.0

        for i, span in enumerate(chart.houses):
            h_id = span.house_number
            pri_rashi_idx = int(span.madhya / 30.0) + 1
            pri_lord = span.primary_lord.lower()
            lord_id = PLANET_ID_MAP.get(pri_lord, 1)

            # Count occupants in this Vishamabhava house
            occupants = [p for p, h in chart.planet_bhava_placements.items() if h == h_id]
            occ_count = len(occupants)
            occ_effect = sum(planet_final_scores.get(p.lower(), 0.0) for p in occupants)

            # Lord strength
            lord_score = planet_final_scores.get(pri_lord, 0.0)
            
            # Final bhava score
            final_bhava = round(0.6 * lord_score + 0.4 * (occ_effect / occ_count if occ_count > 0 else 0.0), 4)
            final_bhava = max(-1.0, min(1.0, final_bhava))
            bhava_block_total += final_bhava

            bhavas_list.append(
                TPhalitBhava(
                    BhavaID=h_id,
                    SignID=pri_rashi_idx,
                    LordID=lord_id,
                    OccupantCount=occ_count,
                    LordStrength=lord_score,
                    OccupantEffect=round(occ_effect, 4),
                    AspectEffect=0.0,
                    YogaEffect=0.0,
                    FinalBhavaScore=final_bhava,
                )
            )

        # 7. TPhalitYoga list (Section 6.5)
        # 7. TPhalitYoga list (Section 6.5)
        yogas_list: List[TPhalitYoga] = []
        yoga_block_total = 0.0

        # ── A. Gaja-Kesari Yoga (Jupiter in Kendra from Moon) ─────────────────
        jup_house = chart.planet_bhava_placements.get("Jupiter", 1)
        moon_house = chart.planet_bhava_placements.get("Moon", 1)
        kendra_from_moon = ((jup_house - moon_house) % 12) in [0, 3, 6, 9]  # 1st, 4th, 7th, 10th
        if kendra_from_moon:
            gk_signed = 1.0  # High auspicious expansion
            yoga_block_total += gk_signed
            yogas_list.append(
                TPhalitYoga(
                    YogaID=101,
                    YogaName="GajaKesari",
                    YogaClass=1,  # Raja Yoga
                    IsActive=True,
                    RawStrength=60.0,
                    SignedEffect=gk_signed,
                    CancelsFeatures="",
                    SuppressesFeatures="",
                    AmplifiesFeatures="D1_Jupiter_FinalSigned;D1_Moon_FinalSigned;D1_H1_FinalScore;D1_H10_FinalScore",
                    FinalContribution=gk_signed,
                )
            )

        # ── B. Full Viparita Raja Yoga Suite (Harsha, Sarala, Vimala) ────────
        # 1. Harsha: 6th lord in 6th, 8th, or 12th
        h6_lord = chart.houses[5].primary_lord.lower()
        h6_lord_house = chart.planet_bhava_placements.get(h6_lord.capitalize(), 1)
        if h6_lord_house in [6, 8, 12]:
            vry_signed = 0.8
            yoga_block_total += vry_signed
            yogas_list.append(
                TPhalitYoga(
                    YogaID=401,
                    YogaName="ViparitaRajaHarsha",
                    YogaClass=4,
                    IsActive=True,
                    RawStrength=60.0,
                    SignedEffect=vry_signed,
                    CancelsFeatures="D1_H6_Affliction",
                    SuppressesFeatures="",
                    AmplifiesFeatures="D1_H6_FinalScore;D1_H11_FinalScore",
                    FinalContribution=vry_signed,
                )
            )

        # 2. Sarala: 8th lord in 6th, 8th, or 12th
        h8_lord = chart.houses[7].primary_lord.lower()
        h8_lord_house = chart.planet_bhava_placements.get(h8_lord.capitalize(), 1)
        if h8_lord_house in [6, 8, 12]:
            vry_signed = 0.8
            yoga_block_total += vry_signed
            yogas_list.append(
                TPhalitYoga(
                    YogaID=402,
                    YogaName="ViparitaRajaSarala",
                    YogaClass=4,
                    IsActive=True,
                    RawStrength=60.0,
                    SignedEffect=vry_signed,
                    CancelsFeatures="D1_H8_Affliction",
                    SuppressesFeatures="",
                    AmplifiesFeatures="D1_H8_FinalScore;D1_H10_FinalScore",
                    FinalContribution=vry_signed,
                )
            )

        # 3. Vimala: 12th lord in 6th, 8th, or 12th
        h12_lord = chart.houses[11].primary_lord.lower()
        h12_lord_house = chart.planet_bhava_placements.get(h12_lord.capitalize(), 1)
        if h12_lord_house in [6, 8, 12]:
            vry_signed = 0.8
            yoga_block_total += vry_signed
            yogas_list.append(
                TPhalitYoga(
                    YogaID=403,
                    YogaName="ViparitaRajaVimala",
                    YogaClass=4,
                    IsActive=True,
                    RawStrength=60.0,
                    SignedEffect=vry_signed,
                    CancelsFeatures="D1_H12_Affliction",
                    SuppressesFeatures="",
                    AmplifiesFeatures="D1_H12_FinalScore;D1_H9_FinalScore",
                    FinalContribution=vry_signed,
                )
            )

        # ── C. Neechabhanga Raja Yoga ─────────────────────────────────────────
        for p in ephem.planet_positions:
            if p.dignity and p.dignity.value == "debilitated":
                # Find dispositor
                r_idx = int(p.sidereal_longitude / 30.0) % 12
                r_names = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
                r_name = r_names[r_idx]
                disp_name = SIGN_LORDS.get(r_name, "")

                disp_house = chart.planet_bhava_placements.get(disp_name.capitalize(), 1)
                # If dispositor is in Kendra from Lagna (1, 4, 7, 10)
                if disp_house in [1, 4, 7, 10]:
                    nb_signed = 0.9
                    yoga_block_total += nb_signed
                    yogas_list.append(
                        TPhalitYoga(
                            YogaID=501,
                            YogaName=f"Neechabhanga_{p.planet.capitalize()}",
                            YogaClass=5,
                            IsActive=True,
                            RawStrength=50.0,
                            SignedEffect=nb_signed,
                            CancelsFeatures=f"D1_{p.planet.capitalize()}_Debilitation",
                            SuppressesFeatures="",
                            AmplifiesFeatures=f"D1_{p.planet.capitalize()}_FinalSigned;D1_H{disp_house}_FinalScore",
                            FinalContribution=nb_signed,
                        )
                    )


        # 8. Assemble TPhalitFeatureVector (Section 6.6)
        planet_block_total = sum(p.FinalSignedEffect for p in planets_list)
        
        atomic_features: Dict[str, float] = {}
        for p in planets_list:
            atomic_features[f"D1_{p.PlanetName}_FinalSigned"] = p.FinalSignedEffect
            atomic_features[f"D1_{p.PlanetName}_DignityWeight"] = p.DignityWeight
            atomic_features[f"D1_{p.PlanetName}_FuncNature"] = p.FunctionalNature

        for b in bhavas_list:
            atomic_features[f"D1_H{b.BhavaID}_FinalScore"] = b.FinalBhavaScore

        for y in yogas_list:
            atomic_features[f"Yoga_{y.YogaName}_Contribution"] = y.FinalContribution

        block_totals = {
            "PlanetBlock": round(planet_block_total, 4),
            "BhavaBlock": round(bhava_block_total, 4),
            "AspectBlock": round(aspect_block_total, 4),
            "YogaBlock": round(yoga_block_total, 4),
            "VargaBlock": round(planet_block_total * v_weight, 4),
            "TemporalBlock": round(planet_block_total * context.TemporalWeight, 4),
        }

        det_score = round(sum(block_totals.values()), 4)

        return TPhalitFeatureVector(
            AtomicFeatures=atomic_features,
            BlockTotals=block_totals,
            DeterministicScore=det_score,
            TargetValue=target_value,
            Metadata=context,
        )
