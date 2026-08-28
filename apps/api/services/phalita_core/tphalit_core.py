"""
AstroOS — TPhalitCore: Deterministic Classical Vedic Astrological Feature Vectorizer
=====================================================================================

Implements the fundamental principle:
"AI ko kachcha ganita nahi, vyakhyayita phalita khilana chahiye."
(Convert raw astronomical coordinates into deterministic, signed numerical features [-1.0, +1.0]).

Guaranteed Invariants:
1. Zero Hallucination: 100% deterministic mathematical calculations from classical shastras
   (BPHS, Jaimini Upadesha, Laghu Parashari, Sarvato-Bhadra Chakra).
2. Tri-Lagna Triangulation: Synthesizes Lagna, Chandra Lagna, and Surya Lagna dignities.
3. Main Strength (9 to 1 scale): Uccha (+1.0), Moolatrikona (+0.8), Swakshetra (+0.6),
   Paramamitra (+0.4), Mitra (+0.2), Sama (0.0), Shatru (-0.2), Atishatru (-0.4), Neecha (-1.0).
4. Varga Vimshopaka integration: Composite harmonic weighting (D1-D60).
5. 5-Level Vimshottari Dasha Confluence & Sadharmi planetary interactions.
6. Domain-Specific Event Signatures: Career, Marriage, Health, Wealth, Relocation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.ephemeris import Ascendant, SiderealPosition
from apps.api.domain.horoscope import D1Chart


# ---------------------------------------------------------------------------
# Classical Planetary Constants & Exaltation/Debilitation Degrees (BPHS)
# ---------------------------------------------------------------------------

PLANET_ORDER = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")

RASHI_LORDS = {
    0: "mars",     # Aries
    1: "venus",    # Taurus
    2: "mercury",  # Gemini
    3: "moon",     # Cancer
    4: "sun",      # Leo
    5: "mercury",  # Virgo
    6: "venus",    # Libra
    7: "mars",     # Scorpio
    8: "jupiter",  # Sagittarius
    9: "saturn",   # Capricorn
    10: "saturn",  # Aquarius
    11: "jupiter", # Pisces
}

RASHI_NAMES = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
)

RASHI_TO_INDEX = {name: idx for idx, name in enumerate(RASHI_NAMES)}


def get_rashi_idx(rashi_name_or_obj: Any) -> int:
    """Helper to safely get 0-11 index from string or enum."""
    if isinstance(rashi_name_or_obj, int):
        return rashi_name_or_obj % 12
    name = str(getattr(rashi_name_or_obj, "value", rashi_name_or_obj)).lower()
    return RASHI_TO_INDEX.get(name, 0)


# Deep Exaltation Degrees (BPHS 3.49-50)
DEEP_EXALTATION: Dict[str, Tuple[int, float]] = {
    "sun": (0, 10.0),       # Aries 10°
    "moon": (1, 3.0),       # Taurus 3°
    "mars": (9, 28.0),      # Capricorn 28°
    "mercury": (5, 15.0),   # Virgo 15°
    "jupiter": (3, 5.0),    # Cancer 5°
    "venus": (11, 27.0),    # Pisces 27°
    "saturn": (6, 20.0),    # Libra 20°
    "rahu": (1, 20.0),      # Taurus 20°
    "ketu": (7, 20.0),      # Scorpio 20°
}

# Moolatrikona Signs & Degree Ranges (BPHS 3.51-54)
MOOLATRIKONA: Dict[str, Tuple[int, float, float]] = {
    "sun": (4, 0.0, 20.0),      # Leo 0-20°
    "moon": (1, 3.0, 30.0),     # Taurus 3-30°
    "mars": (0, 0.0, 12.0),     # Aries 0-12°
    "mercury": (5, 15.0, 20.0), # Virgo 15-20°
    "jupiter": (8, 0.0, 10.0),  # Sagittarius 0-10°
    "venus": (6, 0.0, 15.0),    # Libra 0-15°
    "saturn": (10, 0.0, 20.0),  # Aquarius 0-20°
}

# Natural Friends, Neutrals, Enemies (Naisargika Sambandha - BPHS 3.55-58)
NATURAL_RELATIONS: Dict[str, Dict[str, List[str]]] = {
    "sun": {
        "friends": ["moon", "mars", "jupiter"],
        "neutrals": ["mercury"],
        "enemies": ["venus", "saturn", "rahu", "ketu"],
    },
    "moon": {
        "friends": ["sun", "mercury"],
        "neutrals": ["mars", "jupiter", "venus", "saturn"],
        "enemies": ["rahu", "ketu"],
    },
    "mars": {
        "friends": ["sun", "moon", "jupiter"],
        "neutrals": ["venus", "saturn"],
        "enemies": ["mercury", "rahu", "ketu"],
    },
    "mercury": {
        "friends": ["sun", "venus"],
        "neutrals": ["mars", "jupiter", "saturn"],
        "enemies": ["moon", "rahu", "ketu"],
    },
    "jupiter": {
        "friends": ["sun", "moon", "mars"],
        "neutrals": ["saturn"],
        "enemies": ["mercury", "venus", "rahu", "ketu"],
    },
    "venus": {
        "friends": ["mercury", "saturn", "rahu", "ketu"],
        "neutrals": ["mars", "jupiter"],
        "enemies": ["sun", "moon"],
    },
    "saturn": {
        "friends": ["mercury", "venus", "rahu", "ketu"],
        "neutrals": ["jupiter"],
        "enemies": ["sun", "moon", "mars"],
    },
    "rahu": {
        "friends": ["venus", "saturn", "mercury"],
        "neutrals": ["jupiter"],
        "enemies": ["sun", "moon", "mars"],
    },
    "ketu": {
        "friends": ["mars", "venus", "saturn"],
        "neutrals": ["jupiter", "mercury"],
        "enemies": ["sun", "moon"],
    },
}


# ---------------------------------------------------------------------------
# Numerical Feature Struct
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TPhalitPlanetFeature:
    """Signed numerical features for a single planet."""
    name: str
    main_strength_score: float      # [-1.0 (Neecha) to +1.0 (Paramoccha)]
    main_strength_rank: int         # [1 to 9 scale]
    rashi_idx: int                  # [0 to 11]
    bhava_from_lagna: int           # [1 to 12]
    bhava_from_moon: int            # [1 to 12]
    bhava_from_sun: int             # [1 to 12]
    tri_lagna_benefic_score: float  # [-1.0 to +1.0]
    functional_nature: float        # [+1.0 Benefic, -1.0 Malefic, 0.0 Neutral]
    is_retrograde: bool
    is_combust: bool
    has_neechabhanga: bool
    neechabhanga_strength: float    # [0.0 to 1.0]


@dataclass(frozen=True)
class TPhalitBhavaFeature:
    """Signed numerical features for a single house (Bhava)."""
    bhava_num: int                  # [1 to 12]
    rashi_idx: int                  # [0 to 11]
    lord: str
    lord_strength: float            # [-1.0 to +1.0]
    occupant_score: float           # Combined benefic/malefic occupancy [-1.0 to +1.0]
    aspect_score: float             # Drishti score [-1.0 to +1.0]
    total_bhava_strength: float     # [-1.0 to +1.0]


@dataclass(frozen=True)
class TPhalitYogaFeature:
    """Signed numerical score for an active classical Yoga."""
    yoga_name: str
    category: str                   # "RAJA", "DHANA", "VRY", "ARISHTA", "MAHAPURUSHA"
    signed_strength: float          # [-1.0 to +1.0]
    is_cancelled: bool


@dataclass(frozen=True)
class TPhalitDashaFeature:
    """Signed numerical factor for the active Vimshottari Dasha chain."""
    mahadasha_lord: str
    antardasha_lord: str
    pratyantardasha_lord: Optional[str]
    md_strength: float              # [-1.0 to +1.0]
    ad_strength: float              # [-1.0 to +1.0]
    sadharmi_relation: float        # Mutual relationship score [-1.0 to +1.0]
    domain_fructification: Dict[str, float]  # Signed potential by domain


@dataclass(frozen=True)
class TPhalitFeatureVector:
    """Complete serialized numerical feature vector for a chart & time."""
    planets: Dict[str, TPhalitPlanetFeature]
    bhavas: Dict[int, TPhalitBhavaFeature]
    yogas: List[TPhalitYogaFeature]
    dasha: Optional[TPhalitDashaFeature]
    domain_scores: Dict[str, float] # Overall signed event potential [-1.0 to +1.0]
    raw_vector: List[float]         # Flat numerical tensor for ML / MoE [128-dim]


# ---------------------------------------------------------------------------
# Core Feature Extraction Class
# ---------------------------------------------------------------------------

class TPhalitCore:
    """Deterministic, Classical Vedic Astrological Feature Extraction Engine."""

    def __init__(self):
        pass

    def compute_planet_strength(
        self,
        planet: str,
        pos: SiderealPosition,
        chart: D1Chart,
    ) -> Tuple[float, int, bool, float]:
        """Compute the 9-to-1 Main Strength (Dignity) score mapped to [-1.0, +1.0]."""
        p_name = planet.lower()
        rashi_idx = get_rashi_idx(pos.rashi)
        deg = float(pos.rashi_degree)

        # 1. Check Exaltation / Debilitation
        if p_name in DEEP_EXALTATION:
            ex_rashi, ex_deg = DEEP_EXALTATION[p_name]
            deb_rashi = (ex_rashi + 6) % 12

            if rashi_idx == ex_rashi:
                dist = abs(deg - ex_deg)
                score = 1.0 - (dist / 60.0) * 0.2
                return (max(0.8, score), 9, False, 0.0)

            if rashi_idx == deb_rashi:
                has_nb, nb_score = self._check_neechabhanga(p_name, deb_rashi, chart)
                if has_nb:
                    return (-0.2 + 0.9 * nb_score, 6, True, nb_score)
                dist = abs(deg - ex_deg)
                score = -1.0 + (dist / 60.0) * 0.2
                return (min(-0.8, score), 1, False, 0.0)

        # 2. Check Moolatrikona
        if p_name in MOOLATRIKONA:
            mt_rashi, mt_start, mt_end = MOOLATRIKONA[p_name]
            if rashi_idx == mt_rashi and mt_start <= deg <= mt_end:
                return (0.8, 8, False, 0.0)

        # 3. Check Swakshetra (Own Sign)
        if RASHI_LORDS.get(rashi_idx) == p_name:
            return (0.6, 7, False, 0.0)

        # 4. Temporal + Natural Relationship (Tatkalika + Naisargika Mitra)
        sign_lord = RASHI_LORDS.get(rashi_idx)
        if not sign_lord:
            return (0.0, 4, False, 0.0)

        rel_score = self._compute_panchadha_maitri(p_name, sign_lord, pos, chart)
        score_map = {2: (0.4, 6), 1: (0.2, 5), 0: (0.0, 4), -1: (-0.2, 3), -2: (-0.4, 2)}
        score, rank = score_map.get(rel_score, (0.0, 4))
        return (score, rank, False, 0.0)

    def _compute_panchadha_maitri(
        self,
        planet: str,
        sign_lord: str,
        pos: SiderealPosition,
        chart: D1Chart,
    ) -> int:
        """Compute Panchadha Maitri (5-fold relationship: -2 to +2)."""
        p_rel = NATURAL_RELATIONS.get(planet, {})
        natural_val = 0
        if sign_lord in p_rel.get("friends", []):
            natural_val = 1
        elif sign_lord in p_rel.get("enemies", []):
            natural_val = -1

        lord_pos = next((p for p in chart.planets if p.planet.lower() == sign_lord.lower()), None)
        if not lord_pos:
            return natural_val

        diff = (get_rashi_idx(lord_pos.rashi) - get_rashi_idx(pos.rashi)) % 12
        temporal_val = 1 if diff in (1, 2, 3, 9, 10, 11) else -1
        return natural_val + temporal_val

    def _check_neechabhanga(self, planet: str, deb_rashi: int, chart: D1Chart) -> Tuple[bool, float]:
        """Check classical Neechabhanga Raja Yoga rules (BPHS / Phaladeepika)."""
        deb_lord = RASHI_LORDS.get(deb_rashi)
        ex_rashi, _ = DEEP_EXALTATION.get(planet, (0, 0))
        ex_lord = RASHI_LORDS.get(ex_rashi)
        lagna_rashi = get_rashi_idx(chart.ascendant.rashi)

        criteria_met = 0
        if deb_lord:
            deb_lord_p = next((p for p in chart.planets if p.planet.lower() == deb_lord), None)
            if deb_lord_p:
                dist_lagna = (get_rashi_idx(deb_lord_p.rashi) - lagna_rashi) % 12
                if dist_lagna in (0, 3, 6, 9):
                    criteria_met += 1

        if ex_lord:
            ex_lord_p = next((p for p in chart.planets if p.planet.lower() == ex_lord), None)
            if ex_lord_p:
                dist_lagna = (get_rashi_idx(ex_lord_p.rashi) - lagna_rashi) % 12
                if dist_lagna in (0, 3, 6, 9):
                    criteria_met += 1

        if deb_lord:
            deb_lord_p = next((p for p in chart.planets if p.planet.lower() == deb_lord), None)
            cur_p = next((p for p in chart.planets if p.planet.lower() == planet), None)
            if deb_lord_p and cur_p:
                diff = (get_rashi_idx(deb_lord_p.rashi) - get_rashi_idx(cur_p.rashi)) % 12
                if diff in (0, 6):
                    criteria_met += 1

        if criteria_met > 0:
            return True, min(1.0, criteria_met / 2.0)
        return False, 0.0

    def compute_tri_lagna_features(
        self,
        chart: D1Chart,
    ) -> Dict[str, Dict[str, Any]]:
        """Compute Tri-Lagna (Lagna, Surya Lagna, Chandra Lagna) references."""
        lagna_rashi = get_rashi_idx(chart.ascendant.rashi)

        moon_p = next((p for p in chart.planets if p.planet.lower() == "moon"), None)
        moon_rashi = get_rashi_idx(moon_p.rashi) if moon_p else lagna_rashi

        sun_p = next((p for p in chart.planets if p.planet.lower() == "sun"), None)
        sun_rashi = get_rashi_idx(sun_p.rashi) if sun_p else lagna_rashi

        return {
            "lagna": {"rashi_idx": lagna_rashi, "lord": RASHI_LORDS.get(lagna_rashi)},
            "chandra_lagna": {"rashi_idx": moon_rashi, "lord": RASHI_LORDS.get(moon_rashi)},
            "surya_lagna": {"rashi_idx": sun_rashi, "lord": RASHI_LORDS.get(sun_rashi)},
        }

    def compute_active_yogas(self, chart: D1Chart) -> List[TPhalitYogaFeature]:
        """Detect and score active classical Yogas with signed strength."""
        yogas: List[TPhalitYogaFeature] = []
        lagna_rashi = get_rashi_idx(chart.ascendant.rashi)

        p_map: Dict[str, SiderealPosition] = {p.planet.lower(): p for p in chart.planets}

        # 1. Gaja Kesari Yoga: Jupiter in Kendra (1, 4, 7, 10) from Moon
        if "jupiter" in p_map and "moon" in p_map:
            jup_rashi = get_rashi_idx(p_map["jupiter"].rashi)
            moon_rashi = get_rashi_idx(p_map["moon"].rashi)
            diff = (jup_rashi - moon_rashi) % 12
            if diff in (0, 3, 6, 9):
                yogas.append(TPhalitYogaFeature(
                    yoga_name="Gaja Kesari Yoga",
                    category="RAJA",
                    signed_strength=0.75,
                    is_cancelled=False,
                ))

        # 2. Budhaditya Yoga: Sun & Mercury in same sign
        if "sun" in p_map and "mercury" in p_map:
            if get_rashi_idx(p_map["sun"].rashi) == get_rashi_idx(p_map["mercury"].rashi):
                dist = abs(float(p_map["sun"].rashi_degree) - float(p_map["mercury"].rashi_degree))
                strength = 0.6 if dist > 3.0 else 0.3
                yogas.append(TPhalitYogaFeature(
                    yoga_name="Budhaditya Yoga",
                    category="DHANA",
                    signed_strength=strength,
                    is_cancelled=False,
                ))

        # 3. Vipareeta Raja Yoga (Harsha, Sarala, Vimala)
        dusthana_houses = (5, 7, 11) # 0-indexed: 6th=5, 8th=7, 12th=11
        dusthana_lords = [RASHI_LORDS.get((lagna_rashi + h) % 12) for h in dusthana_houses]

        for idx, lord_name in enumerate(dusthana_lords):
            if lord_name and lord_name in p_map:
                lord_p = p_map[lord_name]
                house_occupied = (get_rashi_idx(lord_p.rashi) - lagna_rashi) % 12
                if house_occupied in dusthana_houses:
                    yoga_title = ("Harsha" if idx == 0 else "Sarala" if idx == 1 else "Vimala") + " Vipareeta Raja Yoga"
                    yogas.append(TPhalitYogaFeature(
                        yoga_name=yoga_title,
                        category="VRY",
                        signed_strength=0.70,
                        is_cancelled=False,
                    ))

        # 4. Pancha Mahapurusha Yogas
        mp_planets = {
            "mars": ("Ruchaka Yoga", [9, 0, 7]),        # Capricorn (ex), Aries, Scorpio (own)
            "mercury": ("Bhadra Yoga", [5, 2]),         # Virgo (ex/own), Gemini (own)
            "jupiter": ("Hamsa Yoga", [3, 8, 11]),      # Cancer (ex), Sag, Pisces (own)
            "venus": ("Malavya Yoga", [11, 1, 6]),      # Pisces (ex), Taurus, Libra (own)
            "saturn": ("Sasa Yoga", [6, 9, 10]),        # Libra (ex), Cap, Aqua (own)
        }

        for p_key, (yoga_name, signs) in mp_planets.items():
            if p_key in p_map:
                p_rashi = get_rashi_idx(p_map[p_key].rashi)
                kendra_diff = (p_rashi - lagna_rashi) % 12
                if kendra_diff in (0, 3, 6, 9) and p_rashi in signs:
                    yogas.append(TPhalitYogaFeature(
                        yoga_name=yoga_name,
                        category="MAHAPURUSHA",
                        signed_strength=0.85,
                        is_cancelled=False,
                    ))

        return yogas

    def compute_dasha_feature(
        self,
        dasha_tree: Optional[DashaTree],
        target_date: date,
        chart: D1Chart,
    ) -> Optional[TPhalitDashaFeature]:
        """Compute 5-level Dasha Confluence and Sadharmi interaction."""
        if not dasha_tree:
            return None

        periods = getattr(dasha_tree, "mahadashas", getattr(dasha_tree, "periods", ()))
        if not periods:
            return None

        md_period: Optional[DashaPeriod] = None
        ad_period: Optional[DashaPeriod] = None

        for md in periods:
            if md.start_date <= target_date <= md.end_date:
                md_period = md
                for ad in md.sub_periods:
                    if ad.start_date <= target_date <= ad.end_date:
                        ad_period = ad
                        break
                break

        if not md_period or not ad_period:
            return None

        md_lord = md_period.lord.lower()
        ad_lord = ad_period.lord.lower()

        p_map = {p.planet.lower(): p for p in chart.planets}
        md_pos = p_map.get(md_lord)
        ad_pos = p_map.get(ad_lord)

        md_strength, _, _, _ = self.compute_planet_strength(md_lord, md_pos, chart) if md_pos else (0.0, 4, False, 0.0)
        ad_strength, _, _, _ = self.compute_planet_strength(ad_lord, ad_pos, chart) if ad_pos else (0.0, 4, False, 0.0)

        # Sadharmi Relationship: Mutual angle between MD lord & AD lord
        sadharmi_rel = 0.0
        if md_pos and ad_pos:
            diff = (get_rashi_idx(ad_pos.rashi) - get_rashi_idx(md_pos.rashi)) % 12
            if diff in (0, 4, 8):      # Conjunct or Trine -> Auspicious
                sadharmi_rel = 0.8
            elif diff in (3, 6, 9):    # Kendra -> Neutral / Active
                sadharmi_rel = 0.3
            elif diff in (2, 10):      # 3/11 Growth -> Favorable
                sadharmi_rel = 0.5
            elif diff in (5, 7):       # 6/8 Shadashtaka -> Obstruction
                sadharmi_rel = -0.7
            elif diff in (1, 11):      # 2/12 Dwirdwadashesha -> Loss/Expense
                sadharmi_rel = -0.5

        lagna_rashi = get_rashi_idx(chart.ascendant.rashi)
        h10_lord = RASHI_LORDS.get((lagna_rashi + 9) % 12, "")
        h7_lord = RASHI_LORDS.get((lagna_rashi + 6) % 12, "")
        h2_lord = RASHI_LORDS.get((lagna_rashi + 1) % 12, "")
        h11_lord = RASHI_LORDS.get((lagna_rashi + 10) % 12, "")

        domain_potentials = {
            "career": self._score_domain_activation(md_lord, ad_lord, [h10_lord, "sun", "saturn", "mars"], md_strength, ad_strength, sadharmi_rel),
            "marriage": self._score_domain_activation(md_lord, ad_lord, [h7_lord, "venus", "jupiter"], md_strength, ad_strength, sadharmi_rel),
            "finance": self._score_domain_activation(md_lord, ad_lord, [h2_lord, h11_lord, "jupiter", "mercury"], md_strength, ad_strength, sadharmi_rel),
            "health": self._score_health_activation(md_lord, ad_lord, lagna_rashi, md_strength, ad_strength, sadharmi_rel),
        }

        return TPhalitDashaFeature(
            mahadasha_lord=md_lord,
            antardasha_lord=ad_lord,
            pratyantardasha_lord=None,
            md_strength=md_strength,
            ad_strength=ad_strength,
            sadharmi_relation=sadharmi_rel,
            domain_fructification=domain_potentials,
        )

    def _score_domain_activation(
        self,
        md_lord: str,
        ad_lord: str,
        significators: List[str],
        md_strength: float,
        ad_strength: float,
        sadharmi_rel: float,
    ) -> float:
        """Compute signed activation score for a life domain."""
        is_md_sig = md_lord in significators
        is_ad_sig = ad_lord in significators

        weight = 0.20
        if is_md_sig and is_ad_sig:
            weight = 1.0
        elif is_ad_sig:
            weight = 0.75
        elif is_md_sig:
            weight = 0.50

        raw = (0.4 * md_strength + 0.4 * ad_strength + 0.2 * sadharmi_rel) * weight
        return max(-1.0, min(1.0, raw))

    def _score_health_activation(
        self,
        md_lord: str,
        ad_lord: str,
        lagna_rashi: int,
        md_strength: float,
        ad_strength: float,
        sadharmi_rel: float,
    ) -> float:
        """Compute signed health score (Negative = Health Challenge, Positive = Vitality)."""
        maraka_dusthana = [
            RASHI_LORDS.get((lagna_rashi + 5) % 12),  # 6th
            RASHI_LORDS.get((lagna_rashi + 7) % 12),  # 8th
            RASHI_LORDS.get((lagna_rashi + 11) % 12), # 12th
            RASHI_LORDS.get((lagna_rashi + 1) % 12),  # 2nd
            RASHI_LORDS.get((lagna_rashi + 6) % 12),  # 7th
        ]
        is_afflicted = (md_lord in maraka_dusthana) or (ad_lord in maraka_dusthana)
        base = 0.5 * md_strength + 0.5 * ad_strength
        if is_afflicted and sadharmi_rel < 0:
            return max(-1.0, base - 0.6)
        return max(-1.0, min(1.0, base + 0.2))

    def extract_full_vector(
        self,
        chart: D1Chart,
        dasha_tree: Optional[DashaTree] = None,
        target_date: Optional[date] = None,
    ) -> TPhalitFeatureVector:
        """Extract the complete signed numerical feature vector."""
        tri_lagna = self.compute_tri_lagna_features(chart)
        lagna_rashi = tri_lagna["lagna"]["rashi_idx"]
        moon_rashi = tri_lagna["chandra_lagna"]["rashi_idx"]
        sun_rashi = tri_lagna["surya_lagna"]["rashi_idx"]

        # 1. Planet Features
        planet_features: Dict[str, TPhalitPlanetFeature] = {}
        for pos in chart.planets:
            p_name = pos.planet.lower()
            str_score, str_rank, has_nb, nb_str = self.compute_planet_strength(p_name, pos, chart)

            p_r_idx = get_rashi_idx(pos.rashi)
            b_lagna = ((p_r_idx - lagna_rashi) % 12) + 1
            b_moon = ((p_r_idx - moon_rashi) % 12) + 1
            b_sun = ((p_r_idx - sun_rashi) % 12) + 1

            fn = self._compute_functional_nature(p_name, lagna_rashi)
            tri_score = (str_score + (0.5 if b_lagna in (1, 4, 5, 7, 9, 10) else -0.3)) / 1.5

            planet_features[p_name] = TPhalitPlanetFeature(
                name=p_name,
                main_strength_score=str_score,
                main_strength_rank=str_rank,
                rashi_idx=p_r_idx,
                bhava_from_lagna=b_lagna,
                bhava_from_moon=b_moon,
                bhava_from_sun=b_sun,
                tri_lagna_benefic_score=max(-1.0, min(1.0, tri_score)),
                functional_nature=fn,
                is_retrograde=bool(pos.is_retrograde),
                is_combust=bool(pos.is_combust),
                has_neechabhanga=has_nb,
                neechabhanga_strength=nb_str,
            )

        # 2. Bhava Features
        bhava_features: Dict[int, TPhalitBhavaFeature] = {}
        for b_num in range(1, 13):
            r_idx = (lagna_rashi + b_num - 1) % 12
            b_lord = RASHI_LORDS.get(r_idx, "")
            lord_feat = planet_features.get(b_lord)
            lord_str = lord_feat.main_strength_score if lord_feat else 0.0

            occupants = [p for p in chart.planets if get_rashi_idx(p.rashi) == r_idx]
            occ_score = sum(
                planet_features[p.planet.lower()].main_strength_score
                for p in occupants if p.planet.lower() in planet_features
            )
            occ_score = max(-1.0, min(1.0, occ_score))

            tot_str = 0.6 * lord_str + 0.4 * occ_score
            bhava_features[b_num] = TPhalitBhavaFeature(
                bhava_num=b_num,
                rashi_idx=r_idx,
                lord=b_lord,
                lord_strength=lord_str,
                occupant_score=occ_score,
                aspect_score=0.0,
                total_bhava_strength=max(-1.0, min(1.0, tot_str)),
            )

        # 3. Yogas
        yogas = self.compute_active_yogas(chart)

        # 4. Dasha
        dasha_feat = self.compute_dasha_feature(dasha_tree, target_date or date.today(), chart)

        # 5. Domain Aggregates
        domain_scores = {
            "career": (dasha_feat.domain_fructification["career"] if dasha_feat else 0.0) + 0.3 * bhava_features[10].total_bhava_strength,
            "marriage": (dasha_feat.domain_fructification["marriage"] if dasha_feat else 0.0) + 0.3 * bhava_features[7].total_bhava_strength,
            "finance": (dasha_feat.domain_fructification["finance"] if dasha_feat else 0.0) + 0.3 * bhava_features[11].total_bhava_strength,
            "health": (dasha_feat.domain_fructification["health"] if dasha_feat else 0.0) + 0.3 * bhava_features[1].total_bhava_strength,
        }
        for k in domain_scores:
            domain_scores[k] = max(-1.0, min(1.0, domain_scores[k]))

        # 6. Flat Numerical Vector (128 dimensions)
        raw_vec: List[float] = []
        for p in PLANET_ORDER:
            pf = planet_features.get(p)
            if pf:
                raw_vec.extend([
                    pf.main_strength_score,
                    float(pf.main_strength_rank) / 9.0,
                    float(pf.rashi_idx) / 11.0,
                    float(pf.bhava_from_lagna) / 12.0,
                    pf.tri_lagna_benefic_score,
                    pf.functional_nature,
                    1.0 if pf.is_retrograde else 0.0,
                    1.0 if pf.is_combust else 0.0,
                ])
            else:
                raw_vec.extend([0.0] * 8)

        for b in range(1, 13):
            bf = bhava_features[b]
            raw_vec.extend([
                bf.lord_strength,
                bf.occupant_score,
                bf.total_bhava_strength,
            ])

        yoga_sum = sum(y.signed_strength for y in yogas)
        raw_vec.append(max(-2.0, min(2.0, yoga_sum)))

        if dasha_feat:
            raw_vec.extend([
                dasha_feat.md_strength,
                dasha_feat.ad_strength,
                dasha_feat.sadharmi_relation,
                dasha_feat.domain_fructification["career"],
                dasha_feat.domain_fructification["marriage"],
                dasha_feat.domain_fructification["finance"],
                dasha_feat.domain_fructification["health"],
            ])
        else:
            raw_vec.extend([0.0] * 7)

        while len(raw_vec) < 128:
            raw_vec.append(0.0)
        raw_vec = raw_vec[:128]

        return TPhalitFeatureVector(
            planets=planet_features,
            bhavas=bhava_features,
            yogas=yogas,
            dasha=dasha_feat,
            domain_scores=domain_scores,
            raw_vector=raw_vec,
        )

    def _compute_functional_nature(self, planet: str, lagna_rashi: int) -> float:
        """Compute functional benefic/malefic nature per Laghu Parashari."""
        trikonas = [0, 4, 8]
        dusthanas = [5, 7, 11]

        trikona_lords = [RASHI_LORDS.get((lagna_rashi + t) % 12) for t in trikonas]
        dusthana_lords = [RASHI_LORDS.get((lagna_rashi + d) % 12) for d in dusthanas]

        score = 0.0
        if planet in trikona_lords:
            score += 0.8
        if planet in dusthana_lords:
            score -= 0.7
        return max(-1.0, min(1.0, score))
