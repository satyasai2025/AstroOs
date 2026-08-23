"""
AstroOS — Divisional Chart Engine (Task 5)

Computes all 22 Varga charts (D2–D144) using Parashara rules.

Varga rules implemented
-----------------------
D2  (Hora)              — 2 parts; Sun/Moon hora alternation by odd/even sign
D3  (Drekkana)          — 3 parts; 1st/5th/9th trines from natal sign
D4  (Chaturthamsha)     — 4 parts; successive kendras from natal sign
D5  (Panchamsha)        — 5 non-sequential parts; Mars/Sat/Jup/Merc/Ven target signs
D6  (Shashthamsha)      — 6 parts; odd sign from Aries, even sign from Libra
D7  (Saptamsha)         — 7 parts; odd sign starts from same sign, even from 7th
D8  (Ashtamsha)         — 8 parts; Movable→Aries, Fixed→Sagittarius, Dual→Leo
D9  (Navamsha)          — 9 parts; standard zodiacal formula (sign × 9 + part)
D10 (Dasamsha)          — 10 parts; odd sign from same, even sign from 9th
D11 (Rudramsha)         — 11 parts; start sign = (12 − sign_index) mod 12
D12 (Dvadashamsha)      — 12 parts; starts from natal sign
D16 (Shodashamsha)      — 16 parts; Cardinal→Aries, Fixed→Leo, Mutable→Sagittarius
D20 (Vimshamsha)        — 20 parts; Movable→Aries, Fixed→Sagittarius, Dual→Leo
D24 (Chaturvimshamsha)  — 24 parts; odd sign→Leo, even sign→Cancer
D27 (Bhamsha)           — 27 parts; Fire→Aries, Earth→Cancer, Air→Libra, Water→Cap
D30 (Trimshamsha)       — 30 non-equal parts; Parashara special ruleset
D40 (Khavedamsha)       — 40 parts; odd→Aries, even→Libra
D45 (Akshavedamsha)     — 45 parts; Movable→Aries, Fixed→Leo, Dual→Sagittarius
D60 (Shashtiamsha)      — 60 parts; odd→Aries, even→Libra

Composite ("varga of varga") charts — no standalone degree formula exists;
each is one varga applied to another's output. Composition order verified
empirically against a Classical Vedic reference export, not assumed:
D81  (Nava-Navamsha)    — D9 of D9
D108 (Ashtottaramsha)   — D12 of D9   (NOT D9 of D12 — that matches 0/15)
D144 (Dwadasamsa²)      — D12 of D12

All degrees within a varga sign are normalised to [0, 30).
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from apps.api.domain.divisional import VargaAscendant, VargaChart, VargaPosition
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from packages.shared.degrees import normalize_degrees
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset

# ── Sign constants ────────────────────────────────────────────────────────────

_RASHI_LIST = [r.value for r in Rashi]

# All supported vargas (divisor → label)
SUPPORTED_VARGAS: dict[str, int] = {
    "D2": 2, "D3": 3, "D4": 4, "D5": 5, "D6": 6, "D7": 7, "D8": 8, "D9": 9,
    "D10": 10, "D11": 11, "D12": 12, "D16": 16, "D20": 20, "D24": 24,
    "D27": 27, "D30": 30, "D40": 40, "D45": 45, "D60": 60,
    "D81": 81, "D108": 108, "D144": 144,
}


# ── Sign-type helpers ─────────────────────────────────────────────────────────

def _is_odd_sign(sign_index: int) -> bool:
    """
    Odd sign (vishama rashi) in Vedic numbering:
    Aries(1), Gemini(3), Leo(5), Libra(7), Sagittarius(9), Aquarius(11).
    In 0-indexed arrays these are indices 0, 2, 4, 6, 8, 10 → sign_index % 2 == 0.
    """
    return sign_index % 2 == 0


# Movable (chara) signs: Aries(0), Cancer(3), Libra(6), Capricorn(9)
_MOVABLE = frozenset({0, 3, 6, 9})
# Fixed (sthira) signs: Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
_FIXED = frozenset({1, 4, 7, 10})
# Dual/Mutable (dvisvabhava) signs: Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
_DUAL = frozenset({2, 5, 8, 11})

# Fire: Aries(0), Leo(4), Sagittarius(8)
_FIRE = frozenset({0, 4, 8})
# Earth: Taurus(1), Virgo(5), Capricorn(9)
_EARTH = frozenset({1, 5, 9})
# Air: Gemini(2), Libra(6), Aquarius(10)
_AIR = frozenset({2, 6, 10})
# Water: Cancer(3), Scorpio(7), Pisces(11)
_WATER = frozenset({3, 7, 11})


# ── Individual varga calculators ──────────────────────────────────────────────

def _d2_hora(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D2 — Hora chart.
    Odd sign: first 15° → Leo (Sun hora), second 15° → Cancer (Moon hora).
    Even sign: first 15° → Cancer, second 15° → Leo.
    Degree within varga sign is proportionally scaled to [0, 30).
    """
    part = 0 if deg < 15.0 else 1
    part_deg = (deg % 15.0) * 2.0  # scale 0-15 → 0-30

    if _is_odd_sign(sign_index):
        vsign = "leo" if part == 0 else "cancer"
    else:
        vsign = "cancer" if part == 0 else "leo"

    return vsign, part_deg


