"""
AstroOS — Vinay Jha Canonical Dignity & Main Strength Engine (Step 3 & 4)
========================================================================
Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Step 3 & Step 4)
Source: BPHS Ishta-Kashta-Vivechana Chapter & Jha's "How To Make Correct Predictions"

Enforces Jha's Strict Mathematical Strength Principles:
  1. Panchadha Maitri: Synthesis of Naisargika (Natural) + Tatkalika (Temporal) friendships.
  2. 9-Tier Dignity Hierarchy:
       Tier 9: Exalted (Uchcha)
       Tier 8: Moolatrikona
       Tier 7: Own Sign (Svakshetra)
       Tier 6: Fast Friend's Sign (Atimitra)
       Tier 5: Friend's Sign (Mitra)
       Tier 4: Neutral Sign (Sama)
       Tier 3: Enemy's Sign (Shatru)
       Tier 2: Bitter Enemy's Sign (Atishatru)
       Tier 1: Debilitated (Neecha)
  3. Log-Base-2 Main Strength Scale:
       Main Strength = 2^(Dignity - 1)  (Range: 1.0 to 256.0)
       - Exalted (9) is 256x stronger than Debilitated (1), 128x Bitter Enemy (2).
  4. Shadbala as Tiebreaker ONLY:
       Shadbala is linear; Main Strength is exponential. Shadbala is consulted
       only when two planets hold identical Main Strength scores.
  5. Final Varga Strength:
       Final Strength = Main Strength x (Vimshopaka Weight / 20.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

RASHI_LIST: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
)

RASHI_LORDS: dict[str, str] = {
    "aries": "mars", "scorpio": "mars",
    "taurus": "venus", "libra": "venus",
    "gemini": "mercury", "virgo": "mercury",
    "cancer": "moon", "leo": "sun",
    "sagittarius": "jupiter", "pisces": "jupiter",
    "capricorn": "saturn", "aquarius": "saturn"
}

HINDI_PLANET_MAP: dict[str, str] = {
    "सूर्य": "sun", "रवि": "sun",
    "चंद्र": "moon", "चन्द्र": "moon",
    "मंगल": "mars", "भौम": "mars",
    "बुध": "mercury",
    "गुरु": "jupiter", "बृहस्पति": "jupiter",
    "शुक्र": "venus",
    "शनि": "saturn",
    "राहु": "rahu",
    "केतु": "ketu",
}

# Classical Exaltation & Debilitation Ranges: (Sign Index [0-11], Start Deg, End Deg)
# Data-driven declarative tables eliminating procedural hardcoding.
EXALTATION_RANGES: dict[str, tuple[int, float, float]] = {
    "sun":     (0, 0.0, 30.0),      # Aries 0-30° (Peak 10°)
    "moon":    (1, 0.0, 3.0),       # Taurus 0-3° (Peak 3°, remaining 3-30° is Moolatrikona)
    "mars":    (9, 0.0, 30.0),      # Capricorn 0-30° (Peak 28°)
    "mercury": (5, 0.0, 15.0),      # Virgo 0-15° (Peak 15°, 15-20° Moolatrikona, 20-30° Own)
    "jupiter": (3, 0.0, 30.0),      # Cancer 0-30° (Peak 5°)
    "venus":   (11, 0.0, 30.0),     # Pisces 0-30° (Peak 27°)
    "saturn":  (6, 0.0, 30.0),      # Libra 0-30° (Peak 20°)
    "rahu":    (1, 0.0, 30.0),      # Taurus 0-30° (canonical Jha SSS)
    "ketu":    (7, 0.0, 30.0),      # Scorpio 0-30° (canonical Jha SSS)
}

DEBILITATION_RANGES: dict[str, tuple[int, float, float]] = {
    "sun":     (6, 0.0, 30.0),      # Libra 0-30°
    "moon":    (7, 0.0, 30.0),      # Scorpio 0-30°
    "mars":    (3, 0.0, 30.0),      # Cancer 0-30°
    "mercury": (11, 0.0, 30.0),     # Pisces 0-30°
    "jupiter": (9, 0.0, 30.0),      # Capricorn 0-30°
    "venus":   (5, 0.0, 30.0),      # Virgo 0-30°
    "saturn":  (0, 0.0, 30.0),      # Aries 0-30°
    "rahu":    (7, 0.0, 30.0),      # Scorpio 0-30°
    "ketu":    (1, 0.0, 30.0),      # Taurus 0-30°
}

# Derived sign-only mappings for backward compatibility
EXALTATION_SIGNS: dict[str, int] = {k: v[0] for k, v in EXALTATION_RANGES.items()}
DEBILITATION_SIGNS: dict[str, int] = {k: v[0] for k, v in DEBILITATION_RANGES.items()}

# Own Signs
OWN_SIGNS: dict[str, tuple[int, ...]] = {
    "sun": (4,), "moon": (3,), "mars": (0, 7), "mercury": (2, 5),
    "jupiter": (8, 11), "venus": (1, 6), "saturn": (9, 10)
}

# Moolatrikona Signs and Degree Boundaries (BPHS / Jha)
MOOLATRIKONA_RANGES: dict[str, tuple[int, float, float]] = {
    "sun": (4, 0.0, 20.0),       # Leo 0-20°
    "moon": (1, 3.0, 30.0),      # Taurus 3-30°
    "mars": (0, 0.0, 12.0),      # Aries 0-12°
    "mercury": (5, 15.0, 20.0),  # Virgo 15-20°
    "jupiter": (8, 0.0, 10.0),   # Sagittarius 0-10°
    "venus": (6, 0.0, 15.0),     # Libra 0-15°
    "saturn": (10, 0.0, 20.0),   # Aquarius 0-20°
}

# Classical Naisargika (Natural) Relationships (BPHS Ch. 15)
# Values: +1 (Friend), 0 (Neutral), -1 (Enemy)
NAISARGIKA_RELATIONSHIPS: dict[str, dict[str, int]] = {
    "sun": {
        "moon": 1, "mars": 1, "jupiter": 1,
        "mercury": 0,
        "venus": -1, "saturn": -1
    },
    "moon": {
        "sun": 1, "mercury": 1,
        "mars": 0, "jupiter": 0, "venus": 0, "saturn": 0,
    },
    "mars": {
        "sun": 1, "moon": 1, "jupiter": 1,
        "venus": 0, "saturn": 0,
        "mercury": -1
    },
    "mercury": {
        "sun": 1, "venus": 1,
        "mars": 0, "jupiter": 0, "saturn": 0,
        "moon": -1
    },
    "jupiter": {
        "sun": 1, "moon": 1, "mars": 1,
        "saturn": 0,
        "mercury": -1, "venus": -1
    },
    "venus": {
        "mercury": 1, "saturn": 1,
        "mars": 0, "jupiter": 0,
        "sun": -1, "moon": -1
    },
    "saturn": {
        "mercury": 1, "venus": 1,
        "jupiter": 0,
        "sun": -1, "moon": -1, "mars": -1
    }
}

DIGNITY_LABELS: dict[int, str] = {
    9: "Exalted (Uchcha)",
    8: "Moolatrikona",
    7: "Own Sign (Svakshetra)",
    6: "Fast Friend (Atimitra)",
    5: "Friend (Mitra)",
    4: "Neutral (Sama)",
    3: "Enemy (Shatru)",
    2: "Bitter Enemy (Atishatru)",
    1: "Debilitated (Neecha)",
}


@dataclass(frozen=True)
class JhaDignityResult:
    planet: str
    rashi_index: int
    rashi_name: str
    degree_in_rashi: float
    sign_lord: str
    naisargika_relation: str      # Friend, Neutral, Enemy
    tatkalika_relation: str       # Friend, Enemy
    panchadha_relation: str       # Atimitra, Mitra, Sama, Shatru, Atishatru
    dignity_tier: int             # 1 to 9
    dignity_label: str
    main_strength: float          # 2^(dignity_tier - 1), 1.0 to 256.0
    vimshopaka_weight: float      # out of 20
    final_varga_strength: float   # main_strength * (vimshopaka / 20.0)
    shadbala_score: Optional[float] = None
    shastric_notes: str = ""


class JhaDignityEngine:
    """
    Computes Panchadha Maitri and Jha Log-Base-2 Main Strength for all Grahas.
    """

    @classmethod
    def evaluate_planet_dignity(
        cls,
        planet: str,
        sidereal_lon: float,
        chart_planet_positions: Dict[str, float],
        varga_code: str = "D1",
        vimshopaka_weight: float = 6.0,
        shadbala_score: Optional[float] = None,
    ) -> JhaDignityResult:
        p = planet.lower()
        rashi_idx = int(sidereal_lon // 30.0) % 12
        deg_in_sign = sidereal_lon % 30.0
        rashi_name = RASHI_LIST[rashi_idx]
        sign_lord = RASHI_LORDS.get(rashi_name, "mars")

        # 1. Check Exaltation (Uchcha) -> Tier 9
        if p in EXALTATION_RANGES:
            ex_rashi, ex_start, ex_end = EXALTATION_RANGES[p]
            if rashi_idx == ex_rashi and ex_start <= deg_in_sign <= ex_end:
                tier = 9
                main_str = 2.0 ** (tier - 1.0)
                return JhaDignityResult(
                    planet=p, rashi_index=rashi_idx, rashi_name=rashi_name,
                    degree_in_rashi=round(deg_in_sign, 2), sign_lord=sign_lord,
                    naisargika_relation="Exalted", tatkalika_relation="Exalted",
                    panchadha_relation="Exalted", dignity_tier=tier,
                    dignity_label=DIGNITY_LABELS[tier], main_strength=main_str,
                    vimshopaka_weight=vimshopaka_weight,
                    final_varga_strength=round(main_str * (vimshopaka_weight / 20.0), 2),
                    shadbala_score=shadbala_score,
                    shastric_notes="Exalted at peak dignity (256x base strength)."
                )

        # 2. Check Debilitation (Neecha) -> Tier 1
        if p in DEBILITATION_RANGES:
            deb_rashi, deb_start, deb_end = DEBILITATION_RANGES[p]
            if rashi_idx == deb_rashi and deb_start <= deg_in_sign <= deb_end:
                tier = 1
                main_str = 2.0 ** (tier - 1.0)
                return JhaDignityResult(
                    planet=p, rashi_index=rashi_idx, rashi_name=rashi_name,
                    degree_in_rashi=round(deg_in_sign, 2), sign_lord=sign_lord,
                    naisargika_relation="Debilitated", tatkalika_relation="Debilitated",
                    panchadha_relation="Debilitated", dignity_tier=tier,
                    dignity_label=DIGNITY_LABELS[tier], main_strength=main_str,
                    vimshopaka_weight=vimshopaka_weight,
                    final_varga_strength=round(main_str * (vimshopaka_weight / 20.0), 2),
                    shadbala_score=shadbala_score,
                    shastric_notes="Debilitated at minimum dignity (1.0x base strength)."
            )

        # 3. Check Moolatrikona -> Tier 8
        if p in MOOLATRIKONA_RANGES:
            mt_rashi, mt_start, mt_end = MOOLATRIKONA_RANGES[p]
            if rashi_idx == mt_rashi and mt_start <= deg_in_sign <= mt_end:
                tier = 8
                main_str = 2.0 ** (tier - 1.0)
                return JhaDignityResult(
                    planet=p, rashi_index=rashi_idx, rashi_name=rashi_name,
                    degree_in_rashi=round(deg_in_sign, 2), sign_lord=sign_lord,
                    naisargika_relation="Moolatrikona", tatkalika_relation="Moolatrikona",
                    panchadha_relation="Moolatrikona", dignity_tier=tier,
                    dignity_label=DIGNITY_LABELS[tier], main_strength=main_str,
                    vimshopaka_weight=vimshopaka_weight,
                    final_varga_strength=round(main_str * (vimshopaka_weight / 20.0), 2),
                    shadbala_score=shadbala_score,
                    shastric_notes=f"Moolatrikona placement in {rashi_name.capitalize()} (128x base strength)."
                )

        # 4. Check Own Sign (Svakshetra) -> Tier 7
        if p in OWN_SIGNS and rashi_idx in OWN_SIGNS[p]:
            tier = 7
            main_str = 2.0 ** (tier - 1.0)
            return JhaDignityResult(
                planet=p, rashi_index=rashi_idx, rashi_name=rashi_name,
                degree_in_rashi=round(deg_in_sign, 2), sign_lord=sign_lord,
                naisargika_relation="Own Sign", tatkalika_relation="Own Sign",
                panchadha_relation="Own Sign", dignity_tier=tier,
                dignity_label=DIGNITY_LABELS[tier], main_strength=main_str,
                vimshopaka_weight=vimshopaka_weight,
                final_varga_strength=round(main_str * (vimshopaka_weight / 20.0), 2),
                shadbala_score=shadbala_score,
                shastric_notes=f"Svakshetra ownership in {rashi_name.capitalize()} (64x base strength)."
            )

        # 5. Compute Panchadha Maitri (Tiers 2 to 6)
        # Naisargika Relation
        n_rel_val = NAISARGIKA_RELATIONSHIPS.get(p, {}).get(sign_lord, 0)
        n_label = "Friend" if n_rel_val == 1 else ("Enemy" if n_rel_val == -1 else "Neutral")

        # Tatkalika Relation (Based on house difference in the birth chart)
        lord_pos = chart_planet_positions.get(sign_lord, None)
        if lord_pos is not None:
            lord_rashi = int(lord_pos // 30.0) % 12
            # Houses from planet to sign lord (1 to 12)
            house_diff = ((lord_rashi - rashi_idx) % 12) + 1
            # BPHS Rule: 2, 3, 4, 10, 11, 12 are Temporal Friends (+1); 1, 5, 6, 7, 8, 9 are Temporal Enemies (-1)
            t_rel_val = 1 if house_diff in (2, 3, 4, 10, 11, 12) else -1
        else:
            t_rel_val = 0
        t_label = "Friend" if t_rel_val == 1 else ("Enemy" if t_rel_val == -1 else "Neutral")

        # Compound Panchadha Maitri Sum
        p_val = n_rel_val + t_rel_val # Range: -2 to +2
        if p_val == 2:
            tier = 6
            p_label = "Atimitra (Fast Friend)"
        elif p_val == 1:
            tier = 5
            p_label = "Mitra (Friend)"
        elif p_val == 0:
            tier = 4
            p_label = "Sama (Neutral)"
        elif p_val == -1:
            tier = 3
            p_label = "Shatru (Enemy)"
        else:
            tier = 2
            p_label = "Atishatru (Bitter Enemy)"

        main_str = 2.0 ** (tier - 1.0) # 2.0 to 32.0
        final_str = main_str * (vimshopaka_weight / 20.0)

        notes = f"Panchadha Maitri: Natural {n_label} + Temporal {t_label} -> {p_label}."
        return JhaDignityResult(
            planet=p, rashi_index=rashi_idx, rashi_name=rashi_name,
            degree_in_rashi=round(deg_in_sign, 2), sign_lord=sign_lord,
            naisargika_relation=n_label, tatkalika_relation=t_label,
            panchadha_relation=p_label, dignity_tier=tier,
            dignity_label=DIGNITY_LABELS[tier], main_strength=main_str,
            vimshopaka_weight=vimshopaka_weight,
            final_varga_strength=round(final_str, 2),
            shadbala_score=shadbala_score,
            shastric_notes=notes,
        )

    @classmethod
    def resolve_strength_tiebreaker(
        cls,
        planet_a: JhaDignityResult,
        planet_b: JhaDignityResult,
    ) -> Tuple[JhaDignityResult, str]:
        """
        Shadbala is used strictly as a tiebreaker when two planets hold identical Main Strength.
        """
        if planet_a.main_strength > planet_b.main_strength:
            return planet_a, f"{planet_a.planet.capitalize()} wins by higher Main Strength ({planet_a.main_strength} vs {planet_b.main_strength})."
        elif planet_b.main_strength > planet_a.main_strength:
            return planet_b, f"{planet_b.planet.capitalize()} wins by higher Main Strength ({planet_b.main_strength} vs {planet_a.main_strength})."

        # Identical Main Strength -> Consult Shadbala
        s_a = planet_a.shadbala_score or 1.0
        s_b = planet_b.shadbala_score or 1.0
        if s_a >= s_b:
            return planet_a, f"{planet_a.planet.capitalize()} wins tiebreaker by Shadbala ({s_a:.2f} vs {s_b:.2f})."
        else:
            return planet_b, f"{planet_b.planet.capitalize()} wins tiebreaker by Shadbala ({s_b:.2f} vs {s_a:.2f})."


def compute_dignity(
    planet: str,
    sign: int,
    degree: float = 15.0,
    chart_planet_positions: Optional[Dict[str, float]] = None,
) -> int:
    """
    Convenience function returning the integer dignity tier (1 to 9).
    Supports English ("venus", "moon") and Hindi ("शुक्र", "चंद्र") names.
    """
    p_clean = HINDI_PLANET_MAP.get(planet.strip(), planet.lower().strip())
    sidereal_lon = (sign % 12) * 30.0 + (degree % 30.0)
    positions = chart_planet_positions or {p_clean: sidereal_lon}
    res = JhaDignityEngine.evaluate_planet_dignity(
        planet=p_clean,
        sidereal_lon=sidereal_lon,
        chart_planet_positions=positions,
    )
    return res.dignity_tier


def compute_strength(rank: int) -> float:
    """Returns Jha exponential main strength: 2^(rank - 1)."""
    return 2.0 ** (rank - 1.0)
