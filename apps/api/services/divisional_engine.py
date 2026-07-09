"""
AstroOS — Divisional Chart Engine (Task 5)

Computes all 15 Varga charts (D2–D60) using Parashara rules.

Varga rules implemented
-----------------------
D2  (Hora)              — 2 parts; Sun/Moon hora alternation by odd/even sign
D3  (Drekkana)          — 3 parts; 1st/5th/9th trines from natal sign
D4  (Chaturthamsha)     — 4 parts; successive kendras from natal sign
D7  (Saptamsha)         — 7 parts; odd sign starts from same sign, even from 7th
D9  (Navamsha)          — 9 parts; standard zodiacal formula (sign × 9 + part)
D10 (Dasamsha)          — 10 parts; odd sign from same, even sign from 9th
D12 (Dvadashamsha)      — 12 parts; starts from natal sign
D16 (Shodashamsha)      — 16 parts; Cardinal→Aries, Fixed→Leo, Mutable→Sagittarius
D20 (Vimshamsha)        — 20 parts; Movable→Aries, Fixed→Sagittarius, Dual→Leo
D24 (Chaturvimshamsha)  — 24 parts; odd sign→Leo, even sign→Cancer
D27 (Bhamsha)           — 27 parts; Fire→Aries, Earth→Cancer, Air→Libra, Water→Cap
D30 (Trimshamsha)       — 30 non-equal parts; Parashara special ruleset
D40 (Khavedamsha)       — 40 parts; odd→Aries, even→Libra
D45 (Akshavedamsha)     — 45 parts; Movable→Aries, Fixed→Leo, Dual→Sagittarius
D60 (Shashtiamsha)      — 60 parts; odd→Aries, even→Libra

All degrees within a varga sign are normalised to [0, 30).
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.divisional import VargaAscendant, VargaChart, VargaPosition
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)

# ── Sign constants ────────────────────────────────────────────────────────────

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

# All supported vargas (divisor → label)
SUPPORTED_VARGAS: dict[str, int] = {
    "D2": 2, "D3": 3, "D4": 4, "D7": 7, "D9": 9,
    "D10": 10, "D12": 12, "D16": 16, "D20": 20, "D24": 24,
    "D27": 27, "D30": 30, "D40": 40, "D45": 45, "D60": 60,
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
    Sixty equal 0.5° parts.
    Odd sign: starts from Aries (0).
    Even sign: starts from Libra (6).
    """
    part_size = 0.5
    part = min(int(deg / part_size), 59)
    start = 0 if _is_odd_sign(sign_index) else 6
    vsign_idx = (start + part) % 12
    vdeg = (deg % part_size) * 60.0
    return _RASHI_LIST[vsign_idx], vdeg


# ── Dispatch table ────────────────────────────────────────────────────────────

_VARGA_CALCULATOR = {
    "D2":  _d2_hora,
    "D3":  _d3_drekkana,
    "D4":  _d4_chaturthamsha,
    "D7":  _d7_saptamsha,
    "D9":  _d9_navamsha,
    "D10": _d10_dasamsha,
    "D12": _d12_dvadashamsha,
    "D16": _d16_shodashamsha,
    "D20": _d20_vimshamsha,
    "D24": _d24_chaturvimshamsha,
    "D27": _d27_bhamsha,
    "D30": _d30_trimshamsha,
    "D40": _d40_khavedamsha,
    "D45": _d45_akshavedamsha,
    "D60": _d60_shashtiamsha,
}


# ── Low-level helpers ─────────────────────────────────────────────────────────

def compute_varga_sign(varga: str, sidereal_longitude: float) -> tuple[str, float]:
    """
    Public helper: compute the varga sign and degree for any planet or ascendant.

    Args:
        varga:              One of SUPPORTED_VARGAS keys ("D2", "D9", …).
        sidereal_longitude: Sidereal longitude in [0, 360).

    Returns:
        (varga_rashi, varga_rashi_degree) — sign name + degree within sign [0, 30).

    Raises:
        ValueError: If the varga code is not recognised.
    """
    if varga not in _VARGA_CALCULATOR:
        raise ValueError(
            f"Unknown varga '{varga}'. Supported: {sorted(_VARGA_CALCULATOR)}"
        )
    lon = sidereal_longitude % 360.0
    sign_index = int(lon / 30.0)
    deg = lon % 30.0
    return _VARGA_CALCULATOR[varga](sign_index, deg)


# ── Divisional Engine ─────────────────────────────────────────────────────────

class DivisionalEngine:
    """
    Computes all 15 supported Varga charts from a birth moment.

    Usage::

        wrapper = EphemerisWrapper("data/ephemeris")
        engine = DivisionalEngine(wrapper)
        chart = engine.compute(birth_dt, lat, lon, varga="D9")
    """

    def __init__(self, ephemeris_wrapper: EphemerisWrapper) -> None:
        self._wrapper = ephemeris_wrapper

    # ── Public API ─────────────────────────────────────────────────────────────

    def compute(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        varga: str,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> VargaChart:
        """
        Compute a single Varga chart.

        Args:
            birth_datetime_utc: UTC birth datetime (timezone-aware).
            latitude:           Geographic latitude (-90 to +90).
            longitude:          Geographic longitude (-180 to +180).
            varga:              Divisional chart code ('D2' … 'D60').
            ayanamsa:           Ayanamsa system key (default 'lahiri').
            house_system:       House system code — used only for D1 context (default 'W').

        Returns:
            A fully computed VargaChart.

        Raises:
            ValueError: For unsupported varga codes or naive datetimes.
        """
        if varga not in SUPPORTED_VARGAS:
            raise ValueError(
                f"Unsupported varga '{varga}'. Choose from: {sorted(SUPPORTED_VARGAS)}"
            )

        result = self._wrapper.calculate(
            dt=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        return self._build_from_result(result, varga, ayanamsa)

    def compute_all(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> dict[str, VargaChart]:
        """
        Compute all 15 Varga charts in a single call.

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

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _build_from_result(
        self,
        result,  # EphemerisResult — avoid circular import with type hint
        varga: str,
        ayanamsa: str,
    ) -> VargaChart:
        """Build a VargaChart from an already-computed EphemerisResult."""
        asc_sid = result.ascendant.sidereal_longitude
        asc_d1_rashi, asc_d1_deg = longitude_to_rashi(asc_sid)
        asc_v_rashi, asc_v_deg = compute_varga_sign(varga, asc_sid)

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
                v_rashi, v_deg = compute_varga_sign(varga, d1_sid)

            v_rashi_idx = _RASHI_LIST.index(v_rashi)
            house_number = ((v_rashi_idx - lagna_rashi_idx) % 12) + 1
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
            divisor=SUPPORTED_VARGAS[varga],
            ascendant=varga_ascendant,
            planet_positions=tuple(varga_positions),
            ayanamsa_system=ayanamsa,
            julian_day=result.julian_day,
        )