def _d3_drekkana(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D3 — Drekkana.
    Three 10° parts. Each part falls into the 1st, 5th, or 9th sign from natal.
    Offsets: [0, 4, 8] (i.e., same, +4, +8 signs).
    """
    part = min(int(deg / 10.0), 2)
    offsets = (0, 4, 8)
    vsign_idx = (sign_index + offsets[part]) % 12
    vdeg = (deg % 10.0) * 3.0  # scale 10° → 30°
    return _RASHI_LIST[vsign_idx], vdeg


def _d4_chaturthamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D4 — Chaturthamsha.
    Four 7.5° parts. Each successive part falls in the next kendra
    (same, 4th, 7th, 10th → offsets 0, 3, 6, 9).
    """
    part = min(int(deg / 7.5), 3)
    vsign_idx = (sign_index + part * 3) % 12
    vdeg = (deg % 7.5) * 4.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d7_saptamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D7 — Saptamsha.
    Seven equal parts (30/7° each).
    Odd sign: starts from same sign.
    Even sign: starts from 7th sign (offset 6).
    """
    part_size = 30.0 / 7.0
    part = min(int(deg / part_size), 6)
    start = sign_index if _is_odd_sign(sign_index) else (sign_index + 6) % 12
    vsign_idx = (start + part) % 12
    vdeg = (deg % part_size) * 7.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d9_navamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D9 — Navamsha (the most important divisional chart).
    Nine equal parts (30/9° each).
    Formula: varga_sign = (sign_index × 9 + part) mod 12.
    This correctly places:
      - Aries → starts at Aries
      - Taurus → starts at Capricorn
      - Gemini → starts at Libra
      - Cancer → starts at Cancer
    """
    part_size = 30.0 / 9.0
    part = min(int(deg / part_size), 8)
    vsign_idx = (sign_index * 9 + part) % 12
    vdeg = (deg % part_size) * 9.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d10_dasamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D10 — Dasamsha.
    Ten equal 3° parts.
    Odd sign: starts from same sign.
    Even sign: starts from the 9th sign (offset 8).
    """
    part = min(int(deg / 3.0), 9)
    start = sign_index if _is_odd_sign(sign_index) else (sign_index + 8) % 12
    vsign_idx = (start + part) % 12
    vdeg = (deg % 3.0) * 10.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d12_dvadashamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D12 — Dvadashamsha.
    Twelve equal 2.5° parts. Each sign's first part starts from that same sign;
    subsequent parts advance through the zodiac.
    Formula: varga_sign = (sign_index + part) mod 12.
    """
    part = min(int(deg / 2.5), 11)
    vsign_idx = (sign_index + part) % 12
    vdeg = (deg % 2.5) * 12.0
    return _RASHI_LIST[vsign_idx], vdeg


# D16 starting signs: Cardinal → Aries(0), Fixed → Leo(4), Mutable → Sagittarius(8)
_D16_START: dict[int, int] = {
    0: 0, 3: 0, 6: 0, 9: 0,   # Movable (Cardinal) → Aries
    1: 4, 4: 4, 7: 4, 10: 4,  # Fixed → Leo
    2: 8, 5: 8, 8: 8, 11: 8,  # Mutable (Dual) → Sagittarius
}


def _d16_shodashamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D16 — Shodashamsha.
    Sixteen equal 1.875° parts.
    Starting sign by quality: Cardinal→Aries, Fixed→Leo, Mutable→Sagittarius.
    """
    part_size = 30.0 / 16.0
    part = min(int(deg / part_size), 15)
    vsign_idx = (_D16_START[sign_index] + part) % 12
    vdeg = (deg % part_size) * 16.0
    return _RASHI_LIST[vsign_idx], vdeg


# D20 starting signs: Movable→Aries(0), Fixed→Sagittarius(8), Dual→Leo(4)
_D20_START: dict[int, int] = {
    0: 0, 3: 0, 6: 0, 9: 0,   # Movable → Aries
    1: 8, 4: 8, 7: 8, 10: 8,  # Fixed → Sagittarius
    2: 4, 5: 4, 8: 4, 11: 4,  # Dual → Leo
}


def _d20_vimshamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D20 — Vimshamsha.
    Twenty equal 1.5° parts.
    Starting sign by quality: Movable→Aries, Fixed→Sagittarius, Dual→Leo.
    """
    part_size = 1.5
    part = min(int(deg / part_size), 19)
    vsign_idx = (_D20_START[sign_index] + part) % 12
    vdeg = (deg % part_size) * 20.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d24_chaturvimshamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D24 — Chaturvimshamsha (Siddhamsha).
    Twenty-four equal 1.25° parts.
    Odd sign: starts from Leo (4).
    Even sign: starts from Cancer (3).
    """
    part_size = 30.0 / 24.0
    part = min(int(deg / part_size), 23)
    start = 4 if _is_odd_sign(sign_index) else 3
    vsign_idx = (start + part) % 12
    vdeg = (deg % part_size) * 24.0
    return _RASHI_LIST[vsign_idx], vdeg


# D27 starting signs: Fire→Aries(0), Earth→Cancer(3), Air→Libra(6), Water→Capricorn(9)
_D27_START: dict[int, int] = {
    0: 0, 4: 0, 8: 0,   # Fire → Aries
    1: 3, 5: 3, 9: 3,   # Earth → Cancer
    2: 6, 6: 6, 10: 6,  # Air → Libra
    3: 9, 7: 9, 11: 9,  # Water → Capricorn
}


def _d27_bhamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D27 — Bhamsha (Nakshatramsha).
    Twenty-seven equal parts (30/27° each).
    Start sign by element: Fire→Aries, Earth→Cancer, Air→Libra, Water→Capricorn.
    """
    part_size = 30.0 / 27.0
    part = min(int(deg / part_size), 26)
    vsign_idx = (_D27_START[sign_index] + part) % 12
    vdeg = (deg % part_size) * 27.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d30_trimshamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D30 — Trimshamsha (Parashara non-uniform partition).

    Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius):
        0– 5° → Aries   (Mars)
        5–10° → Aquarius  (Saturn)
       10–18° → Sagittarius (Jupiter)
       18–25° → Gemini   (Mercury)
       25–30° → Libra    (Venus)

    Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces):
        0– 5° → Taurus   (Venus)
        5–12° → Virgo    (Mercury)
       12–20° → Pisces   (Jupiter)
       20–25° → Capricorn (Saturn)
       25–30° → Scorpio  (Mars)

    Sun and Moon have no Trimshamsha — they receive the D1 sign itself.
    """
    if _is_odd_sign(sign_index):
        if deg < 5.0:
            vsign, vdeg = "aries", deg * 6.0
        elif deg < 10.0:
            vsign, vdeg = "aquarius", (deg - 5.0) * 6.0
        elif deg < 18.0:
            vsign, vdeg = "sagittarius", (deg - 10.0) * (30.0 / 8.0)
        elif deg < 25.0:
            vsign, vdeg = "gemini", (deg - 18.0) * (30.0 / 7.0)
        else:
            vsign, vdeg = "libra", (deg - 25.0) * 6.0
    else:
        if deg < 5.0:
            vsign, vdeg = "taurus", deg * 6.0
        elif deg < 12.0:
            vsign, vdeg = "virgo", (deg - 5.0) * (30.0 / 7.0)
        elif deg < 20.0:
            vsign, vdeg = "pisces", (deg - 12.0) * (30.0 / 8.0)
        elif deg < 25.0:
            vsign, vdeg = "capricorn", (deg - 20.0) * 6.0
        else:
            vsign, vdeg = "scorpio", (deg - 25.0) * 6.0

    return vsign, min(vdeg, 29.9999)


def _d40_khavedamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D40 — Khavedamsha.
    Forty equal 0.75° parts.
    Odd sign: starts from Aries (0).
    Even sign: starts from Libra (6).
    """
    part_size = 0.75
    part = min(int(deg / part_size), 39)
    start = 0 if _is_odd_sign(sign_index) else 6
    vsign_idx = (start + part) % 12
    vdeg = (deg % part_size) * 40.0
    return _RASHI_LIST[vsign_idx], vdeg


