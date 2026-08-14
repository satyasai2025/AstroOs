"""
AstroOS — Divisional Chart Engine Unit Tests (Task 5)

Covers:
  - compute_varga_sign() for all 19 varga codes
  - D2 Hora — odd/even sign, first/second half
  - D3 Drekkana — three trines
  - D4 Chaturthamsha — four kendras
  - D9 Navamsha — standard zodiacal formula verification
  - D12 Dvadashamsha — starts from natal sign
  - D30 Trimshamsha — Parashara non-uniform; Sun/Moon receive D1 sign
  - D60 Shashtiamsha — odd/even alternation
  - DivisionalEngine.compute() — structure, planet count, house ranges
  - DivisionalEngine.compute_all() — all 19 vargas, determinism
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.divisional import VargaChart, VargaPosition
from apps.api.services.divisional_engine import (
    DivisionalEngine,
    SUPPORTED_VARGAS,
    compute_varga_sign,
    _d2_hora,
    _d3_drekkana,
    _d4_chaturthamsha,
    _d5_panchamsha,
    _d6_shashthamsha,
    _d8_ashtamsha,
    _d9_navamsha,
    _d11_rudramsha,
    _d12_dvadashamsha,
    _d30_trimshamsha,
    _d60_shashtiamsha,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_EPHE_PATH = "data/ephemeris"
_VALID_RASHIS = frozenset({
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
})

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine() -> DivisionalEngine:
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    return DivisionalEngine(wrapper)


@pytest.fixture(scope="module")
def sample_d9(engine) -> VargaChart:
    """Reference Navamsha chart: 2000-01-01 05:30 UTC, New Delhi."""
    dt = datetime(2000, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    return engine.compute(
        birth_datetime_utc=dt,
        latitude=28.6139,
        longitude=77.2090,
        varga="D9",
    )


# ── compute_varga_sign() — unit tests ─────────────────────────────────────────

def test_compute_varga_sign_invalid_varga():
    with pytest.raises(ValueError, match="Unknown varga"):
        compute_varga_sign("D99", 0.0)


@pytest.mark.parametrize("varga", list(SUPPORTED_VARGAS))
def test_compute_varga_sign_all_vargas_return_valid_rashi(varga):
    """All vargas must return a valid rashi for any longitude."""
    rashi, deg = compute_varga_sign(varga, 45.0)
    assert rashi in _VALID_RASHIS
    assert 0.0 <= deg < 30.0


@pytest.mark.parametrize("lon", [0.0, 30.0, 60.0, 90.0, 180.0, 270.0, 359.9])
@pytest.mark.parametrize("varga", list(SUPPORTED_VARGAS))
def test_compute_varga_sign_degree_in_bounds(varga, lon):
    """Varga degree must always be in [0, 30) regardless of input."""
    _, deg = compute_varga_sign(varga, lon)
    assert 0.0 <= deg < 30.0, f"{varga} @ {lon}° → deg={deg}"


# ── D2 (Hora) ─────────────────────────────────────────────────────────────────

def test_d2_odd_sign_first_half_is_leo():
    """Aries (odd sign, index 0), first 15° → Leo."""
    vsign, vdeg = _d2_hora(sign_index=0, deg=7.5)
    assert vsign == "leo"
    assert 0.0 <= vdeg < 30.0


def test_d2_odd_sign_second_half_is_cancer():
    """Aries (odd sign), second 15° → Cancer."""
    vsign, _ = _d2_hora(sign_index=0, deg=20.0)
    assert vsign == "cancer"


def test_d2_even_sign_first_half_is_cancer():
    """Taurus (even sign, index 1), first 15° → Cancer."""
    vsign, _ = _d2_hora(sign_index=1, deg=5.0)
    assert vsign == "cancer"


def test_d2_even_sign_second_half_is_leo():
    """Taurus (even sign), second 15° → Leo."""
    vsign, _ = _d2_hora(sign_index=1, deg=20.0)
    assert vsign == "leo"


def test_d2_boundary_exactly_15():
    """Exactly 15° falls into the second half (Leo/Cancer swap)."""
    # Aries, 15.0° → second half → Cancer
    vsign, _ = _d2_hora(sign_index=0, deg=15.0)
    assert vsign == "cancer"


def test_d2_only_two_possible_signs():
    """Hora chart can only place planets in Cancer or Leo."""
    for sign_idx in range(12):
        for half_deg in [7.0, 22.0]:
            vsign, _ = _d2_hora(sign_idx, half_deg)
            assert vsign in ("cancer", "leo")


# ── D3 (Drekkana) ─────────────────────────────────────────────────────────────

def test_d3_first_part_same_sign():
    """Aries (0), first 10° → Aries."""
    vsign, _ = _d3_drekkana(sign_index=0, deg=5.0)
    assert vsign == "aries"


def test_d3_second_part_fifth_sign():
    """Aries (0), 10–20° → 5th sign = Leo (offset 4)."""
    vsign, _ = _d3_drekkana(sign_index=0, deg=15.0)
    assert vsign == "leo"


def test_d3_third_part_ninth_sign():
    """Aries (0), 20–30° → 9th sign = Sagittarius (offset 8)."""
    vsign, _ = _d3_drekkana(sign_index=0, deg=25.0)
    assert vsign == "sagittarius"


def test_d3_taurus_first_part():
    """Taurus (1), first 10° → Taurus (same sign)."""
    vsign, _ = _d3_drekkana(sign_index=1, deg=3.0)
    assert vsign == "taurus"


def test_d3_taurus_second_part():
    """Taurus (1), 10–20° → (1+4)%12 = 5 → Virgo."""
    vsign, _ = _d3_drekkana(sign_index=1, deg=15.0)
    assert vsign == "virgo"


def test_d3_degree_scaled_to_30():
    """Drekkana degree is scaled: 10° span → 30° in varga sign."""
    _, vdeg = _d3_drekkana(sign_index=0, deg=5.0)  # 5° in first 10° span
    assert abs(vdeg - 15.0) < 1e-9


# ── D5 (Panchamsha) ───────────────────────────────────────────────────────────
# Non-sequential target-sign scheme: Mars/Saturn/Jupiter/Mercury/Venus order,
# not a simple offset. Worked example: Aries (odd), 2nd part (6-12deg, Saturn) -> Aquarius.

def test_d5_odd_sign_part0_is_aries():
    """Aries (odd, index 0), 1st part (0-6°, Mars) → Aries."""
    vsign, _ = _d5_panchamsha(sign_index=0, deg=3.0)
    assert vsign == "aries"


def test_d5_odd_sign_part1_is_aquarius():
    """Aries (odd), 2nd part (6-12°, Saturn) → Aquarius — worked example."""
    vsign, _ = _d5_panchamsha(sign_index=0, deg=8.0)
    assert vsign == "aquarius"


def test_d5_even_sign_part1_is_virgo():
    """Taurus (even, index 1), 2nd part (6-12°) → Virgo.

    Verified against a JHora reference chart (2026-08-15, Pune): Gulika
    and Uranus both land in Taurus 6-12deg and both show D5=Virgo.
    """
    vsign, _ = _d5_panchamsha(sign_index=1, deg=8.0)
    assert vsign == "virgo"


def test_d5_even_sign_part0_is_taurus():
    """Taurus (even), 1st part (0-6°) → Taurus (self).

    Verified against the same JHora reference chart: Mrityu Sphuta in
    Taurus 4°50' shows D5=Taurus.
    """
    vsign, _ = _d5_panchamsha(sign_index=1, deg=2.0)
    assert vsign == "taurus"


def test_d5_only_ten_possible_signs():
    """Panchamsha places planets in one of five odd-sign or five even-sign targets."""
    odd_allowed = {"aries", "aquarius", "sagittarius", "gemini", "libra"}
    even_allowed = {"taurus", "virgo", "pisces", "capricorn", "scorpio"}
    for sign_idx in range(12):
        allowed = odd_allowed if sign_idx % 2 == 0 else even_allowed
        for deg in (1.0, 7.0, 13.0, 19.0, 25.0):
            vsign, _ = _d5_panchamsha(sign_idx, deg)
            assert vsign in allowed


# ── D6 (Shashthamsha) ─────────────────────────────────────────────────────────

def test_d6_odd_sign_starts_from_aries():
    """Aries (odd, index 0), 1st part (0-5°) → Aries."""
    vsign, _ = _d6_shashthamsha(sign_index=0, deg=2.0)
    assert vsign == "aries"


def test_d6_even_sign_starts_from_libra():
    """Taurus (even, index 1), 1st part (0-5°) → Libra."""
    vsign, _ = _d6_shashthamsha(sign_index=1, deg=2.0)
    assert vsign == "libra"


def test_d6_degree_scaled_to_30():
    """Shashthamsha degree is scaled: 5° span → 30° in varga sign."""
    _, vdeg = _d6_shashthamsha(sign_index=0, deg=2.5)  # midpoint of first 5° span
    assert abs(vdeg - 15.0) < 1e-9


# ── D8 (Ashtamsha) ────────────────────────────────────────────────────────────

def test_d8_movable_sign_starts_from_aries():
    """Aries (movable, index 0) → starting sign Aries."""
    vsign, _ = _d8_ashtamsha(sign_index=0, deg=1.0)
    assert vsign == "aries"


def test_d8_fixed_sign_starts_from_sagittarius():
    """Taurus (fixed, index 1) → starting sign Sagittarius."""
    vsign, _ = _d8_ashtamsha(sign_index=1, deg=1.0)
    assert vsign == "sagittarius"


def test_d8_dual_sign_starts_from_leo():
    """Gemini (dual, index 2) → starting sign Leo."""
    vsign, _ = _d8_ashtamsha(sign_index=2, deg=1.0)
    assert vsign == "leo"


# ── D11 (Rudramsha) ───────────────────────────────────────────────────────────

def test_d11_start_sign_is_reverse_count_from_aries():
    """Gemini (index 2) → start sign = (12-2)%12 = 10 → Aquarius, part 0."""
    vsign, _ = _d11_rudramsha(sign_index=2, deg=1.0)
    assert vsign == "aquarius"


def test_d11_worked_example_gemini_5th_part_lands_back_in_gemini():
    """Gemini, 5th part (Mercury @ 11°) → (10+4)%12 == 2 → Gemini."""
    vsign, _ = _d11_rudramsha(sign_index=2, deg=11.0)
    assert vsign == "gemini"


# ── D4 (Chaturthamsha) ────────────────────────────────────────────────────────

def test_d4_aries_four_parts():
    """Aries (0): 0-7.5→Aries, 7.5-15→Cancer, 15-22.5→Libra, 22.5-30→Capricorn."""
    expected = ["aries", "cancer", "libra", "capricorn"]
    centres = [3.75, 11.25, 18.75, 26.25]
    for i, (ctr, exp) in enumerate(zip(centres, expected)):
        vsign, _ = _d4_chaturthamsha(sign_index=0, deg=ctr)
        assert vsign == exp, f"D4 Aries part {i+1}: expected {exp}, got {vsign}"


# ── D9 (Navamsha) ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("sign_idx, expected_first_nav", [
    (0, "aries"),        # Fire → Aries
    (1, "capricorn"),    # Earth → Capricorn
    (2, "libra"),        # Air → Libra
    (3, "cancer"),       # Water → Cancer
    (4, "aries"),        # Fire → Aries
    (5, "capricorn"),    # Earth → Capricorn
    (6, "libra"),        # Air → Libra
    (7, "cancer"),       # Water → Cancer
    (8, "aries"),        # Fire → Aries
    (9, "capricorn"),    # Earth → Capricorn
    (10, "libra"),       # Air → Libra
    (11, "cancer"),      # Water → Cancer
])
def test_d9_first_navamsha_per_sign(sign_idx, expected_first_nav):
    """First Navamsha of each sign follows the elemental starting point."""
    vsign, _ = _d9_navamsha(sign_index=sign_idx, deg=0.1)
    assert vsign == expected_first_nav, (
        f"D9 sign {sign_idx}: expected {expected_first_nav}, got {vsign}"
    )


def test_d9_aries_all_nine_navamshas():
    """Aries has 9 Navamshas: Aries → Sagittarius (9 consecutive signs)."""
    expected = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius",
    ]
    part_size = 30.0 / 9.0
    for i, exp in enumerate(expected):
        deg = i * part_size + 0.01
        vsign, _ = _d9_navamsha(sign_index=0, deg=deg)
        assert vsign == exp, f"Aries D9 part {i+1}: expected {exp}, got {vsign}"


# ── D12 (Dvadashamsha) ───────────────────────────────────────────────────────

def test_d12_aries_first_part_is_aries():
    vsign, _ = _d12_dvadashamsha(sign_index=0, deg=0.5)
    assert vsign == "aries"


def test_d12_taurus_first_part_is_taurus():
    vsign, _ = _d12_dvadashamsha(sign_index=1, deg=0.5)
    assert vsign == "taurus"


def test_d12_twelve_parts_cycle_full_zodiac():
    """Aries splits into all 12 signs sequentially (Aries to Pisces)."""
    all_signs = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    part_size = 2.5
    for i, exp in enumerate(all_signs):
        deg = i * part_size + 0.01
        vsign, _ = _d12_dvadashamsha(sign_index=0, deg=deg)
        assert vsign == exp, f"D12 Aries part {i+1}: expected {exp}, got {vsign}"


# ── D30 (Trimshamsha) — Parashara rules ───────────────────────────────────────

def test_d30_odd_sign_first_5deg_is_aries():
    """Aries (odd), 0–5° → Aries (Mars portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=0, deg=2.5)
    assert vsign == "aries"


