"""
AstroOS — Sarvatobhadra Chakra (SBC) CellNum Vedha-Path Table

**Sourcing.** Extracted directly from a real, working SBC tool
(`2026-07-20_SarvatobhadraChakra_Vedhas_rev3.xlsm`, sheet `Vedha_Map`,
columns T:X, header row 3 — "Cell Num" / "Cell Content" / "Right Vedha
Cell Num" / "Front Vedha Cell Num" / "Left Vedha Cell Num"). This is a
different (and more complete) table from the tool's own Pada112 table
(same sheet, columns Z:AJ) — that one stops at 108 rows and has no
Abhijit entries at all, a genuine gap in the source tool itself (its own
author flags cell A2: "NEEDS VERIFICATION: the Sravana / Dhanishta /
Shatabhisha and Abhijit Vedha pairs vary between classical sources").

CellNum uses a 1-81 index over the same 9x9 SBC grid this codebase
already derives independently in sarvatobhadra_grid.py (from Saravali,
https://saravali.github.io/astrology/sbc_basics.html) — just numbered
column-major (1-81) instead of (col, row) tuples. The 28-nakshatra
cyclic sequence around the perimeter matches sarvatobhadra_grid.py's
SBC_BORDER exactly, side-for-side and nakshatra-for-nakshatra, including
Abhijit's position between Uttara Ashadha and Shravana. Four corner
cells (1, 9, 73, 81 — labelled with Devanagari vowels in the source
sheet, e.g. "अ") have no nakshatra occupant and only a Right-direction
path, consistent with them being grid junctions rather than nakshatra
cells.

**Verification.** Cell 37 (Uttara Bhadrapada) here matches the worked
example already independently documented from this same source tool:
Right `47,57,67,77`, Front `38,39,40,41,42,43,44,45`, Left `29,21,13,5`.
Dhanishtha (cell 64) and Shatabhisha (cell 55) were separately confirmed
against live JHora screenshots in this session (JHora's diagonal/
straight-line highlights for both nakshatras landed exactly on the
border cells this table's geometry predicts).

**Scope.** This table's Right/Front/Left entries are lists of CellNum
values a Vedha ray from that nakshatra passes through (used for
CellNum-granularity hit-testing per modSBC_Vedha.bas's real mechanism —
see sbc_vedha_engine.py), not single point targets. This is coarser
than true pada-level (112) precision, which the source tool itself does
not have a complete/Abhijit-inclusive table for; do not conflate this
with sarvatobhadra_grid.py's SBC_BORDER, which uses a different (col,
row) coordinate scheme for the same 28-cell perimeter.

**Column-naming gotcha, confirmed by cross-checking against
sarvatobhadra_grid.py's independently-derived (and JHora-verified, this
session) Forward/Opposite/Backward values for Dhanishtha and
Shatabhisha:** this table's "front"/"left"/"right" column names do NOT
correspond 1:1 by name to the classical Forward/Opposite/Backward terms
used elsewhere in this codebase. The actual correspondence is:
  - this table's **left**  == sarvatobhadra_grid.py's **Forward** (clockwise diagonal)
  - this table's **front** == sarvatobhadra_grid.py's **Opposite** (straight across)
  - this table's **right** == sarvatobhadra_grid.py's **Backward** (counter-clockwise diagonal)
Verified both ways: Dhanishtha's `left` path ends at Ashlesha (cellnum
8) matching Forward=Ashlesha; `front` ends at Vishakha (72) matching
Opposite=Vishakha; `right` is Shravana (74) matching Backward=Shravana.
Shatabhisha's `left` ends at Pushya (7) matching Forward=Pushya;
`front` ends at Swati (63) matching Opposite=Swati; `right` is Abhijit
(75) matching Backward=Abhijit (the specific pair JHora-confirmed this
session). sbc_vedha_engine.py's motion-state rule ("Normal speed ->
Front") therefore casts via this table's literal "front" column (i.e.
the classical *Opposite* ray), not the classical Forward ray — this is
what the source tool's own VBA does, not a bug; do not "fix" the
direction names to match classical terminology without re-deriving the
motion-to-direction rule from the VBA source first.
"""