# D45 starting signs: Movable→Aries(0), Fixed→Leo(4), Dual→Sagittarius(8)
_D45_START: dict[int, int] = {
    0: 0, 3: 0, 6: 0, 9: 0,   # Movable → Aries
    1: 4, 4: 4, 7: 4, 10: 4,  # Fixed → Leo
    2: 8, 5: 8, 8: 8, 11: 8,  # Dual → Sagittarius
}


def _d45_akshavedamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D45 — Akshavedamsha.
    Forty-five equal parts (30/45° = 0.6̄° each).
    Starting sign by quality: Movable→Aries, Fixed→Leo, Dual→Sagittarius.
    """
    part_size = 30.0 / 45.0
    part = min(int(deg / part_size), 44)
    vsign_idx = (_D45_START[sign_index] + part) % 12
    vdeg = (deg % part_size) * 45.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d60_shashtiamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D60 — Shashtiamsha (the most detailed varga).
    Sixty equal 0.5° parts, counted FORWARD FROM THE PLANET'S OWN SIGN
    (not from a fixed Aries/Libra odd-even split — that was this
    function's previous, incorrect implementation). This is the
    "Traditional Parasara Shashtyamsha" method — cross-verified against
    PyJHora's jhora.horoscope.chart.charts.shashtyamsa_chart(
    chart_method=1), which is both PyJHora's own default and explicitly
    labeled "Traditional Parasara shashtyamsa (from sign)" in its
    docstring. Confirmed exact for the 1995-01-01 12:00 UTC, New Delhi
    reference chart (Sun -> Virgo, Moon -> Libra).
    """
    part_size = 0.5
    part = min(int(deg / part_size), 59)
    vsign_idx = (sign_index + part) % 12
    vdeg = (deg % part_size) * 60.0
    return _RASHI_LIST[vsign_idx], vdeg


