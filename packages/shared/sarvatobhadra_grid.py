"""
AstroOS — Sarvatobhadra Chakra (SBC) 28-Nakshatra Border Grid

**Sourcing.** The user provided an architecture document describing SBC's
general shape, which was NOT trusted as-is: it gave only 2 illustrative
example grid entries (framed explicitly as "when you build it" schema
examples, not verified classical data), and one of those two examples
directly contradicts an independent source below (it claimed Krittika's
"straight" target is Abhijit; Saravali states it is Shravana — see
verification below). That document's border-nakshatra grouping also
didn't match a second, independent web source. Given two disagreeing,
unverified sources, neither was used for the actual grid.

Instead this grid is derived from **Saravali** (https://saravali.github.io),
an open-source Vedic astrology calculation project, specifically:
  - https://saravali.github.io/astrology/sbc_basics.html — states the grid
    is a 9x9 (81-cell) square, the 28 nakshatras (incl. Abhijit) occupy the
    perimeter cells excluding the 4 corners, counting is clockwise, and
    gives the 4 corner boundary points as classical anchors:
      Right Upper: Bharani-Krittika boundary (26:40 Aries)
      Right Lower: Ashlesha-Magha boundary (0:00 Leo)
      Left Lower:  Vishakha-Anuradha boundary (3:20 Scorpio)
      Left Upper:  Shravana-Dhanishtha boundary (23:20 Capricorn)
    plus the single fact "Aswini is the 6th Nakshatra in the upper row."
  - https://saravali.github.io/astrology/sbc_vedhas.html — defines Forward
    (diagonal, clockwise direction, for a planet in direct motion),
    Opposite (straight across, for a stationary planet), and Backward
    (diagonal, counter-clockwise, for a retrograde planet) Vedha, with 4
    fully worked examples: Ashwini, Swati, Purva Ashadha, and Krittika.

**Derivation.** The 4 corner facts + "Ashwini is 6th in the upper row"
uniquely determine the full 28-cell border layout (worked out by hand
below, then encoded as SBC_BORDER). The Vedha geometry (straight-across
for Opposite; 45-degree diagonal, continued until the border is hit
again, in the stated rotational sense for Forward/Backward) was then
applied to that layout and independently checked against ALL FOUR of
Saravali's worked examples — all 4 nakshatras x all 3 Vedha types (12
checks total) match exactly. See test_sarvatobhadra_grid.py for these
checks as executable assertions. This is the same "verify against known
examples before trusting a derivation" standard used elsewhere in this
codebase, not a from-scratch invention.

**Grid layout** (9x9, columns 1-9 left-to-right, rows 1-9 top-to-bottom;
corners at (1,1)/(9,1)/(1,9)/(9,9) are unused by the nakshatra border):

  Upper row (row=1, cols 2-8, left-to-right):
    Dhanishtha, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada,
    Revati, Ashwini, Bharani
  Right column (col=9, rows 2-8, top-to-bottom):
    Krittika, Rohini, Mrigashira, Ardra, Punarvasu, Pushya, Ashlesha
  Bottom row (row=9, cols 8-2, right-to-left):
    Magha, Purva Phalguni, Uttara Phalguni, Hasta, Chitra, Swati, Vishakha
  Left column (col=1, rows 8-2, bottom-to-top):
    Anuradha, Jyeshtha, Mula, Purva Ashadha, Uttara Ashadha, Abhijit,
    Shravana

Abhijit sits between Uttara Ashadha and Shravana on the left column, per
Saravali's basics page ("Abhijit is the 28th star and is located between
Uttarashadha and Sravana") — consistent with both sources.

**Scope note.** SBC is a 28-nakshatra system; the rest of this codebase
(Dasha, KP Sub Lord, Karakatva, etc.) deliberately stays on the standard
27-nakshatra system, which is correct for those purposes. Abhijit
detection is scoped only to this module's use (see
services/nakshatra_vedha_calculator.py) and does not change any other
nakshatra computation in the app.
"""

from __future__ import annotations

from packages.shared.constants import DEGREES_PER_NAKSHATRA
from packages.shared.enums import Nakshatra

# Nakshatra tokens match packages.shared.enums.Nakshatra exactly (lowercase
# snake_case), plus "abhijit" which only exists for SBC purposes.

_UPPER_ROW = [
    "dhanishtha", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada",
    "revati", "ashwini", "bharani",
]
_RIGHT_COLUMN = [
    "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",
]
_BOTTOM_ROW = [
    "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha",
]
_LEFT_COLUMN = [
    "anuradha", "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "abhijit", "shravana",
]

# (col, row), 1-indexed, on the 9x9 grid.
SBC_BORDER: dict[str, tuple[int, int]] = {}
for _i, _name in enumerate(_UPPER_ROW):
    SBC_BORDER[_name] = (2 + _i, 1)
for _i, _name in enumerate(_RIGHT_COLUMN):
    SBC_BORDER[_name] = (9, 2 + _i)
