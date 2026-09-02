"""
AstroOS — Karakamsha & 7-Chara Karaka Synthesis Engine
======================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 5)
Sources: BPHS (Chara Karaka Adhyaya), Jaimini Sutras & Jha's "How To Make Correct Predictions"

Key Siddhantic Rules Enforced:
1. 7 Chara Karakas ALWAYS (never 8).
   - Only classical 7 planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn.
   - Rahu/Ketu are NOT Chara Karakas.
   - Ranked by descending order of degree within sign (0° to 30°):
     AK (Atma), AmK (Amatya), BK (Bhratri), MK (Matri), PK (Putra), GK (Gnati), DK (Dara).
2. Karakamsha Lagna (KL):
   - The sign occupied by Atmakaraka (AK) in D9 Navamsha.
   - Houses from Karakamsha Lagna indicate soul purpose, spiritual strength, and karmic capacity.
3. Karaka Yogas & Arudha Alignments:
   - Raja Yogas: AK conjoined or aspecting PK / AmK / DK.
   - AK in 1st, 5th, 9th, 10th from Karakamsha = High life elevation.
   - Benefics in 2nd/12th from Karakamsha = Moksha / higher consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.divisional_engine import compute_varga_sign
from packages.shared.constants import KALACHAKRA_SAVYA_SIGNS, SIGN_LORDS


@dataclass(frozen=True)
class CharaKarakaAssignment:
    karaka_role: str           # "AK", "AmK", "BK", "MK", "PK", "GK", "DK"
    full_name: str             # "Atmakaraka", "Amatyakaraka", etc.
    planet: str                # e.g., "Sun", "Jupiter"
    d1_rashi: str
    d1_rashi_idx: int
    degree_in_sign: float
    d9_rashi: str
    d9_rashi_idx: int
    house_from_lagna: int
    house_from_karakamsha: int
    signification: str


@dataclass(frozen=True)
class KarakamshaSynthesisResult:
    atmakaraka_planet: str
    karakamsha_rashi: str
    karakamsha_rashi_idx: int
    chara_karakas: Tuple[CharaKarakaAssignment, ...]
    jaimini_raja_yogas: Tuple[str, ...]
    is_moksha_oriented: bool
    karakamsha_karmic_theme: str
    shastric_synthesis_summary: str


class KarakamshaSynthesisEngine:
    """
    Computes 7 Chara Karakas, Karakamsha Lagna, and Jaimini Raja Yogas.
    """

    KARAKA_RANKS = [
        ("AK", "Atmakaraka", "Soul purpose, ultimate ambition, self-realization, principal karmic director"),
        ("AmK", "Amatyakaraka", "Career, profession, mind, minister, secondary advisor and status"),
        ("BK", "Bhratrikaraka", "Siblings, courage, mentors, gurus, and enterprising spirit"),
        ("MK", "Matrikaraka", "Mother, emotional foundations, properties, conveyances, inner peace"),
        ("PK", "Putrakaraka", "Progeny, intellect, creative intelligence, authorship, Purvapunya"),
        ("GK", "Gnatikaraka", "Kith/kin rivalry, obstacles, debts, litigation, competitors"),
        ("DK", "Darakaraka", "Spouse, partnership, marital union, worldly trade and counterpart"),
    ]

    @classmethod
    def compute_synthesis(
        cls,
        d1_planet_longitudes: Dict[str, float], # planet -> 0..360 longitude
        d1_lagna_lon: float,
    ) -> KarakamshaSynthesisResult:
        """
        Computes 7 Chara Karakas, Karakamsha Lagna (D9 of AK), and Jaimini Yogas.
        """
        d1_lagna_idx = int(d1_lagna_lon / 30.0) % 12

        # 1. Filter strictly to the 7 classical planets
        eligible_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        planet_degrees: List[Tuple[str, float, int, float]] = []

        for p in eligible_planets:
            lon = d1_planet_longitudes.get(p, 0.0)
            deg_in_sign = lon % 30.0
            r_idx = int(lon / 30.0) % 12
            planet_degrees.append((p.capitalize(), deg_in_sign, r_idx, lon))

        # 2. Sort descending by degree within sign (Highest deg = AK)
        planet_degrees.sort(key=lambda x: x[1], reverse=True)

        # 3. Assign 7 Chara Karakas
        ak_tuple = planet_degrees[0]
        ak_planet = ak_tuple[0]
        ak_lon = ak_tuple[3]

        # Karakamsha Lagna = Navamsha (D9) sign of Atmakaraka
        ak_d9_rashi_name, _ = compute_varga_sign("D9", ak_lon)
        ak_d9_rashi_clean = ak_d9_rashi_name.lower()
        kl_rashi_idx = KALACHAKRA_SAVYA_SIGNS.index(ak_d9_rashi_clean) if ak_d9_rashi_clean in KALACHAKRA_SAVYA_SIGNS else 0

        karaka_assignments: List[CharaKarakaAssignment] = []
        karaka_map: Dict[str, str] = {} # role -> planet

        for i, (p_name, deg_in_sign, r_idx, lon) in enumerate(planet_degrees[:7]):
            role, full_name, sig_desc = cls.KARAKA_RANKS[i]
            karaka_map[role] = p_name

            # Compute D9 sign for this planet
            d9_rashi_name, _ = compute_varga_sign("D9", lon)
            d9_rashi_clean = d9_rashi_name.lower()
            d9_r_idx = KALACHAKRA_SAVYA_SIGNS.index(d9_rashi_clean) if d9_rashi_clean in KALACHAKRA_SAVYA_SIGNS else 0

            house_lagna = ((r_idx - d1_lagna_idx) % 12) + 1
            house_kl = ((d9_r_idx - kl_rashi_idx) % 12) + 1

            karaka_assignments.append(
                CharaKarakaAssignment(
                    karaka_role=role,
                    full_name=full_name,
                    planet=p_name,
                    d1_rashi=KALACHAKRA_SAVYA_SIGNS[r_idx].capitalize(),
                    d1_rashi_idx=r_idx,
                    degree_in_sign=round(deg_in_sign, 2),
                    d9_rashi=d9_rashi_name.capitalize(),
                    d9_rashi_idx=d9_r_idx,
                    house_from_lagna=house_lagna,
                    house_from_karakamsha=house_kl,
                    signification=sig_desc,
                )
            )

        # 4. Detect Jaimini Raja Yogas
        yogas: List[str] = []
        ak_p = karaka_map.get("AK", "")
        amk_p = karaka_map.get("AmK", "")
        pk_p = karaka_map.get("PK", "")
        dk_p = karaka_map.get("DK", "")

        ak_item = next((k for k in karaka_assignments if k.karaka_role == "AK"), None)
        amk_item = next((k for k in karaka_assignments if k.karaka_role == "AmK"), None)
        pk_item = next((k for k in karaka_assignments if k.karaka_role == "PK"), None)
        dk_item = next((k for k in karaka_assignments if k.karaka_role == "DK"), None)

        if ak_item and amk_item:
            # Conjunction in D1 or D9
            if ak_item.d1_rashi_idx == amk_item.d1_rashi_idx:
                yogas.append(f"AK-AmK Raja Yoga: Atmakaraka ({ak_p}) and Amatyakaraka ({amk_p}) conjoined in {ak_item.d1_rashi} (D1).")
            if ak_item.d9_rashi_idx == amk_item.d9_rashi_idx:
                yogas.append(f"Karakamsha AK-AmK Yoga: Atmakaraka and Amatyakaraka conjoined in Navamsha {ak_item.d9_rashi}.")

        if ak_item and pk_item:
            if ak_item.d1_rashi_idx == pk_item.d1_rashi_idx:
                yogas.append(f"AK-PK Raja Yoga: Atmakaraka ({ak_p}) and Putrakaraka ({pk_p}) conjoined in {ak_item.d1_rashi}.")
            if ak_item.d9_rashi_idx == pk_item.d9_rashi_idx:
                yogas.append(f"Karakamsha AK-PK Yoga: High intellect & Purvapunya in Navamsha {ak_item.d9_rashi}.")

        if ak_item and dk_item:
            if ak_item.d1_rashi_idx == dk_item.d1_rashi_idx:
                yogas.append(f"AK-DK Dhana/Raja Yoga: Atmakaraka ({ak_p}) and Darakaraka ({dk_p}) conjoined.")

        if ak_item and ak_item.house_from_lagna in (1, 5, 9, 10):
            yogas.append(f"Atmakaraka Fortification: {ak_p} well-placed in House {ak_item.house_from_lagna} from Lagna.")

        # 5. Check Moksha indicators (12th from Karakamsha)
        h12_kl_idx = (kl_rashi_idx + 11) % 12
        planets_in_12th_kl = [k.planet for k in karaka_assignments if k.d9_rashi_idx == h12_kl_idx]
        is_moksha = any(p in ("Jupiter", "Venus", "Moon") for p in planets_in_12th_kl)
        if is_moksha:
            yogas.append(f"Moksha Karakamsha Yoga: Benefic ({', '.join(planets_in_12th_kl)}) occupies 12th house from Karakamsha.")

        # 6. Overall synthesis summary
        theme = (
            f"Atmakaraka {ak_p} establishes Karakamsha Lagna in {ak_d9_rashi_name.capitalize()} (D9). "
            f"{len(yogas)} Jaimini Raja/Karaka alignments identified."
        )

        return KarakamshaSynthesisResult(
            atmakaraka_planet=ak_p,
            karakamsha_rashi=ak_d9_rashi_name.capitalize(),
            karakamsha_rashi_idx=kl_rashi_idx,
            chara_karakas=tuple(karaka_assignments),
            jaimini_raja_yogas=tuple(yogas),
            is_moksha_oriented=is_moksha,
            karakamsha_karmic_theme=theme,
            shastric_synthesis_summary=f"Karakamsha in {ak_d9_rashi_name.capitalize()} rules soul trajectory with {ak_p} as AK and {amk_p} as AmK.",
        )