from __future__ import annotations

from typing import NamedTuple, Optional


class SBCCellAnchor(NamedTuple):
    cellnum: int
    nakshatra: Optional[str]  # None for the 4 corner junction cells
    right: tuple[int, ...]
    front: tuple[int, ...]  # empty for corners
    left: tuple[int, ...]  # empty for corners


# (cellnum, nakshatra_token_or_None, right_path, front_path, left_path)
_RAW: list[tuple[int, Optional[str], tuple[int, ...], tuple[int, ...], tuple[int, ...]]] = [
    (1, None, (11, 21, 31, 41, 51, 61, 71, 81), (), ()),
    (2, "krittika", (10,), (11, 20, 29, 38, 47, 56, 65, 74), (12, 22, 32, 42, 52, 62, 72)),
    (3, "rohini", (11, 19), (12, 21, 30, 39, 48, 57, 66, 75), (13, 23, 33, 43, 53, 63)),
    (4, "mrigashira", (12, 20, 28), (13, 22, 31, 40, 49, 58, 67, 76), (14, 24, 34, 44, 54)),
    (5, "ardra", (13, 21, 29, 37), (14, 23, 32, 41, 50, 59, 68, 77), (15, 25, 35, 45)),
    (6, "punarvasu", (14, 22, 30, 38, 46), (15, 24, 33, 42, 51, 60, 69, 78), (16, 26, 36)),
    (7, "pushya", (15, 23, 31, 39, 47, 55), (16, 25, 34, 43, 52, 61, 70, 79), (17, 27)),
    (8, "ashlesha", (16, 24, 32, 40, 48, 56, 64), (17, 26, 35, 44, 53, 62, 71, 80), (18,)),
    (9, None, (17, 25, 33, 41, 49, 57, 65, 73), (), ()),
    (18, "magha", (8,), (17, 16, 15, 14, 13, 12, 11, 10), (26, 34, 42, 50, 58, 66, 74)),
    (27, "purva_phalguni", (17, 7), (26, 25, 24, 23, 22, 21, 20, 19), (35, 43, 51, 59, 67, 75)),
    (36, "uttara_phalguni", (26, 16, 6), (35, 34, 33, 32, 31, 30, 29, 28), (44, 52, 60, 68, 76)),
    (45, "hasta", (35, 25, 15, 5), (44, 43, 42, 41, 40, 39, 38, 37), (53, 61, 69, 77)),
    (54, "chitra", (44, 34, 24, 14, 4), (53, 52, 51, 50, 49, 48, 47, 46), (62, 70, 78)),
    (63, "swati", (53, 43, 33, 23, 13, 3), (62, 61, 60, 59, 58, 57, 56, 55), (71, 79)),
    (72, "vishakha", (62, 52, 42, 32, 22, 12, 2), (71, 70, 69, 68, 67, 66, 65, 64), (80,)),
    (81, None, (71, 61, 51, 41, 31, 21, 11, 1), (), ()),
    (80, "anuradha", (72,), (71, 62, 53, 44, 35, 26, 17, 8), (70, 60, 50, 40, 30, 20, 10)),
    (79, "jyeshtha", (71, 63), (70, 61, 52, 43, 34, 25, 16, 7), (69, 59, 49, 39, 29, 19)),
    (78, "mula", (70, 62, 54), (69, 60, 51, 42, 33, 24, 15, 6), (68, 58, 48, 38, 28)),
    (77, "purva_ashadha", (69, 61, 53, 45), (68, 59, 50, 41, 32, 23, 14, 5), (67, 57, 47, 37)),
    (76, "uttara_ashadha", (68, 60, 52, 44, 36), (67, 58, 49, 40, 31, 22, 13, 4), (66, 56, 46)),
    (75, "abhijit", (67, 59, 51, 43, 35, 27), (66, 57, 48, 39, 30, 21, 12, 3), (65, 55)),
    (74, "shravana", (66, 58, 50, 42, 34, 26, 18), (65, 56, 47, 38, 29, 20, 11, 2), (64,)),
    (73, None, (65, 57, 49, 41, 33, 25, 17, 9), (), ()),
    (64, "dhanishtha", (74,), (65, 66, 67, 68, 69, 70, 71, 72), (56, 48, 40, 32, 24, 16, 8)),
    (55, "shatabhisha", (65, 75), (56, 57, 58, 59, 60, 61, 62, 63), (47, 39, 31, 23, 15, 7)),
    (46, "purva_bhadrapada", (56, 66, 76), (47, 48, 49, 50, 51, 52, 53, 54), (38, 30, 22, 14, 6)),
    (37, "uttara_bhadrapada", (47, 57, 67, 77), (38, 39, 40, 41, 42, 43, 44, 45), (29, 21, 13, 5)),
    (28, "revati", (38, 48, 58, 68, 78), (29, 30, 31, 32, 33, 34, 35, 36), (20, 12, 4)),
    (19, "ashwini", (29, 39, 49, 59, 69, 79), (20, 21, 22, 23, 24, 25, 26, 27), (11, 3)),
    (10, "bharani", (20, 30, 40, 50, 60, 70, 80), (11, 12, 13, 14, 15, 16, 17, 18), (2,)),
]

