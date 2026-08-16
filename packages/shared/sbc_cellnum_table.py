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
