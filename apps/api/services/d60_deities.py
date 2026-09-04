"""
AstroOS — Shashtiamsa (D60) 60 Deities Engine
=============================================
Provides authentic classical D60 deity mappings according to:
  1. Brihat Parashara Hora Shastra (BPHS Chapter 6, default 'CheckD60' ON in Kundalee)
  2. Jataka Parijata (Adhyaya 1, slokas 36-41, 'CheckD60' OFF in Kundalee)

Mathematical Definition:
  - Each Rashi (30 degrees) is divided into 60 equal parts of 0.5 degrees (30 arcminutes).
  - Odd signs (1, 3, 5, 7, 9, 11): numbered 1 to 60 directly.
  - Even signs (2, 4, 6, 8, 10, 12): numbered 60 to 1 in reverse order.
  - Each deity has a classical disposition: Saumya (benefic) or Krura (malefic).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


BPHS_D60_DEITIES: list[tuple[int, str, str, str]] = [
    (1, "घोर", "Ghora", "krura"),
    (2, "राक्षस", "Rakshasa", "krura"),
    (3, "देव", "Deva", "saumya"),
    (4, "कुबेर", "Kubera", "saumya"),
    (5, "यक्ष", "Yaksha", "saumya"),
    (6, "किन्नर", "Kinnara", "saumya"),
    (7, "भ्रष्ट", "Bhrashta", "krura"),
    (8, "कुलघ्न", "Kulaghna", "krura"),
    (9, "गरल", "Garala", "krura"),
    (10, "वह्नि", "Vahni", "krura"),
    (11, "माया", "Maya", "krura"),
    (12, "पुरीषक", "Purishaka", "krura"),
    (13, "अपांपति", "Apampati", "saumya"),
    (14, "मरुत्वान", "Marutwana", "saumya"),
    (15, "काल", "Kala", "krura"),
    (16, "सर्प", "Sarpa", "krura"),
    (17, "अमृत", "Amrita", "saumya"),
    (18, "इन्दु", "Indu", "saumya"),
    (19, "मृदु", "Mridu", "saumya"),
    (20, "कोमल", "Komala", "saumya"),
    (21, "हेरम्ब", "Heramba", "saumya"),
    (22, "ब्रह्मा", "Brahma", "saumya"),
    (23, "विष्णु", "Vishnu", "saumya"),
    (24, "महेश्वर", "Maheshwara", "saumya"),
    (25, "देव", "Deva", "saumya"),
    (26, "आर्द्रा", "Ardra", "saumya"),
    (27, "कलिनाश", "Kalinasa", "saumya"),
    (28, "क्षितीश", "Kshiteesha", "saumya"),
    (29, "कमलाकर", "Kamalakara", "saumya"),
    (30, "गुलिक", "Gulika", "krura"),
    (31, "मृत्यु", "Mrityu", "krura"),
    (32, "काल", "Kala", "krura"),
    (33, "दावाग्नि", "Davagni", "krura"),
    (34, "घोर", "Ghora", "krura"),
    (35, "यम", "Yama", "krura"),
    (36, "कण्टक", "Kantaka", "krura"),
    (37, "सुधा", "Sudha", "saumya"),
    (38, "अमृत", "Amrita", "saumya"),
    (39, "पूर्णचन्द्र", "Purnachandra", "saumya"),
    (40, "विषदिग्ध", "Vishadagdha", "krura"),
    (41, "कुलनाशन", "Kulanasana", "krura"),
    (42, "वंशक्षय", "Vamshakshaya", "krura"),
    (43, "उत्पात", "Utpata", "krura"),
    (44, "काल", "Kala", "krura"),
    (45, "सौम्य", "Saumya", "saumya"),
    (46, "कोमल", "Komala", "saumya"),
    (47, "शीतल", "Shitala", "saumya"),
    (48, "करालदंष्ट्र", "Karaladamshtra", "krura"),
    (49, "चन्द्रमुखी", "Chandramukhi", "saumya"),
    (50, "प्रवीण", "Praveena", "saumya"),
    (51, "कालापावक", "Kalapavaka", "krura"),
    (52, "दण्डायुध", "Dandayudha", "krura"),
    (53, "निर्मल", "Nirmala", "saumya"),
    (54, "सौम्य", "Saumya", "saumya"),
    (55, "क्रूर", "Krura", "krura"),
    (56, "अतिशीतल", "Atisheetala", "saumya"),
    (57, "अमृत", "Amrita", "saumya"),
    (58, "पयोधि", "Payodhi", "saumya"),
    (59, "भ्रमण", "Bhramana", "krura"),
    (60, "चन्द्ररेखा", "Chandrarekha", "saumya"),
]

JATAKA_PARIJATA_D60_DEITIES: list[tuple[int, str, str, str]] = [
    (1, "घोर", "Ghora", "krura"),
    (2, "राक्षस", "Rakshasa", "krura"),
    (3, "चर", "Chara", "saumya"),
    (4, "यक्ष", "Yaksha", "saumya"),
    (5, "किन्नर", "Kinnara", "saumya"),
    (6, "कुबेर", "Kubera", "saumya"),
    (7, "भ्रष्ट", "Bhrashta", "krura"),
    (8, "कुलघ्न", "Kulaghna", "krura"),
    (9, "गरल", "Garala", "krura"),
    (10, "अग्नि", "Agni", "krura"),
    (11, "माया", "Maya", "krura"),
    (12, "यम", "Yama", "krura"),
    (13, "वरुण", "Varuna", "saumya"),
    (14, "इन्द्र", "Indra", "saumya"),
    (15, "काल", "Kala", "krura"),
    (16, "सर्प", "Sarpa", "krura"),
    (17, "अमृत", "Amrita", "saumya"),
    (18, "चन्द्र", "Chandra", "saumya"),
    (19, "मृदु", "Mridu", "saumya"),
    (20, "कोमल", "Komala", "saumya"),
    (21, "पद्म", "Padma", "saumya"),
    (22, "विष्णु", "Vishnu", "saumya"),
    (23, "वागीश", "Vagisha", "saumya"),
    (24, "दिगम्बर", "Digambara", "saumya"),
    (25, "देव", "Deva", "saumya"),
    (26, "आर्द्रा", "Ardra", "saumya"),
    (27, "कलिनाश", "Kalinasa", "saumya"),
    (28, "मुख्यपद", "Mukhyapada", "saumya"),
    (29, "कलानिधि", "Kalanidhi", "saumya"),
    (30, "मन्दगथ", "Mandagatha", "krura"),
    (31, "मृत्यु", "Mrityu", "krura"),
    (32, "काल", "Kala", "krura"),
    (33, "दावाग्नि", "Davagni", "krura"),
    (34, "भीम", "Bhima", "krura"),
    (35, "यम", "Yama", "krura"),
    (36, "कण्टक", "Kantaka", "krura"),
    (37, "सुधा", "Sudha", "saumya"),
    (38, "अमृत", "Amrita", "saumya"),
    (39, "पूर्णचन्द्र", "Purnachandra", "saumya"),
    (40, "विषदिग्ध", "Vishadagdha", "krura"),
    (41, "कुलनाशन", "Kulanasana", "krura"),
    (42, "वंशक्षय", "Vamshakshaya", "krura"),
    (43, "उत्पात", "Utpata", "krura"),
    (44, "काल", "Kala", "krura"),
    (45, "सौम्य", "Saumya", "saumya"),
    (46, "शुभ", "Shubha", "saumya"),
    (47, "शीतल", "Shitala", "saumya"),
    (48, "करालदंष्ट्र", "Karaladamshtra", "krura"),
    (49, "चन्द्रमुख", "Chandramukha", "saumya"),
    (50, "प्रवीण", "Praveena", "saumya"),
    (51, "कालापावक", "Kalapavaka", "krura"),
    (52, "दण्डायुध", "Dandayudha", "krura"),
    (53, "निर्मल", "Nirmala", "saumya"),
    (54, "शुभ", "Shubha", "saumya"),
    (55, "अशुभ", "Ashubha", "krura"),
    (56, "अतिशीतल", "Atisheetala", "saumya"),
    (57, "सुधासुत", "Sudhasuta", "saumya"),
    (58, "पयोधि", "Payodhi", "saumya"),
    (59, "भ्रमण", "Bhramana", "krura"),
    (60, "इन्दुरेखा", "Indurekha", "saumya"),
]


@dataclass(frozen=True)
class D60DeityResult:
    part_index_in_rashi: int
    shashtiamsa_number: int
    rashi_index: int
    is_odd_rashi: bool
    deity_name_sanskrit: str
    deity_name_english: str
    nature: Literal["saumya", "krura"]
    tradition: Literal["bphs", "jataka_parijata"]


def get_d60_deity(
    longitude_deg: float,
    tradition: Literal["bphs", "jataka_parijata"] = "bphs",
) -> D60DeityResult:
    lon = longitude_deg % 360.0
    rashi_idx = int(lon // 30.0) + 1
    degree_in_rashi = lon % 30.0

    part_idx = int(degree_in_rashi // 0.5) + 1
    part_idx = min(60, max(1, part_idx))

    is_odd = (rashi_idx % 2 == 1)
    if is_odd:
        deity_idx = part_idx
    else:
        deity_idx = 61 - part_idx

    table = BPHS_D60_DEITIES if tradition.lower() == "bphs" else JATAKA_PARIJATA_D60_DEITIES
    entry = table[deity_idx - 1]

    return D60DeityResult(
        part_index_in_rashi=part_idx,
        shashtiamsa_number=deity_idx,
        rashi_index=rashi_idx,
        is_odd_rashi=is_odd,
        deity_name_sanskrit=entry[1],
        deity_name_english=entry[2],
        nature=entry[3],
        tradition=tradition.lower(),
    )

def evaluate_chart_d60_deities(
    graha_longitudes: dict[str, float],
    tradition: Literal["bphs", "jataka_parijata"] = "bphs",
) -> dict[str, dict[str, any]]:
    """Evaluates D60 deity for each graha in a chart."""
    results = {}
    for p, lon in graha_longitudes.items():
        res = get_d60_deity(lon, tradition=tradition)
        results[p] = {
            "longitude": lon,
            "part_in_rashi": res.part_index_in_rashi,
            "d60_number": res.shashtiamsa_number,
            "deity_sanskrit": res.deity_name_sanskrit,
            "deity_english": res.deity_name_english,
            "nature": res.nature,
            "tradition": res.tradition,
        }
    return results