SBC_CELLNUM_ANCHORS: dict[int, SBCCellAnchor] = {
    cellnum: SBCCellAnchor(cellnum, nak, right, front, left)
    for cellnum, nak, right, front, left in _RAW
}

# Reverse lookup: nakshatra token -> its anchor CellNum (corners excluded, they have no nakshatra).
NAKSHATRA_TO_CELLNUM: dict[str, int] = {
    anchor.nakshatra: anchor.cellnum
    for anchor in SBC_CELLNUM_ANCHORS.values()
    if anchor.nakshatra is not None
}

assert len(NAKSHATRA_TO_CELLNUM) == 28, "Expected all 28 SBC nakshatras (27 + Abhijit)"



def cellnum_for_nakshatra(nakshatra: str) -> int:
    """Anchor CellNum (1-81) for a 28-system nakshatra token (incl. 'abhijit')."""
    return NAKSHATRA_TO_CELLNUM[nakshatra]


def vedha_path(nakshatra: str, direction: str) -> tuple[int, ...]:
    """
    CellNum path for `nakshatra`'s Vedha ray in the given `direction`
    ("front", "left", or "right"). A transiting planet at any CellNum in
    this path is considered vedha-hit from `nakshatra`.
    """
    anchor = SBC_CELLNUM_ANCHORS[cellnum_for_nakshatra(nakshatra)]
    return getattr(anchor, direction)


class SBCCellSemantic(NamedTuple):
    col: int
    row: int
    category: str  # "nakshatra" | "rashi" | "swara" | "akshara" | "tithi"
    key: str
    display_name_en: str
    display_name_hi: str
    layer: int
    cell_num: int
    metadata: dict[str, any]