# D5 target signs, by ruling planet in Parashari order (Mars, Saturn, Jupiter,
# Mercury, Venus) — NOT a simple sequential/offset scheme like the other
# vargas above. Corroborated across two independent sources including a
# worked example (Sun 2nd part of Aries, ruled by Saturn -> D5 sign Aquarius).
# No classical rationale for this particular planet order is preserved in the
# texts that describe it; it is simply the attested sequence.
_D5_ODD_SIGNS = (0, 10, 8, 2, 6)     # Aries, Aquarius, Sagittarius, Gemini, Libra
                                      # (Mars, Saturn, Jupiter, Mercury, Venus — own sign)
_D5_EVEN_SIGNS = (1, 5, 11, 9, 7)    # Taurus, Virgo, Pisces, Capricorn, Scorpio
                                      # (Venus, Mercury, Jupiter, Saturn, Mars — reverse
                                      # planet order, EACH PLANET'S OTHER SIGN, not its
                                      # sign used above.) Corrected against a Classical Vedic
                                      # reference chart (2026-08-15, Pune) — the initial
                                      # "reverse of the odd table" guess did not match;
                                      # this table was reverse-engineered from ~15
                                      # independent even-sign data points in that export
                                      # and matches all of them exactly.


def _d5_panchamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D5 — Panchamsha.
    Five equal 6° parts, mapped to explicit target signs (not a sequential
    offset). Odd sign -> Aries, Aquarius, Sagittarius, Gemini, Libra (Mars,
    Saturn, Jupiter, Mercury, Venus, in their primary sign). Even sign ->
    Taurus, Virgo, Pisces, Capricorn, Scorpio — the same five planets in
    reverse order (Venus, Mercury, Jupiter, Saturn, Mars), each in its
    *other* sign rather than the one used for the odd table.
    """
    part_size = 6.0
    part = min(int(deg / part_size), 4)
    targets = _D5_ODD_SIGNS if _is_odd_sign(sign_index) else _D5_EVEN_SIGNS
    vdeg = (deg % part_size) * 5.0
    return _RASHI_LIST[targets[part]], vdeg


def _d6_shashthamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D6 — Shashthamsha.
    Six equal 5° parts, sequential from a starting sign.
    Odd sign: starts from Aries (0). Even sign: starts from Libra (6).
    """
    part_size = 5.0
    part = min(int(deg / part_size), 5)
    start = 0 if _is_odd_sign(sign_index) else 6
    vsign_idx = (start + part) % 12
    vdeg = (deg % part_size) * 6.0
    return _RASHI_LIST[vsign_idx], vdeg


# D8 starting signs by quality — identical scheme to D20's _D20_START:
# Movable -> Aries(0), Fixed -> Sagittarius(8), Dual -> Leo(4).
_D8_START: dict[int, int] = {
    0: 0, 3: 0, 6: 0, 9: 0,   # Movable → Aries
    1: 8, 4: 8, 7: 8, 10: 8,  # Fixed → Sagittarius
    2: 4, 5: 4, 8: 4, 11: 4,  # Dual → Leo
}


def _d8_ashtamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D8 — Ashtamsha.
    Eight equal 3°45' parts.
    Starting sign by quality: Movable→Aries, Fixed→Sagittarius, Dual→Leo.
    """
    part_size = 30.0 / 8.0
    part = min(int(deg / part_size), 7)
    vsign_idx = (_D8_START[sign_index] + part) % 12
    vdeg = (deg % part_size) * 8.0
    return _RASHI_LIST[vsign_idx], vdeg


def _d11_rudramsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D11 — Rudramsha (Ekadashamsha).
    Eleven equal parts (30/11° ≈ 2°43'38" each).

    Starting sign per P.V.R. Narasimha Rao's method (Vedic Astrology: An
    Integrated Approach): count the rasi's position from Aries zodiacally
    (1-indexed), then count that same number of positions from Aries
    ANTI-zodiacally — the sign reached is where the 11 parts start.

    Equivalently: start_sign_index = (12 - sign_index) % 12.

    Verified against the source's own worked examples: Gemini (index 2) ->
    start = Aquarius (index 10); the 5th part of Gemini (Mercury at 11°)
    lands back in Gemini — (10 + 4) % 12 == 2. ✓
    """
    part_size = 30.0 / 11.0
    part = min(int(deg / part_size), 10)
    start = (12 - sign_index) % 12
    vsign_idx = (start + part) % 12
    vdeg = (deg % part_size) * 11.0
    return _RASHI_LIST[vsign_idx], vdeg