for _i, _name in enumerate(_BOTTOM_ROW):
    SBC_BORDER[_name] = (8 - _i, 9)
for _i, _name in enumerate(_LEFT_COLUMN):
    SBC_BORDER[_name] = (1, 8 - _i)

_GRID_MIN, _GRID_MAX = 1, 9


def _on_border(col: int, row: int) -> bool:
    on_edge = col in (_GRID_MIN, _GRID_MAX) or row in (_GRID_MIN, _GRID_MAX)
    is_corner = col in (_GRID_MIN, _GRID_MAX) and row in (_GRID_MIN, _GRID_MAX)
    return on_edge and not is_corner


_COORD_TO_NAME: dict[tuple[int, int], str] = {v: k for k, v in SBC_BORDER.items()}


def opposite_vedha_target(nakshatra: str) -> str:
    """Straight-line target (used for a stationary planet)."""
    col, row = SBC_BORDER[nakshatra]
    if col in (_GRID_MIN, _GRID_MAX):
        # Left/right column cell -> straight across to the same row, other column.
        target_col = _GRID_MAX if col == _GRID_MIN else _GRID_MIN
        target = (target_col, row)
    else:
        # Upper/lower row cell -> straight across to the same column, other row.
        target_row = _GRID_MAX if row == _GRID_MIN else _GRID_MIN
        target = (col, target_row)
    return _COORD_TO_NAME[target]


def _diagonal_target(nakshatra: str, *, clockwise: bool) -> str:
    """
    Walk diagonally from `nakshatra`'s border cell until hitting the
    border again (excluding the starting cell), in the rotational sense
    given by `clockwise`. The four border sides are traversed
    upper->right->bottom->left in the clockwise direction (matching how
    the nakshatras themselves are laid out), so "clockwise diagonal" from
    a given side always steps toward the next side in that sequence, and
    counter-clockwise steps toward the previous one.
    """
    col, row = SBC_BORDER[nakshatra]

    if row == _GRID_MIN:  # upper row
        dc, dr = (1, 1) if clockwise else (-1, 1)
    elif col == _GRID_MAX:  # right column
        dc, dr = (-1, 1) if clockwise else (-1, -1)
    elif row == _GRID_MAX:  # bottom row
        dc, dr = (-1, -1) if clockwise else (1, -1)
    else:  # left column
        dc, dr = (1, -1) if clockwise else (1, 1)

    c, r = col, row
    while True:
        c, r = c + dc, r + dr
        if not (_GRID_MIN <= c <= _GRID_MAX and _GRID_MIN <= r <= _GRID_MAX):
            raise ValueError(f"Diagonal from {nakshatra} walked off the grid before hitting a border cell")
        if _on_border(c, r):
            return _COORD_TO_NAME[(c, r)]


def forward_vedha_target(nakshatra: str) -> str:
    """Clockwise-diagonal target (used for a planet in direct motion)."""
    return _diagonal_target(nakshatra, clockwise=True)


def backward_vedha_target(nakshatra: str) -> str:
    """Counter-clockwise-diagonal target (used for a retrograde planet)."""
    return _diagonal_target(nakshatra, clockwise=False)


# ── Abhijit-aware (28-nakshatra) longitude classification ───────────────────
#
# Scoped ONLY to SBC use — every other nakshatra computation in this app
# (Dasha, KP Sub Lord, Karakatva, etc.) correctly stays on the standard
# 27-nakshatra system and is untouched by this.
#
# Saravali's "Basics" page notes two classical opinions on Abhijit's
# extent: (1) omit it entirely, or (2) carve it out of the last part of
# Uttara Ashadha and the first part of Shravana. SBC requires Abhijit to
# be a real, occupiable grid cell (opinion 2), so that's what's used here
# — specifically "the last quarter of Uttarashadha and the first 15th
# part of Sravana are regarded as belonging to Abhijit," per Saravali.
_STANDARD_27 = [n.value for n in Nakshatra]
_UTTARA_ASHADHA_INDEX = _STANDARD_27.index("uttara_ashadha")
_SHRAVANA_INDEX = _STANDARD_27.index("shravana")
_UTTARA_ASHADHA_END = (_UTTARA_ASHADHA_INDEX + 1) * DEGREES_PER_NAKSHATRA
_SHRAVANA_START = _SHRAVANA_INDEX * DEGREES_PER_NAKSHATRA
_ABHIJIT_START = _UTTARA_ASHADHA_END - (DEGREES_PER_NAKSHATRA / 4)
_ABHIJIT_END = _SHRAVANA_START + (DEGREES_PER_NAKSHATRA / 15)


def longitude_to_sbc_nakshatra(sidereal_longitude: float) -> str:
    """28-system (Abhijit-aware) nakshatra for a sidereal longitude — SBC
    use only, see module note above."""
    lon = sidereal_longitude % 360.0
    if _ABHIJIT_START <= lon < _ABHIJIT_END:
        return "abhijit"
    index = int(lon / DEGREES_PER_NAKSHATRA)
    return _STANDARD_27[index % 27]