def test_d30_odd_sign_5to10_is_aquarius():
    """Aries (odd), 5–10° → Aquarius (Saturn portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=0, deg=7.5)
    assert vsign == "aquarius"


def test_d30_odd_sign_10to18_is_sagittarius():
    """Aries (odd), 10–18° → Sagittarius (Jupiter portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=0, deg=14.0)
    assert vsign == "sagittarius"


def test_d30_odd_sign_18to25_is_gemini():
    """Aries (odd), 18–25° → Gemini (Mercury portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=0, deg=21.0)
    assert vsign == "gemini"


def test_d30_odd_sign_25to30_is_libra():
    """Aries (odd), 25–30° → Libra (Venus portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=0, deg=27.0)
    assert vsign == "libra"


def test_d30_even_sign_first_5deg_is_taurus():
    """Taurus (even), 0–5° → Taurus (Venus portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=1, deg=2.5)
    assert vsign == "taurus"


def test_d30_even_sign_5to12_is_virgo():
    """Taurus (even), 5–12° → Virgo (Mercury portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=1, deg=8.0)
    assert vsign == "virgo"


def test_d30_even_sign_12to20_is_pisces():
    """Taurus (even), 12–20° → Pisces (Jupiter portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=1, deg=16.0)
    assert vsign == "pisces"


def test_d30_even_sign_20to25_is_capricorn():
    """Taurus (even), 20–25° → Capricorn (Saturn portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=1, deg=22.0)
    assert vsign == "capricorn"