# Canonical 81-cell matrix (28 Nakshatra + 12 Rashi + 16 Swara + 20 Akshara + 5 Tithi = 81)
SBC_81_CANONICAL: dict[tuple[int, int], SBCCellSemantic] = {
    # ── Ring 1 (9x9 Border): 4 Swaras (Corners) + 28 Nakshatras ───────────────
    (1, 1): SBCCellSemantic(1, 1, "swara", "swara_a", "a", "अ", 1, 1, {"corner": "NW"}),
    (2, 1): SBCCellSemantic(2, 1, "nakshatra", "dhanishtha", "Dhanishtha", "धनिष्ठा", 1, 64, {"nakshatra_number": 23, "nakshatra_token": "dhanishtha"}),
    (3, 1): SBCCellSemantic(3, 1, "nakshatra", "shatabhisha", "Shatabhisha", "शतभिषा", 1, 55, {"nakshatra_number": 24, "nakshatra_token": "shatabhisha"}),
    (4, 1): SBCCellSemantic(4, 1, "nakshatra", "purva_bhadrapada", "Purva Bhadra", "पू.भाद्र.", 1, 46, {"nakshatra_number": 25, "nakshatra_token": "purva_bhadrapada"}),
    (5, 1): SBCCellSemantic(5, 1, "nakshatra", "uttara_bhadrapada", "Uttara Bhadra", "उ.भाद्र.", 1, 37, {"nakshatra_number": 26, "nakshatra_token": "uttara_bhadrapada"}),
    (6, 1): SBCCellSemantic(6, 1, "nakshatra", "revati", "Revati", "रेवती", 1, 28, {"nakshatra_number": 27, "nakshatra_token": "revati"}),
    (7, 1): SBCCellSemantic(7, 1, "nakshatra", "ashwini", "Ashwini", "अश्विनी", 1, 19, {"nakshatra_number": 1, "nakshatra_token": "ashwini"}),
    (8, 1): SBCCellSemantic(8, 1, "nakshatra", "bharani", "Bharani", "भरणी", 1, 10, {"nakshatra_number": 2, "nakshatra_token": "bharani"}),
    (9, 1): SBCCellSemantic(9, 1, "swara", "swara_aa", "ā", "आ", 1, 9, {"corner": "NE"}),

    (9, 2): SBCCellSemantic(9, 2, "nakshatra", "krittika", "Krittika", "कृत्तिका", 1, 2, {"nakshatra_number": 3, "nakshatra_token": "krittika"}),
    (9, 3): SBCCellSemantic(9, 3, "nakshatra", "rohini", "Rohini", "रोहिणी", 1, 3, {"nakshatra_number": 4, "nakshatra_token": "rohini"}),
    (9, 4): SBCCellSemantic(9, 4, "nakshatra", "mrigashira", "Mrigashira", "मृगशिरा", 1, 4, {"nakshatra_number": 5, "nakshatra_token": "mrigashira"}),
    (9, 5): SBCCellSemantic(9, 5, "nakshatra", "ardra", "Ardra", "आर्द्रा", 1, 5, {"nakshatra_number": 6, "nakshatra_token": "ardra"}),
    (9, 6): SBCCellSemantic(9, 6, "nakshatra", "punarvasu", "Punarvasu", "पुनर्वसु", 1, 6, {"nakshatra_number": 7, "nakshatra_token": "punarvasu"}),
    (9, 7): SBCCellSemantic(9, 7, "nakshatra", "pushya", "Pushya", "पुष्य", 1, 7, {"nakshatra_number": 8, "nakshatra_token": "pushya"}),
    (9, 8): SBCCellSemantic(9, 8, "nakshatra", "ashlesha", "Ashlesha", "आश्लेषा", 1, 8, {"nakshatra_number": 9, "nakshatra_token": "ashlesha"}),
    (9, 9): SBCCellSemantic(9, 9, "swara", "swara_i", "i", "इ", 1, 81, {"corner": "SE"}),

    (8, 9): SBCCellSemantic(8, 9, "nakshatra", "magha", "Magha", "मघा", 1, 18, {"nakshatra_number": 10, "nakshatra_token": "magha"}),
    (7, 9): SBCCellSemantic(7, 9, "nakshatra", "purva_phalguni", "Purva Phalguni", "पू.फाल्गुनी", 1, 27, {"nakshatra_number": 11, "nakshatra_token": "purva_phalguni"}),
    (6, 9): SBCCellSemantic(6, 9, "nakshatra", "uttara_phalguni", "Uttara Phalguni", "उ.फाल्गुनी", 1, 36, {"nakshatra_number": 12, "nakshatra_token": "uttara_phalguni"}),
    (5, 9): SBCCellSemantic(5, 9, "nakshatra", "hasta", "Hasta", "हस्त", 1, 45, {"nakshatra_number": 13, "nakshatra_token": "hasta"}),
    (4, 9): SBCCellSemantic(4, 9, "nakshatra", "chitra", "Chitra", "चित्रा", 1, 54, {"nakshatra_number": 14, "nakshatra_token": "chitra"}),
    (3, 9): SBCCellSemantic(3, 9, "nakshatra", "swati", "Swati", "स्वाती", 1, 63, {"nakshatra_number": 15, "nakshatra_token": "swati"}),
    (2, 9): SBCCellSemantic(2, 9, "nakshatra", "vishakha", "Vishakha", "विशाखा", 1, 72, {"nakshatra_number": 16, "nakshatra_token": "vishakha"}),
    (1, 9): SBCCellSemantic(1, 9, "swara", "swara_ee", "ī", "ई", 1, 73, {"corner": "SW"}),

    (1, 8): SBCCellSemantic(1, 8, "nakshatra", "anuradha", "Anuradha", "अनुराधा", 1, 80, {"nakshatra_number": 17, "nakshatra_token": "anuradha"}),
    (1, 7): SBCCellSemantic(1, 7, "nakshatra", "jyeshtha", "Jyeshtha", "ज्येष्ठा", 1, 79, {"nakshatra_number": 18, "nakshatra_token": "jyeshtha"}),
    (1, 6): SBCCellSemantic(1, 6, "nakshatra", "mula", "Mula", "मूल", 1, 78, {"nakshatra_number": 19, "nakshatra_token": "mula"}),
    (1, 5): SBCCellSemantic(1, 5, "nakshatra", "purva_ashadha", "Purva Ashadha", "पूर्वाषाढ़ा", 1, 77, {"nakshatra_number": 20, "nakshatra_token": "purva_ashadha"}),
    (1, 4): SBCCellSemantic(1, 4, "nakshatra", "uttara_ashadha", "Uttara Ashadha", "उत्तराषाढ़ा", 1, 76, {"nakshatra_number": 21, "nakshatra_token": "uttara_ashadha"}),
    (1, 3): SBCCellSemantic(1, 3, "nakshatra", "abhijit", "Abhijit", "अभिजित", 1, 75, {"nakshatra_number": 28, "nakshatra_token": "abhijit"}),
    (1, 2): SBCCellSemantic(1, 2, "nakshatra", "shravana", "Shravana", "श्रवण", 1, 74, {"nakshatra_number": 22, "nakshatra_token": "shravana"}),

    # ── Ring 2 (7x7 Border): 4 Swaras (Corners) + 20 Aksharas (5 per side) ──
    (2, 2): SBCCellSemantic(2, 2, "swara", "swara_u", "u", "उ", 2, 65, {"corner": "NW"}),
    (3, 2): SBCCellSemantic(3, 2, "akshara", "akshara_ka", "ka", "क", 2, 56, {}),
    (4, 2): SBCCellSemantic(4, 2, "akshara", "akshara_kha", "kha", "ख", 2, 47, {}),
    (5, 2): SBCCellSemantic(5, 2, "akshara", "akshara_ga", "ga", "ग", 2, 38, {}),
    (6, 2): SBCCellSemantic(6, 2, "akshara", "akshara_gha", "gha", "घ", 2, 29, {}),
    (7, 2): SBCCellSemantic(7, 2, "akshara", "akshara_nga", "ṅa", "ङ", 2, 20, {}),
    (8, 2): SBCCellSemantic(8, 2, "swara", "swara_uu", "ū", "ऊ", 2, 11, {"corner": "NE"}),

    (8, 3): SBCCellSemantic(8, 3, "akshara", "akshara_ca", "ca", "च", 2, 12, {}),
    (8, 4): SBCCellSemantic(8, 4, "akshara", "akshara_cha", "cha", "छ", 2, 13, {}),
    (8, 5): SBCCellSemantic(8, 5, "akshara", "akshara_ja", "ja", "ज", 2, 14, {}),
    (8, 6): SBCCellSemantic(8, 6, "akshara", "akshara_jha", "jha", "झ", 2, 15, {}),
    (8, 7): SBCCellSemantic(8, 7, "akshara", "akshara_nya", "ña", "ञ", 2, 16, {}),
    (8, 8): SBCCellSemantic(8, 8, "swara", "swara_ri", "ṛ", "ऋ", 2, 17, {"corner": "SE"}),

    (7, 8): SBCCellSemantic(7, 8, "akshara", "akshara_tta", "ṭa", "ट", 2, 26, {}),
    (6, 8): SBCCellSemantic(6, 8, "akshara", "akshara_ttha", "ṭha", "ठ", 2, 35, {}),
    (5, 8): SBCCellSemantic(5, 8, "akshara", "akshara_dda", "ḍa", "ड", 2, 44, {}),
    (4, 8): SBCCellSemantic(4, 8, "akshara", "akshara_ddha", "ḍha", "ढ", 2, 53, {}),
    (3, 8): SBCCellSemantic(3, 8, "akshara", "akshara_nna", "ṇa", "ण", 2, 62, {}),
    (2, 8): SBCCellSemantic(2, 8, "swara", "swara_rii", "ṝ", "ॠ", 2, 71, {"corner": "SW"}),

    (2, 7): SBCCellSemantic(2, 7, "akshara", "akshara_ta", "ta", "त", 2, 70, {}),
    (2, 6): SBCCellSemantic(2, 6, "akshara", "akshara_tha", "tha", "थ", 2, 69, {}),
    (2, 5): SBCCellSemantic(2, 5, "akshara", "akshara_da", "da", "द", 2, 68, {}),
    (2, 4): SBCCellSemantic(2, 4, "akshara", "akshara_dha", "dha", "ध", 2, 67, {}),
    (2, 3): SBCCellSemantic(2, 3, "akshara", "akshara_na", "na", "न", 2, 66, {}),

    # ── Ring 3 (5x5 Border): 4 Swaras (Corners) + 12 Rashis (3 per side) ────
    (3, 3): SBCCellSemantic(3, 3, "swara", "swara_lri", "ऌ", "ऌ", 3, 57, {"corner": "NW"}),
    (4, 3): SBCCellSemantic(4, 3, "rashi", "rashi_makara", "Makara", "मकर", 3, 48, {"rashi_code": "capricorn", "symbol": "♑"}),
    (5, 3): SBCCellSemantic(5, 3, "rashi", "rashi_kumbha", "Kumbha", "कुम्भ", 3, 39, {"rashi_code": "aquarius", "symbol": "♒"}),
    (6, 3): SBCCellSemantic(6, 3, "rashi", "rashi_meena", "Meena", "मीन", 3, 30, {"rashi_code": "pisces", "symbol": "♓"}),
    (7, 3): SBCCellSemantic(7, 3, "swara", "swara_lrii", "ॡ", "ॡ", 3, 21, {"corner": "NE"}),

    (7, 4): SBCCellSemantic(7, 4, "rashi", "rashi_mesha", "Mesha", "मेष", 3, 22, {"rashi_code": "aries", "symbol": "♈"}),
    (7, 5): SBCCellSemantic(7, 5, "rashi", "rashi_vrishabha", "Vrishabha", "वृषभ", 3, 23, {"rashi_code": "taurus", "symbol": "♉"}),
    (7, 6): SBCCellSemantic(7, 6, "rashi", "rashi_mithuna", "Mithuna", "मिथुन", 3, 24, {"rashi_code": "gemini", "symbol": "♊"}),
    (7, 7): SBCCellSemantic(7, 7, "swara", "swara_e", "e", "ए", 3, 25, {"corner": "SE"}),

    (6, 7): SBCCellSemantic(6, 7, "rashi", "rashi_karka", "Karka", "कर्क", 3, 34, {"rashi_code": "cancer", "symbol": "♋"}),
    (5, 7): SBCCellSemantic(5, 7, "rashi", "rashi_simha", "Simha", "सिंह", 3, 43, {"rashi_code": "leo", "symbol": "♌"}),
    (4, 7): SBCCellSemantic(4, 7, "rashi", "rashi_kanya", "Kanya", "कन्या", 3, 52, {"rashi_code": "virgo", "symbol": "♍"}),
    (3, 7): SBCCellSemantic(3, 7, "swara", "swara_ai", "ai", "ऐ", 3, 61, {"corner": "SW"}),

    (3, 6): SBCCellSemantic(3, 6, "rashi", "rashi_tula", "Tula", "तुला", 3, 60, {"rashi_code": "libra", "symbol": "♎"}),
    (3, 5): SBCCellSemantic(3, 5, "rashi", "rashi_vrishchika", "Vrishchika", "वृश्चिक", 3, 59, {"rashi_code": "scorpio", "symbol": "♏"}),
    (3, 4): SBCCellSemantic(3, 4, "rashi", "rashi_dhanu", "Dhanu", "धनु", 3, 58, {"rashi_code": "sagittarius", "symbol": "♐"}),

    # ── Ring 4 & Center: 4 Swaras (Corners) + 5 Tithis (with 7 Vara Overlay) ──
    (4, 4): SBCCellSemantic(4, 4, "swara", "swara_o", "o", "ओ", 4, 49, {"corner": "NW"}),
    (5, 4): SBCCellSemantic(5, 4, "tithi", "tithi_nanda", "Nanda", "नन्दा", 4, 40, {"tithi_group": "nanda", "tithis": "1, 6, 11", "vara_overlay": ["Sun", "Mars"], "vara_hi": "सूर्य / मंगल"}),
    (6, 4): SBCCellSemantic(6, 4, "swara", "swara_au", "au", "औ", 4, 31, {"corner": "NE"}),

    (6, 5): SBCCellSemantic(6, 5, "tithi", "tithi_bhadra", "Bhadra", "भद्रा", 4, 32, {"tithi_group": "bhadra", "tithis": "2, 7, 12", "vara_overlay": ["Moon", "Mercury"], "vara_hi": "चन्द्र / बुध"}),
    (6, 6): SBCCellSemantic(6, 6, "swara", "swara_am", "aṃ", "अं", 4, 33, {"corner": "SE"}),

    (5, 6): SBCCellSemantic(5, 6, "tithi", "tithi_jaya", "Jaya", "जया", 4, 42, {"tithi_group": "jaya", "tithis": "3, 8, 13", "vara_overlay": ["Jupiter"], "vara_hi": "गुरु"}),
    (4, 6): SBCCellSemantic(4, 6, "swara", "swara_ah", "aḥ", "अः", 4, 51, {"corner": "SW"}),

    (4, 5): SBCCellSemantic(4, 5, "tithi", "tithi_rikta", "Rikta", "रिक्ता", 4, 50, {"tithi_group": "rikta", "tithis": "4, 9, 14", "vara_overlay": ["Saturn"], "vara_hi": "शनि"}),

    # ── Ring 5 (Center Core 1x1): Purna Tithi / Janma Focal Point ───────────
    (5, 5): SBCCellSemantic(5, 5, "tithi", "tithi_purna", "Purna / Center", "पूर्णा / केन्द्र", 5, 41, {"tithi_group": "purna", "tithis": "5, 10, 15/30", "vara_overlay": ["Venus"], "vara_hi": "शुक्र", "is_center": True}),
}

assert len(SBC_81_CANONICAL) == 81, f"Expected 81 cells, got {len(SBC_81_CANONICAL)}"
# Verify canonical formula: 28 Nakshatra + 12 Rashi + 16 Swara + 20 Akshara + 5 Tithi = 81
_cats = [c.category for c in SBC_81_CANONICAL.values()]
assert _cats.count("nakshatra") == 28, f"Expected 28 nakshatras, got {_cats.count('nakshatra')}"
assert _cats.count("rashi") == 12, f"Expected 12 rashis, got {_cats.count('rashi')}"
assert _cats.count("swara") == 16, f"Expected 16 swaras, got {_cats.count('swara')}"
assert _cats.count("akshara") == 20, f"Expected 20 aksharas, got {_cats.count('akshara')}"
assert _cats.count("tithi") == 5, f"Expected 5 tithis, got {_cats.count('tithi')}"

# Backward compatibility map: cell_num -> SBCCellSemantic
SBC_81_CELLS: dict[int, SBCCellSemantic] = {
    cell.cell_num: cell for cell in SBC_81_CANONICAL.values()
}