# ── Composite ("varga of varga") charts ───────────────────────────────────────
#
# D81/D108/D144 are not independent degree-mapping schemes — each is one varga
# applied to the *output* of another, which is why no standalone classical
# formula for them exists. The exact composition order was determined
# empirically from a Classical Vedic reference export (2026-08-15, Pune) rather than
# guessed: each hypothesis below was tested against 15 independent bodies and
# only kept when it reproduced Classical Vedic's own output.


def _d81_nava_navamsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D81 — Nava-Navamsha: the Navamsha of the Navamsha (9 × 9).

    Verified against the Classical Vedic reference export at full precision:
    15/15 signs and 15/15 degrees, every degree within the tolerance
    implied by the export's arcminute-rounded D1 input (+/-0.7 deg here,
    since a D1 rounding error is amplified 81x).
    """
    vsign, vdeg = _d9_navamsha(sign_index, deg)
    return _d9_navamsha(_RASHI_LIST.index(vsign), vdeg)


def _d108_ashtottaramsha(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D108 — Ashtottaramsha: the Dvadashamsha of the Navamsha (9 × 12).

    Order matters — D12-of-D9 reproduces Classical Vedic exactly (15/15 signs and
    15/15 degrees, all within the +/-0.9 deg tolerance implied by the
    export's arcminute-rounded D1 input) while the reverse composition,
    D9-of-D12, matches 0/15.
    """
    vsign, vdeg = _d9_navamsha(sign_index, deg)
    return _d12_dvadashamsha(_RASHI_LIST.index(vsign), vdeg)


def _d144_dwadasamsa_dwadasamsa(sign_index: int, deg: float) -> tuple[str, float]:
    """
    D144 — Dwadasamsa-Dwadasamsa: the Dvadashamsha of the Dvadashamsha (12 × 12).

    Verified 14/15 signs and 14/15 degrees against the Classical Vedic reference
    export. The single difference is confirmed to be a rounding artefact,
    not a formula disagreement: the export gives Gemini 29°31' where this
    returns Cancer 0°00' — 0.47° apart, straddling a sign boundary, well
    inside the ±1.2° tolerance implied by the export's arcminute-rounded
    D1 input (a D1 rounding error is amplified 144× here). Every other
    body's degree likewise lands within that tolerance.
    """
    vsign, vdeg = _d12_dvadashamsha(sign_index, deg)
    return _d12_dvadashamsha(_RASHI_LIST.index(vsign), vdeg)


# ── Dispatch table ────────────────────────────────────────────────────────────

_VARGA_CALCULATOR = {
    "D2":  _d2_hora,
    "D3":  _d3_drekkana,
    "D4":  _d4_chaturthamsha,
    "D5":  _d5_panchamsha,
    "D6":  _d6_shashthamsha,
    "D7":  _d7_saptamsha,
    "D8":  _d8_ashtamsha,
    "D9":  _d9_navamsha,
    "D10": _d10_dasamsha,
    "D11": _d11_rudramsha,
    "D12": _d12_dvadashamsha,
    "D16": _d16_shodashamsha,
    "D20": _d20_vimshamsha,
    "D24": _d24_chaturvimshamsha,
    "D27": _d27_bhamsha,
    "D30": _d30_trimshamsha,
    "D40": _d40_khavedamsha,
    "D45": _d45_akshavedamsha,
    "D60": _d60_shashtiamsha,
    "D81": _d81_nava_navamsha,
    "D108": _d108_ashtottaramsha,
    "D144": _d144_dwadasamsa_dwadasamsa,
}


# ── Low-level helpers ─────────────────────────────────────────────────────────

# ── Generic (non-classical) varga schemes ─────────────────────────────────────
#
# The 22 charts above each carry their own classically-attested starting-sign
# rule, and those rules do not follow from any single generic formula — D5 uses
# an explicit target table, D8 keys off sign quality, D11 counts anti-zodiacally,
# and so on. So an arbitrary "D-n" cannot be derived by extrapolating from them.
#
# What *is* well-defined for arbitrary n is the Parivritti (cyclical) scheme:
# cut the whole zodiac into equal 30/n° parts and hand them out to the signs in
# unbroken zodiacal order, continuing across sign boundaries rather than
# restarting each sign. Where a classical chart has its own rule, that rule
# wins — use the named code (D9, D11, …), which dispatches to the verified
# implementation. These generic schemes exist for exploring divisions that have
# no classical rule of their own.

MAX_CUSTOM_DIVISOR = 300