def test_d30_even_sign_25to30_is_scorpio():
    """Taurus (even), 25–30° → Scorpio (Mars portion)."""
    vsign, _ = _d30_trimshamsha(sign_index=1, deg=27.0)
    assert vsign == "scorpio"


# ── D60 (Shashtiamsha) ────────────────────────────────────────────────────────

def test_d60_odd_sign_starts_aries():
    """Aries (odd), first 0.5° part → Aries."""
    vsign, _ = _d60_shashtiamsha(sign_index=0, deg=0.1)
    assert vsign == "aries"


def test_d60_even_sign_starts_libra():
    """Taurus (even), first 0.5° part → Libra."""
    vsign, _ = _d60_shashtiamsha(sign_index=1, deg=0.1)
    assert vsign == "libra"


def test_d60_odd_sign_60_parts_cycle_5_times():
    """Aries has 60 parts, cycling through 12 signs 5 times."""
    for part in range(60):
        deg = part * 0.5 + 0.01
        vsign, vdeg = _d60_shashtiamsha(sign_index=0, deg=deg)
        assert vsign in _VALID_RASHIS
        expected_sign_idx = part % 12
        from apps.api.services.divisional_engine import _RASHI_LIST
        assert vsign == _RASHI_LIST[expected_sign_idx], (
            f"D60 Aries part {part}: expected {_RASHI_LIST[expected_sign_idx]}, got {vsign}"
        )


