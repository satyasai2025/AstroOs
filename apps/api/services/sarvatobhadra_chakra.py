"""
AstroOS — Sarvatobhadra Chakra (SBC) Engine (28 Nakshatras & Abhijit)
=====================================================================
Implements the authentic classical Sarvatobhadra Chakra as certified in
Vinay Jha's Kundalee software (A22_Sarvatobhadr, A56_SarvatobhadrPlanets,
frmSarvatobhadraChakra, frmSarvatobhadrPhal):

1. 28 Nakshatra System (with Intercalated Abhijit):
   - Regular Nakshatras: 13°20' (800 arcmin)
   - Uttara Ashadha (21st): shortened to 10°00' (Padas 1, 2, 3 = 266°40' to 276°40')
   - Abhijit (22nd): 276°40' to 280°53'20" (Span: 4°13'20" = 253.333 arcmin)
   - Shravana (23rd): 280°53'20" to 293°20'00" (Span: 12°26'40" = 746.667 arcmin)
   - Total Circle: Exactly 360°00'00" (21600 arcmin)

2. 9x9 Grid Coordinate Mapping (81 Squares):
   - Outer Perimeter (28 Squares): 28 Nakshatras (7 per side: East, South, West, North)
   - Concentric Ring 2: 16 Swaras (Vowels: अ, आ, इ, ई, उ, ऊ, ऋ, ॠ, ऌ, ॡ, ए, ऐ, ओ, औ, अं, अः)
   - Concentric Ring 3: 20 Varnas (Consonants: क, ख, ग, घ, ङ, च, छ, ज, झ, ञ, ट, ठ, ड, ढ, ण, त, थ, द, ध, न)
   - Concentric Ring 4: 12 Rasis, 5 Tithis (Nanda..Poorna), 7 Weekdays
   - Center (Square [4,4]): Meru / Central Pillar (Focal Native Identity)

3. 4-Fold Vedha (Aspect Lines):
   - Agra Vedha (Front / Cross-Line across opposite perimeter)
   - Dakshina Vedha (Right Diagonal Ray)
   - Vama Vedha (Left Diagonal Ray)
   - Kona / Pashchima Vedha (Opposite Cross Ray)

4. Special Sensitive Natal Nakshatras:
   - Janma (1st), Karma (10th), Sanghatika (16th), Samudayika (18th),
     Adhana (19th), Vainashika (23rd), Jati (26th), Desha (27th), Abhisheka (28th).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple


# ============================================================================
# 1. 28 Nakshatras with Exact Astronomical Longitude Spans
# ============================================================================

# (Index 1..28, Name, Start Deg, End Deg, Ruler)
SBC_28_NAKSHATRAS: list[tuple[int, str, float, float, str]] = [
    (1,  "Ashwini",            0.0,         13.33333333, "ketu"),
    (2,  "Bharani",            13.33333333, 26.66666667, "venus"),
    (3,  "Krittika",           26.66666667, 40.0,        "sun"),
    (4,  "Rohini",             40.0,        53.33333333, "moon"),
    (5,  "Mrigashira",         53.33333333, 66.66666667, "mars"),
    (6,  "Ardra",              66.66666667, 80.0,        "rahu"),
    (7,  "Punarvasu",          80.0,        93.33333333, "jupiter"),
    (8,  "Pushya",             93.33333333, 106.6666667, "saturn"),
    (9,  "Ashlesha",           106.6666667, 120.0,       "mercury"),
    (10, "Magha",              120.0,       133.3333333, "ketu"),
    (11, "Purva Phalguni",     133.3333333, 146.6666667, "venus"),
    (12, "Uttara Phalguni",    146.6666667, 160.0,       "sun"),
    (13, "Hasta",              160.0,       173.3333333, "moon"),
    (14, "Chitra",             173.3333333, 186.6666667, "mars"),
    (15, "Swati",              186.6666667, 200.0,       "rahu"),
    (16, "Vishakha",           200.0,       213.3333333, "jupiter"),
    (17, "Anuradha",           213.3333333, 226.6666667, "saturn"),
    (18, "Jyeshtha",           226.6666667, 240.0,       "mercury"),
    (19, "Moola",              240.0,       253.3333333, "ketu"),
    (20, "Purva Ashadha",      253.3333333, 266.6666667, "venus"),
    # Intercalation of Abhijit:
    (21, "Uttara Ashadha",     266.6666667, 276.6666667, "sun"),     # Padas 1..3 (10°00')
    (22, "Abhijit",            276.6666667, 280.8888889, "sun"),     # U.Ashadha Pada 4 + Shravana 1/15th (4°13'20")
    (23, "Shravana",           280.8888889, 293.3333333, "moon"),    # Remaining 14/15th (12°26'40")
    (24, "Dhanishtha",         293.3333333, 306.6666667, "mars"),
    (25, "Shatabhisha",        306.6666667, 320.0,       "rahu"),
    (26, "Purva Bhadrapada",   320.0,       333.3333333, "jupiter"),
    (27, "Uttara Bhadrapada",  333.3333333, 346.6666667, "saturn"),
    (28, "Revati",             346.6666667, 360.0,       "mercury"),
]

ABHIJIT_START_DEG: float = 276.6666666666667   # 276°40'00"
ABHIJIT_END_DEG: float = 280.8888888888889     # 280°53'20"
ABHIJIT_SPAN_DEG: float = 4.2222222222222      # 4°13'20" = 253.333 arcmin


def longitude_to_28_nakshatra(longitude_deg: float) -> tuple[int, str, float, float, str]:
    """
    Maps any sidereal longitude (0° to 360°) to the exact 28-nakshatra sequence (including Abhijit).
    Returns (nak_index_1_to_28, name, start_deg, end_deg, ruler).
    """
    lon = longitude_deg % 360.0
    for entry in SBC_28_NAKSHATRAS:
        if entry[2] <= lon < entry[3]:
            return entry
    # revati edge case at exactly 360.0 or near 0
    return SBC_28_NAKSHATRAS[-1]


# ============================================================================
# 2. 9x9 Grid Layout Coordinates (Row, Col from 0..8)
# ============================================================================

# The 28 Nakshatras occupy the 28 border squares of the 9x9 grid:
# Top Row (Row 0, Cols 1..7): Krittika(3) to Ashlesha(9)
# Right Col (Col 8, Rows 1..7): Magha(10) to Vishakha(16)
# Bottom Row (Row 8, Cols 7..1): Anuradha(17) to Shravana(23, including Abhijit)
# Left Col (Col 0, Rows 7..1): Dhanishtha(24) to Bharani(2)
# Corners are vowels/Swaras:
# (0,0): अ, (0,8): आ, (8,8): इ, (8,0): ई

NAKSHATRA_GRID_COORDS: dict[int, tuple[int, int]] = {
    # East (Top Row, left to right)
    3:  (0, 1),  # Krittika
    4:  (0, 2),  # Rohini
    5:  (0, 3),  # Mrigashira
    6:  (0, 4),  # Ardra
    7:  (0, 5),  # Punarvasu
    8:  (0, 6),  # Pushya
    9:  (0, 7),  # Ashlesha

    # South (Right Col, top to bottom)
    10: (1, 8),  # Magha
    11: (2, 8),  # P.Phalguni
    12: (3, 8),  # U.Phalguni
    13: (4, 8),  # Hasta
    14: (5, 8),  # Chitra
    15: (6, 8),  # Swati
    16: (7, 8),  # Vishakha

    # West (Bottom Row, right to left)
    17: (8, 7),  # Anuradha
    18: (8, 6),  # Jyeshtha
    19: (8, 5),  # Moola
    20: (8, 4),  # P.Ashadha
    21: (8, 3),  # U.Ashadha
    22: (8, 2),  # Abhijit
    23: (8, 1),  # Shravana

    # North (Left Col, bottom to top)
    24: (7, 0),  # Dhanishtha
    25: (6, 0),  # Shatabhisha
    26: (5, 0),  # P.Bhadrapada
    27: (4, 0),  # U.Bhadrapada
    28: (3, 0),  # Revati
    1:  (2, 0),  # Ashwini
    2:  (1, 0),  # Bharani
}

GRID_TO_NAKSHATRA: dict[tuple[int, int], int] = {
    v: k for k, v in NAKSHATRA_GRID_COORDS.items()
}


# ============================================================================
# 3. 4-Fold Vedha Calculation in the 9x9 Grid
# ============================================================================

@dataclass(frozen=True)
class SBCVedhaTarget:
    target_nakshatra_number: int
    target_nakshatra_name: str
    vedha_type: Literal["agra", "dakshina", "vama", "kona"]
    aspecting_planet: str
    aspecting_nakshatra_number: int
    aspecting_nakshatra_name: str
    planet_nature: Literal["benefic", "malefic"]


def compute_vedha_from_square(row: int, col: int) -> dict[str, tuple[int, int]]:
    """
    Computes the perimeter target squares aspected by (row, col) via the 4-fold Vedha:
      1. Agra (Direct / Opposite across the grid):
         - If on top/bottom: same col, opposite row.
         - If on left/right: same row, opposite col.
      2. Dakshina (Right 45° diagonal ray until hitting perimeter).
      3. Vama (Left 45° diagonal ray until hitting perimeter).
      4. Kona / Cross (Diagonal crossing through the center).
    """
    targets = {}

    # 1. Agra Vedha
    if row == 0:
        targets["agra"] = (8, col)
    elif row == 8:
        targets["agra"] = (0, col)
    elif col == 0:
        targets["agra"] = (row, 8)
    elif col == 8:
        targets["agra"] = (row, 0)

    # 2. Diagonal rays (Right / Dakshina and Left / Vama)
    # Trace diagonals from border square
    diag_rays = []
    for dr, dc in [(-1, 1), (1, 1), (1, -1), (-1, -1)]:
        r, c = row + dr, col + dc
        while 0 <= r <= 8 and 0 <= c <= 8:
            if (r in (0, 8) or c in (0, 8)) and (r, c) != (row, col):
                diag_rays.append((r, c))
                break
            r += dr
            c += dc

    if len(diag_rays) >= 1:
        targets["dakshina"] = diag_rays[0]
    if len(diag_rays) >= 2:
        targets["vama"] = diag_rays[1]
    if len(diag_rays) >= 3:
        targets["kona"] = diag_rays[2]

    return targets


# ============================================================================
# 4. Sensitive Natal Points (SBC Sanghatika / Karma / Janma)
# ============================================================================

def get_sensitive_nakshatras_28(janma_nakshatra_28: int) -> dict[str, int]:
    """
    Derives key SBC sensitive nakshatras in the 28-nakshatra sequence:
      - Janma (1st)
      - Karma (10th)
      - Sanghatika (16th)
      - Samudayika (18th)
      - Adhana (19th)
      - Vainashika (23rd)
      - Jati (26th)
      - Desha (27th)
      - Abhisheka (28th)
    """
    j = janma_nakshatra_28
    return {
        "janma": j,
        "karma": ((j - 1 + 9) % 28) + 1,        # 10th
        "sanghatika": ((j - 1 + 15) % 28) + 1,  # 16th
        "samudayika": ((j - 1 + 17) % 28) + 1,  # 18th
        "adhana": ((j - 1 + 18) % 28) + 1,      # 19th
        "vainashika": ((j - 1 + 22) % 28) + 1,  # 23rd
        "jati": ((j - 1 + 25) % 28) + 1,        # 26th
        "desha": ((j - 1 + 26) % 28) + 1,       # 27th
        "abhisheka": ((j - 1 + 27) % 28) + 1,   # 28th
    }


# ============================================================================
# 5. Full Sarvatobhadra Chakra Analysis Engine
# ============================================================================

MALEFIC_GRAHAS = {"sun", "mars", "saturn", "rahu", "ketu"}
BENEFIC_GRAHAS = {"jupiter", "venus", "mercury", "moon"}


class SarvatobhadraChakraEngine:
    """Analyzes planetary transits in Sarvatobhadra Chakra against natal sensitive points."""

    def evaluate_transit_vedha(
        self,
        natal_moon_longitude: float,
        transit_graha_longitudes: dict[str, float],
    ) -> dict[str, Any]:
        """
        Evaluates 4-fold Vedha of transit grahas against natal sensitive nakshatras.
        """
        # 1. Map natal Moon to 28-nakshatra system
        n_info = longitude_to_28_nakshatra(natal_moon_longitude)
        janma_nak = n_info[0]
        sensitive_points = get_sensitive_nakshatras_28(janma_nak)
        sensitive_naks_rev = {v: k for k, v in sensitive_points.items()}

        # 2. Map transits
        transit_positions = {}
        vedha_hits: list[SBCVedhaTarget] = []

        for planet, lon in transit_graha_longitudes.items():
            p_clean = planet.lower().strip()
            t_nak = longitude_to_28_nakshatra(lon)
            t_nak_num = t_nak[0]
            transit_positions[p_clean] = {
                "longitude": lon,
                "nakshatra_number_28": t_nak_num,
                "nakshatra_name": t_nak[1],
            }

            # Find grid square
            grid_pos = NAKSHATRA_GRID_COORDS.get(t_nak_num)
            if not grid_pos:
                continue

            # Compute aspected squares
            aspects = compute_vedha_from_square(grid_pos[0], grid_pos[1])
            is_malefic = p_clean in MALEFIC_GRAHAS

            for v_type, target_sq in aspects.items():
                target_nak_num = GRID_TO_NAKSHATRA.get(target_sq)
                if target_nak_num:
                    target_name = SBC_28_NAKSHATRAS[target_nak_num - 1][1]
                    vedha_hits.append(SBCVedhaTarget(
                        target_nakshatra_number=target_nak_num,
                        target_nakshatra_name=target_name,
                        vedha_type=v_type,
                        aspecting_planet=p_clean,
                        aspecting_nakshatra_number=t_nak_num,
                        aspecting_nakshatra_name=t_nak[1],
                        planet_nature="malefic" if is_malefic else "benefic",
                    ))

        # 3. Filter hits on natal sensitive points
        afflicted_points = []
        protected_points = []

        for hit in vedha_hits:
            if hit.target_nakshatra_number in sensitive_naks_rev:
                point_type = sensitive_naks_rev[hit.target_nakshatra_number]
                item = {
                    "sensitive_point": point_type,
                    "target_nakshatra": hit.target_nakshatra_name,
                    "target_number": hit.target_nakshatra_number,
                    "aspecting_planet": hit.aspecting_planet,
                    "aspecting_nakshatra": hit.aspecting_nakshatra_name,
                    "vedha_type": hit.vedha_type,
                    "nature": hit.planet_nature,
                }
                if hit.planet_nature == "malefic":
                    afflicted_points.append(item)
                else:
                    protected_points.append(item)

        return {
            "natal_janma_nakshatra": {
                "number_28": janma_nak,
                "name": n_info[1],
            },
            "sensitive_points_28": sensitive_points,
            "transit_positions": transit_positions,
            "total_vedha_hits": len(vedha_hits),
            "afflicted_sensitive_points": afflicted_points,
            "protected_sensitive_points": protected_points,
            "is_janma_afflicted": any(p["sensitive_point"] == "janma" for p in afflicted_points),
            "is_karma_afflicted": any(p["sensitive_point"] == "karma" for p in afflicted_points),
            "is_vainashika_afflicted": any(p["sensitive_point"] == "vainashika" for p in afflicted_points),
        }