def _parivritti_cyclic(n: int):
    """
    Build a calculator for the Parivritti (cyclical) D-n scheme.

    The zodiac is divided into 12·n equal parts of 30/n° each, numbered
    continuously from 0° Aries; part k lands in sign k mod 12.
    """
    part_size = 30.0 / n

    def _calc(sign_index: int, deg: float) -> tuple[str, float]:
        # Reconstruct the absolute longitude so parts run continuously across
        # sign boundaries — the defining property of the cyclical scheme.
        lon = sign_index * 30.0 + deg
        part = int(lon / part_size)
        vdeg = (lon % part_size) * n
        return _RASHI_LIST[part % 12], vdeg

    return _calc


def _parivritti_from_sign(n: int):
    """
    Build a calculator for the "count from the natal sign" D-n scheme —
    the generalisation of D12's rule: part k of a sign falls k signs
    later, restarting from the natal sign in every sign.
    """
    part_size = 30.0 / n

    def _calc(sign_index: int, deg: float) -> tuple[str, float]:
        part = min(int(deg / part_size), n - 1)
        vdeg = (deg % part_size) * n
        return _RASHI_LIST[(sign_index + part) % 12], vdeg

    return _calc


_CUSTOM_SCHEMES = {
    "cyclic": _parivritti_cyclic,
    "from_sign": _parivritti_from_sign,
}

# "D9xD12" — apply D9, then D12 to its output. Same construction the
# classical composites D81/D108/D144 are built from, generalised.
_SUBDIVISIONAL_RE = re.compile(r"^(D\d+)X(D\d+)$")


def _compose(outer_code: str, inner_code: str):
    """
    Build a calculator that applies `outer_code` first, then `inner_code`
    to the resulting sign+degree.

    Naming follows the classical composites: D108 is "the Dvadashamsha of
    the Navamsha", i.e. D9 applied first and D12 second, written D9xD12.
    """
    first = _resolve_calculator(outer_code)
    second = _resolve_calculator(inner_code)

    def _calc(sign_index: int, deg: float) -> tuple[str, float]:
        vsign, vdeg = first(sign_index, deg)
        return second(_RASHI_LIST.index(vsign), vdeg)

    return _calc


def _resolve_calculator(varga: str):
    """
    Resolve a varga code to a calculator function.

    Accepts, in precedence order:
      1. A registered classical code ("D9", "D81", …) — always wins, so a
         chart with its own attested rule never falls through to a generic one.
      2. A composite "D<a>xD<b>" — each half resolved by this same function.
      3. A bare "D<n>" with no classical rule — Parivritti cyclical scheme.

    Raises ValueError with an actionable message for anything else.
    """
    code = varga.upper()

    if code in _VARGA_CALCULATOR:
        return _VARGA_CALCULATOR[code]

    composite = _SUBDIVISIONAL_RE.match(code)
    if composite:
        return _compose(composite.group(1), composite.group(2))

    if re.fullmatch(r"D\d+", code):
        n = int(code[1:])
        if n < 1 or n > MAX_CUSTOM_DIVISOR:
            raise ValueError(
                f"Custom divisor must be between 1 and {MAX_CUSTOM_DIVISOR}; got {n}."
            )
        return _parivritti_cyclic(n)

    raise ValueError(
        f"Unknown varga '{varga}'. Use a classical code "
        f"({', '.join(sorted(_VARGA_CALCULATOR))}), a custom 'Dn', "
        "or a sub-divisional 'DaxDb'."
    )


def varga_divisor(varga: str) -> int:
    """
    The effective divisor for any accepted varga code.

    Classical codes use their registered divisor; a custom "Dn" uses n; a
    sub-divisional "DaxDb" uses a·b (D9xD12 → 108, matching the classical
    D108 it generalises).
    """
    code = varga.upper()
    if code in SUPPORTED_VARGAS:
        return SUPPORTED_VARGAS[code]

    composite = _SUBDIVISIONAL_RE.match(code)
    if composite:
        return varga_divisor(composite.group(1)) * varga_divisor(composite.group(2))

    if re.fullmatch(r"D\d+", code):
        return int(code[1:])

    raise ValueError(f"Unknown varga '{varga}'.")