# ── DivisionalEngine.compute() — integration ─────────────────────────────────

def test_engine_compute_returns_varga_chart(sample_d9):
    assert isinstance(sample_d9, VargaChart)


def test_engine_compute_correct_varga_label(sample_d9):
    assert sample_d9.varga == "D9"
    assert sample_d9.divisor == 9


def test_engine_compute_has_9_planets(sample_d9):
    assert len(sample_d9.planet_positions) == 9


def test_engine_compute_all_planets_present(sample_d9):
    names = {p.planet for p in sample_d9.planet_positions}
    expected = {"sun", "moon", "mars", "mercury", "jupiter",
                "venus", "saturn", "rahu", "ketu"}
    assert names == expected


def test_engine_compute_valid_ascendant(sample_d9):
    assert sample_d9.ascendant.varga_rashi in _VALID_RASHIS
    assert 0.0 <= sample_d9.ascendant.varga_rashi_degree < 30.0


def test_engine_compute_house_numbers_1_to_12(sample_d9):
    for p in sample_d9.planet_positions:
        assert 1 <= p.varga_house_number <= 12, (
            f"{p.planet} house {p.varga_house_number} out of range"
        )


def test_engine_compute_pada_1_to_4(sample_d9):
    for p in sample_d9.planet_positions:
        assert 1 <= p.pada <= 4


def test_engine_compute_d30_sun_moon_keep_d1_sign(engine):
    """In D30, Sun and Moon must retain their D1 sign (Parashara rule)."""
    dt = datetime(2000, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    chart = engine.compute(
        birth_datetime_utc=dt,
        latitude=28.6139,
        longitude=77.2090,
        varga="D30",
    )
    sun = next(p for p in chart.planet_positions if p.planet == "sun")
    moon = next(p for p in chart.planet_positions if p.planet == "moon")
    assert sun.varga_rashi == sun.d1_rashi
    assert moon.varga_rashi == moon.d1_rashi


def test_engine_compute_invalid_varga_raises(engine):
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="Unsupported varga"):
        engine.compute(birth_datetime_utc=dt, latitude=0.0, longitude=0.0, varga="D99")


@pytest.mark.parametrize("varga", list(SUPPORTED_VARGAS))
def test_engine_all_vargas_compute_successfully(engine, varga):
    """Every supported varga must compute without error."""
    dt = datetime(2000, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
    chart = engine.compute(
        birth_datetime_utc=dt,
        latitude=51.5074,
        longitude=-0.1278,
        varga=varga,
    )
    assert len(chart.planet_positions) == 9
    assert chart.varga == varga
    assert chart.ascendant.varga_rashi in _VALID_RASHIS


# ── DivisionalEngine.compute_all() ───────────────────────────────────────────

def test_compute_all_returns_15_charts(engine):
    dt = datetime(2000, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    all_charts = engine.compute_all(
        birth_datetime_utc=dt, latitude=28.6139, longitude=77.2090
    )
    assert len(all_charts) == 19
    assert set(all_charts) == set(SUPPORTED_VARGAS)


def test_compute_all_consistent_jd(engine):
    """All charts from compute_all() must have the same Julian Day."""
    dt = datetime(2000, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    all_charts = engine.compute_all(
        birth_datetime_utc=dt, latitude=28.6139, longitude=77.2090
    )
    jds = {chart.julian_day for chart in all_charts.values()}
    assert len(jds) == 1, f"Multiple Julian Days across compute_all: {jds}"


def test_compute_all_matches_single_compute(engine):
    """compute_all() result for D9 must match a standalone compute("D9")."""
    dt = datetime(1985, 3, 21, 14, 0, 0, tzinfo=timezone.utc)
    kwargs = {"birth_datetime_utc": dt, "latitude": 19.076, "longitude": 72.877}

    single = engine.compute(**kwargs, varga="D9")
    all_charts = engine.compute_all(**kwargs)
    batch_d9 = all_charts["D9"]

    assert single.ascendant.varga_rashi == batch_d9.ascendant.varga_rashi
    for ps, pb in zip(
        sorted(single.planet_positions, key=lambda p: p.planet),
        sorted(batch_d9.planet_positions, key=lambda p: p.planet),
    ):
        assert ps.planet == pb.planet
        assert ps.varga_rashi == pb.varga_rashi, (
            f"{ps.planet}: single={ps.varga_rashi}, batch={pb.varga_rashi}"
        )


def test_compute_all_is_deterministic(engine):
    """Two calls with same input must produce identical results."""
    dt = datetime(1990, 11, 9, 0, 0, 0, tzinfo=timezone.utc)
    kwargs = {"birth_datetime_utc": dt, "latitude": 52.52, "longitude": 13.405}

    a = engine.compute_all(**kwargs)
    b = engine.compute_all(**kwargs)

    for varga_code in SUPPORTED_VARGAS:
        chart_a = a[varga_code]
        chart_b = b[varga_code]
        assert chart_a.ascendant.varga_rashi == chart_b.ascendant.varga_rashi
        for pa, pb in zip(chart_a.planet_positions, chart_b.planet_positions):
            assert pa.varga_rashi == pb.varga_rashi