def compute_varga_sign(
    varga: str,
    sidereal_longitude: float,
    scheme: str = "cyclic",
) -> tuple[str, float]:
    """
    Public helper: compute the varga sign and degree for any planet or ascendant.

    Args:
        varga:              A classical code ("D2", "D9", … "D144"), a custom
                            "Dn", or a sub-divisional "DaxDb" (e.g. "D9xD12").
        sidereal_longitude: Sidereal longitude in [0, 360).
        scheme:             Only consulted for a custom "Dn" that has no
                            classical rule — "cyclic" (default, Parivritti) or
                            "from_sign". Ignored for classical and composite
                            codes, which have their own defined behaviour.

    Returns:
        (varga_rashi, varga_rashi_degree) — sign name + degree within sign [0, 30).

    Raises:
        ValueError: If the varga code or scheme is not recognised.
    """
    code = varga.upper()
    if (
        code not in _VARGA_CALCULATOR
        and re.fullmatch(r"D\d+", code)
        and scheme != "cyclic"
    ):
        if scheme not in _CUSTOM_SCHEMES:
            raise ValueError(
                f"Unknown scheme '{scheme}'. Choose from: {sorted(_CUSTOM_SCHEMES)}."
            )
        n = int(code[1:])
        if n < 1 or n > MAX_CUSTOM_DIVISOR:
            raise ValueError(
                f"Custom divisor must be between 1 and {MAX_CUSTOM_DIVISOR}; got {n}."
            )
        calculator = _CUSTOM_SCHEMES[scheme](n)
    else:
        calculator = _resolve_calculator(code)

    lon = normalize_degrees(sidereal_longitude)
    sign_index = int(lon / 30.0)
    deg = lon % 30.0
    return calculator(sign_index, deg)


# ── Divisional Engine ─────────────────────────────────────────────────────────

class DivisionalEngine:
    """
    Computes all 15 supported Varga charts from a birth moment.

    Usage::

        wrapper = EphemerisWrapper("data/ephemeris")
        engine = DivisionalEngine(wrapper)
        chart = engine.compute(birth_dt, lat, lon, varga="D9")
    """

    def __init__(
        self,
        ephemeris_wrapper: EphemerisWrapper,
        birth_chart_repo=None,
        divisional_chart_repo=None,
        divisional_planet_repo=None,
    ) -> None:
        self._wrapper = ephemeris_wrapper
        # Optional — only required for persist_chart()/persist_all().
        # Default None keeps the existing single-arg construction working
        # for callers/tests that don't need persistence.
        self._birth_chart_repo = birth_chart_repo
        self._divisional_chart_repo = divisional_chart_repo
        self._divisional_planet_repo = divisional_planet_repo

    # ── Public API ─────────────────────────────────────────────────────────────

    def compute(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        varga: str,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        scheme: str = "cyclic",
    ) -> VargaChart:
        """
        Compute a single Varga chart.

        Args:
            birth_datetime_utc: UTC birth datetime (timezone-aware).
            latitude:           Geographic latitude (-90 to +90).
            longitude:          Geographic longitude (-180 to +180).
            varga:              Divisional chart code — classical ('D2' … 'D144'),
                                custom ('D13'), or sub-divisional ('D9xD12').
            ayanamsa:           Ayanamsa system key (default 'lahiri').
            house_system:       House system code — used only for D1 context (default 'W').
            scheme:             Generic-division scheme, consulted only for a
                                custom 'Dn' with no classical rule.

        Returns:
            A fully computed VargaChart.

        Raises:
            ValueError: For unsupported varga codes or naive datetimes.
        """
        # Validate up front so a bad code fails before the ephemeris call
        # rather than once per body inside _build_from_result. Accepts custom
        # "Dn" and sub-divisional "DaxDb" alongside the classical codes.
        _resolve_calculator(varga)

        result = self._wrapper.calculate(
            dt=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        return self._build_from_result(result, varga, ayanamsa, scheme=scheme)

    def compute_all(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> dict[str, VargaChart]:
        """
        Compute all 19 Varga charts in a single call.

        Returns:
            Mapping of varga code → VargaChart, e.g. {"D9": VargaChart(...), …}.
        """
        # Run the ephemeris once; all varga derivations are deterministic
        result = self._wrapper.calculate(
            dt=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )

        charts: dict[str, VargaChart] = {}
        for varga_code in SUPPORTED_VARGAS:
            # Reuse already-computed ephemeris result by calling _build directly
            charts[varga_code] = self._build_from_result(
                result, varga_code, ayanamsa
            )
        return charts

    # ── Persistence ──────────────────────────────────────────────────────────
    #
    # Separate from compute()/compute_all() rather than combined
    # "compute_and_persist" methods, for the same reason as HoroscopeEngine:
    # compute()/compute_all() are blocking pyswisseph calls that routers
    # offload via asyncio.to_thread; persistence is async DB I/O with no
    # CPU-bound work and does not belong inside that thread offload.

    async def persist_chart(
        self,
        chart: VargaChart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        user_id=None,
        subject_name: str = "Unnamed",
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """
        Persist an already-computed VargaChart (from compute()): the
        birth_charts anchor row (created if this subject has no existing
        one), the divisional_charts identity row, and its 9 planet
        placements.

        Requires this engine to have been constructed with
        birth_chart_repo, divisional_chart_repo, and divisional_planet_repo
        — raises RuntimeError otherwise.

        Returns (birth_chart_id, divisional_chart_id).
        """
        self._require_persistence_repos()

        birth_chart_id = await self._birth_chart_repo.get_or_create(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            user_id=user_id,
            subject_name=subject_name,
        )

        divisional_chart_id = await self._divisional_chart_repo.replace_for_birth_chart(
            birth_chart_id,
            chart.varga,
            lagna_rashi=chart.ascendant.varga_rashi,
            lagna_degree=chart.ascendant.varga_rashi_degree,
        )

        await self._divisional_planet_repo.bulk_insert(
            divisional_chart_id, chart.planet_positions
        )

        return birth_chart_id, divisional_chart_id

    async def persist_all(
        self,
        charts: dict[str, VargaChart],
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        user_id=None,
        subject_name: str = "Unnamed",
        birth_chart_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """
        Persist the full dict returned by compute_all() — one
        birth_charts row shared across all 22 vargas, one
        divisional_charts row per varga.

        birth_chart_id: pass this when the caller already resolved the
        birth_charts row (e.g. WorkflowOrchestrator.analyze() always
        calls HoroscopeEngine.persist_d1() first) — skips a redundant
        natural-key SELECT against Postgres that would otherwise re-run
        get_or_create()'s full lookup for a row we already have the id
        for. Standalone callers (e.g. a divisional-only API request with
        no prior D1 persistence) can omit it and get_or_create() runs as
        before. Fixed as part of Phase 10's cleanup pass (2026-07-23),
        flagged by the retroactive performance review.

        Returns the shared birth_chart_id.
        """
        self._require_persistence_repos()

        if birth_chart_id is None:
            birth_chart_id = await self._birth_chart_repo.get_or_create(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa,
                house_system=house_system,
                user_id=user_id,
                subject_name=subject_name,
            )

        for chart in charts.values():
            divisional_chart_id = await self._divisional_chart_repo.replace_for_birth_chart(
                birth_chart_id,
                chart.varga,
                lagna_rashi=chart.ascendant.varga_rashi,
                lagna_degree=chart.ascendant.varga_rashi_degree,
            )
            await self._divisional_planet_repo.bulk_insert(
                divisional_chart_id, chart.planet_positions
            )

        return birth_chart_id

    def _require_persistence_repos(self) -> None:
        if not (
            self._birth_chart_repo
            and self._divisional_chart_repo
            and self._divisional_planet_repo
        ):
            raise RuntimeError(
                "DivisionalEngine persistence requires birth_chart_repo, "
                "divisional_chart_repo, and divisional_planet_repo to be "
                "provided at construction time."
            )

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _build_from_result(
        self,
        result,  # EphemerisResult — avoid circular import with type hint
        varga: str,
        ayanamsa: str,
        scheme: str = "cyclic",
    ) -> VargaChart:
        """Build a VargaChart from an already-computed EphemerisResult."""
        asc_sid = result.ascendant.sidereal_longitude
        asc_d1_rashi, asc_d1_deg = longitude_to_rashi(asc_sid)
        asc_v_rashi, asc_v_deg = compute_varga_sign(varga, asc_sid, scheme=scheme)

        varga_ascendant = VargaAscendant(
            d1_sidereal_longitude=asc_sid,
            d1_rashi=asc_d1_rashi,
            d1_rashi_degree=asc_d1_deg,
            varga_rashi=asc_v_rashi,
            varga_rashi_degree=asc_v_deg,
        )

        lagna_rashi_idx = _RASHI_LIST.index(asc_v_rashi)

        varga_positions: list[VargaPosition] = []
        for sid_pos in result.planet_positions:
            planet = sid_pos.planet
            d1_sid = sid_pos.sidereal_longitude
            d1_rashi, d1_deg = longitude_to_rashi(d1_sid)

            if varga == "D30" and planet in ("sun", "moon"):
                v_rashi, v_deg = d1_rashi, d1_deg
            else:
                v_rashi, v_deg = compute_varga_sign(varga, d1_sid, scheme=scheme)

            v_rashi_idx = _RASHI_LIST.index(v_rashi)
            house_number = house_offset(lagna_rashi_idx, v_rashi_idx)
            nak_info = longitude_to_nakshatra(d1_sid)

            varga_positions.append(
                VargaPosition(
                    planet=planet,
                    d1_sidereal_longitude=d1_sid,
                    d1_rashi=d1_rashi,
                    d1_rashi_degree=round(d1_deg, 6),
                    varga_rashi=v_rashi,
                    varga_rashi_degree=round(v_deg, 6),
                    varga_house_number=house_number,
                    is_retrograde=sid_pos.is_retrograde,
                    is_combust=sid_pos.is_combust,
                    nakshatra=nak_info.nakshatra,
                    pada=nak_info.pada,
                )
            )

        varga_positions.sort(key=lambda p: (p.varga_house_number, p.planet))

        return VargaChart(
            varga=varga,
            divisor=varga_divisor(varga),
            ascendant=varga_ascendant,
            planet_positions=tuple(varga_positions),
            ayanamsa_system=ayanamsa,
            julian_day=result.julian_day,
        )
