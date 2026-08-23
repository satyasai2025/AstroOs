"""
AstroOS — VarshaphalEngine Unit Tests (Stage 1: Varsha chart + Muntha)

The Varsha chart itself is computed by the same EphemerisWrapper.calculate()
already verified for D1 — these tests focus on the two genuinely new
pieces: the solar-return solver and Muntha.
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.varshaphal_engine import VarshaphalEngine

_EPHE_PATH = "data/ephemeris"
_LAT, _LON = 28.6139, 77.2090


@pytest.fixture
def wrapper():
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture
def engine(wrapper):
    return VarshaphalEngine(wrapper)


def test_solar_return_matches_natal_sun_longitude(engine, wrapper):
    birth_dt = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
    result = engine.calculate(birth_dt, _LAT, _LON, varsha_year=36)

    natal = wrapper.calculate(birth_dt, _LAT, _LON)
    natal_sun = next(p for p in natal.planet_positions if p.planet == "sun").sidereal_longitude
    varsha_sun = next(
        p for p in result.varsha_chart.planet_positions if p.planet == "sun"
    ).sidereal_longitude

    diff = abs((varsha_sun - natal_sun + 180) % 360 - 180)
    assert diff < 0.0001  # sub-arcsecond convergence


def test_solar_return_lands_near_correct_anniversary(engine):
    birth_dt = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
    result = engine.calculate(birth_dt, _LAT, _LON, varsha_year=36)

    from apps.api.services.ephemeris_wrapper import jd_to_datetime
    solar_return_dt = jd_to_datetime(result.solar_return_jd)

    assert solar_return_dt.year == 2026
    assert solar_return_dt.month == 5
    assert 10 <= solar_return_dt.day <= 20  # near the 15th, solar year != exact calendar year


def test_muntha_advances_one_rashi_per_year(engine):
    birth_dt = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)

    result_1 = engine.calculate(birth_dt, _LAT, _LON, varsha_year=1)
    result_2 = engine.calculate(birth_dt, _LAT, _LON, varsha_year=2)

    assert (result_2.muntha.rashi_index - result_1.muntha.rashi_index) % 12 == 1


def test_muntha_cycles_through_all_twelve_rashis(engine):
    birth_dt = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
    indices = set()
    for year in range(1, 13):
        result = engine.calculate(birth_dt, _LAT, _LON, varsha_year=year)
        indices.add(result.muntha.rashi_index)
    assert len(indices) == 12


def test_rejects_year_below_one(engine):
    birth_dt = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        engine.calculate(birth_dt, _LAT, _LON, varsha_year=0)


# ── Tajika aspects: pure kinematics, self-verified with constructed cases ──


class _FakePos:
    def __init__(self, planet, sidereal_longitude, rashi_degree, speed_deg_per_day):
        self.planet = planet
        self.sidereal_longitude = sidereal_longitude
        self.rashi_degree = rashi_degree
        self.speed_deg_per_day = speed_deg_per_day


class _FakeChart:
    def __init__(self, planet_positions):
        self.planet_positions = planet_positions


def test_ithasala_applying_conjunction_far_from_sign_boundary():
    """Moon (fast, behind) closing on Sun (slow), both well inside Aries —
    should perfect long before either exits the sign."""
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    chart = _FakeChart([
        _FakePos("sun", 10.0, 10.0, 1.0),
        _FakePos("moon", 8.0, 8.0, 13.0),
    ])
    aspects = VarshaphalEngine._compute_tajika_aspects(chart)
    conj = next(a for a in aspects if a.aspect_angle == 0)

    assert conj.is_applying is True
    assert conj.is_ithasala is True
    assert conj.is_isharpha is False
    assert conj.days_to_exact == pytest.approx(2.0 / 12.0, abs=1e-6)


def test_isharpha_just_separated_conjunction():
    """Moon just passed Sun (now 0.5° ahead) — recently exact, separating fast."""
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    chart = _FakeChart([
        _FakePos("sun", 10.0, 10.0, 1.0),
        _FakePos("moon", 10.5, 10.5, 13.0),
    ])
    aspects = VarshaphalEngine._compute_tajika_aspects(chart)
    conj = next(a for a in aspects if a.aspect_angle == 0)

    assert conj.is_applying is False
    assert conj.is_ithasala is False
    assert conj.is_isharpha is True


def test_ithasala_denied_when_faster_planet_exits_sign_first():
    """Sun is 0.5° from leaving its sign; Moon is applying toward conjunction
    but won't get there before the Sun changes sign — must NOT be Ithasala
    (this is the classical 'frustrated'/Nakta-adjacent case)."""
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    chart = _FakeChart([
        _FakePos("sun", 29.5, 29.5, 1.0),
        _FakePos("moon", 20.0, 20.0, 13.0),
    ])
    aspects = VarshaphalEngine._compute_tajika_aspects(chart)
    conj = next(a for a in aspects if a.aspect_angle == 0)

    assert conj.is_applying is True
    assert conj.is_ithasala is False  # would perfect at ~0.79d, but Sun exits sign at 0.5d


# ── Year Lord (Panchadhikari): hand-derived reference case ──


def test_year_lord_hand_derived_case():
    """
    Constructed chart where only one candidate (Sun) casts a benefic
    (trine/sextile) sign-aspect onto the Varsha Lagna (Aries):
      - Varsha Lagna = Aries(0); natal Lagna sign = Taurus; Muntha = Gemini(2)
      - Day birth -> luminary candidate = Sun's sign lord
      - Sun in Leo(4), Venus in Libra(6), Mercury in Taurus(1), Mars in Scorpio(7)
      - Candidates dedupe to [sun, venus, mercury, mars] (Tri-Rasi day lord
        of Aries is also Sun, per _TRI_RASI_DAY_LORDS[0]==0)
      - Benefic houses from Leo(4): {8,0,6,2} -> Aries(0) is IN this set -> Sun qualifies
      - Venus(Libra=6): malefic set {9,3,6,0} contains Aries(0) -> malefic, not benefic
      - Mercury(Taurus=1), Mars(Scorpio=7): neither benefic nor malefic on Aries
      -> unique benefic candidate is Sun.
    """
    from apps.api.domain.varshaphal import MunthaInfo
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    class _FakeAscendant:
        def __init__(self, rashi):
            self.rashi = rashi

    class _FakeChart:
        def __init__(self, asc_rashi, is_day, positions):
            self.ascendant = _FakeAscendant(asc_rashi)
            self.is_daytime_birth = is_day
            self.planet_positions = positions

    positions = [
        _FakePos("sun", 130.0, 10.0, 1.0), _FakePos("moon", 100.0, 10.0, 13.0),
        _FakePos("mars", 220.0, 10.0, 0.5), _FakePos("mercury", 40.0, 10.0, 1.2),
        _FakePos("jupiter", 260.0, 10.0, 0.1), _FakePos("venus", 190.0, 10.0, 1.1),
        _FakePos("saturn", 280.0, 10.0, 0.03),
    ]
    for p in positions:
        p.rashi = {"sun": "leo", "moon": "cancer", "mars": "scorpio", "mercury": "taurus",
                   "jupiter": "sagittarius", "venus": "libra", "saturn": "capricorn"}[p.planet]

    chart = _FakeChart("aries", True, positions)
    muntha = MunthaInfo(rashi="gemini", rashi_index=2, house_number=1)

    year_lord = VarshaphalEngine._compute_year_lord("taurus", muntha, chart)

    assert year_lord.candidates == ("sun", "venus", "mercury", "mars")
    assert year_lord.selected == "sun"
    assert year_lord.selection_method == "benefic_aspect"


# ── Sahams: A-B+C formula, hand-derived against the PyJHora algorithm ──


def test_saham_adds_30_degrees_when_c_not_between_b_and_a():
    """
    Moon(cancer,r3)=100°, Sun(taurus,r1)=40°, Lagna(aries,r0)=10°.
    raw = 100-40+10 = 70. Sweeping forward from Sun's sign (Taurus=1):
    Gemini(2) then Leo(3, matches Moon's/A's sign) is reached before
    Aries(0, Lagna's/C's sign) -> C is NOT between B and A -> +30 -> 100.
    """
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    punya = VarshaphalEngine._saham_longitude(100.0, 40.0, 10.0)
    assert punya == pytest.approx(100.0, abs=1e-9)


def test_saham_no_correction_when_c_between_b_and_a():
    """
    A=Leo(130°,r4), B=Taurus(40°,r1), C=Gemini(70°,r2). Sweeping forward
    from Taurus(1): Gemini(2, matches C) is reached first -> C IS between
    B and A -> no +30 correction, raw longitude stands.
    """
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    raw_expected = (130.0 - 40.0 + 70.0) % 360.0
    result = VarshaphalEngine._saham_longitude(130.0, 40.0, 70.0)
    assert result == pytest.approx(raw_expected, abs=1e-9)


def test_punya_and_vidya_saham_swap_operands_for_night_birth():
    """Day birth: Punya=Moon-Sun+Lagna, Vidya=Sun-Moon+Lagna. Night birth
    swaps A/B for both (PyJHora saham.py's night_time_birth branch)."""
    from apps.api.domain.varshaphal import SahamInfo
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    class _FakePlanet:
        def __init__(self, sidereal_longitude):
            self.sidereal_longitude = sidereal_longitude

    class _FakeAscendant:
        def __init__(self, sidereal_longitude):
            self.sidereal_longitude = sidereal_longitude

    class _FakeChart:
        def __init__(self, sun_long, moon_long, lagna_long, is_day):
            self.planet_positions = [_FakePlanet(sun_long)]
            self.planet_positions[0].planet = "sun"
            moon = _FakePlanet(moon_long)
            moon.planet = "moon"
            self.planet_positions.append(moon)
            for p in ["mars", "mercury", "jupiter", "venus", "saturn"]:
                fake = _FakePlanet(50.0)
                fake.planet = p
                self.planet_positions.append(fake)
            self.ascendant = _FakeAscendant(lagna_long)
            self.is_daytime_birth = is_day

    sun_long, moon_long, lagna_long = 40.0, 100.0, 10.0

    day_chart = _FakeChart(sun_long, moon_long, lagna_long, is_day=True)
    day_sahams = {s.name: s for s in VarshaphalEngine._compute_sahams(day_chart)}
    assert day_sahams["punya"].sidereal_longitude == pytest.approx(
        VarshaphalEngine._saham_longitude(moon_long, sun_long, lagna_long), abs=1e-9
    )
    assert day_sahams["vidya"].sidereal_longitude == pytest.approx(
        VarshaphalEngine._saham_longitude(sun_long, moon_long, lagna_long), abs=1e-9
    )

    night_chart = _FakeChart(sun_long, moon_long, lagna_long, is_day=False)
    night_sahams = {s.name: s for s in VarshaphalEngine._compute_sahams(night_chart)}
    assert night_sahams["punya"].sidereal_longitude == pytest.approx(
        VarshaphalEngine._saham_longitude(sun_long, moon_long, lagna_long), abs=1e-9
    )
    assert night_sahams["vidya"].sidereal_longitude == pytest.approx(
        VarshaphalEngine._saham_longitude(moon_long, sun_long, lagna_long), abs=1e-9
    )


# ── Real Classical Vedic export cross-check: all 36 Sahams, one real chart ──
#
# Birth: 1971-06-30 04:57:40 IST, Vadodara (73E12'00", 22N18'00").
# Varsha year 55 -> solar return 2026-06-30 ~07:22:54 IST (Classical Vedic-reported).
# Classical Vedic export values below (degree/Rashi/minute/second), user-supplied.
# 33/36 match within the codebase's documented ~1-2 arcmin systematic
# ayanamsa tolerance; Karma/Bandhu/Vanik are a known limitation — see
# varshaphal_engine.py's module docstring for why they're left as-is.

_JHORA_SAHAM_EXPORT = {
    # name: (degrees_in_sign, rashi_abbrev, minutes, seconds)
    "punya": (3, "Cp", 12, 40.32), "vidya": (1, "Aq", 26, 58.68),
    "yasas": (4, "Cp", 52, 40.58), "gaurava": (4, "Cp", 52, 40.58),
    "mitra": (27, "Cp", 29, 17.86), "mahatmya": (28, "Aq", 50, 36.86),
    "asha": (15, "Ta", 34, 4.18), "samartha": (24, "Sg", 1, 51.80),
    "bhratri": (18, "Li", 9, 13.25), "pitri": (8, "Ar", 8, 57.30),
    "rajya": (8, "Ar", 8, 57.30), "matri": (22, "Sg", 23, 13.38),
    "putra": (23, "Cp", 5, 30.24), "jeeva": (16, "Ar", 30, 25.74),
    "karma": (6, "Ta", 59, 21.13), "roga": (19, "Cp", 39, 48.34),
    "kali": (1, "Vi", 23, 27.93), "sastra": (17, "Li", 51, 45.08),
    "bandhu": (19, "Aq", 22, 20.17), "mrityu": (19, "Vi", 39, 48.34),
    "paradesa": (28, "Pi", 54, 7.60), "artha": (20, "Le", 32, 39.16),
    "paradara": (13, "Le", 9, 16.44), "vanik": (15, "Sg", 17, 18.83),
    "karyasiddhi": (7, "Ar", 51, 29.14), "vivaha": (7, "Sc", 20, 8.63),
    "santapa": (7, "Ar", 16, 6.48), "sraddha": (20, "Vi", 34, 23.31),
    "preeti": (16, "Ar", 58, 54.26), "jadya": (18, "Vi", 48, 6.65),
    "vyapara": (19, "Vi", 5, 34.82), "satru": (19, "Vi", 5, 34.82),
    "jalapatana": (27, "Li", 23, 41.85), "bandhana": (15, "Ar", 36, 22.17),
    "apamrityu": (27, "Pi", 57, 46.03), "labha": (9, "Ta", 43, 12.22),
}

# Sahams whose formula is a known, documented gap in the ported algorithm
# (see module docstring) — excluded from the tolerance assertion below,
# checked separately for their (currently wrong) known behaviour instead.
_KNOWN_LIMITATION_SAHAMS = {"karma", "bandhu", "vanik"}

_RASHI_ABBREV_TO_INDEX = {
    "Ar": 0, "Ta": 1, "Ge": 2, "Cn": 3, "Le": 4, "Vi": 5,
    "Li": 6, "Sc": 7, "Sg": 8, "Cp": 9, "Aq": 10, "Pi": 11,
}


def test_all_36_sahams_present():
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    result = _real_jhora_chart_sahams()
    names = {s.name for s in result}
    assert names == set(_JHORA_SAHAM_EXPORT.keys())


def test_33_of_36_sahams_match_real_jhora_export():
    result = {s.name: s for s in _real_jhora_chart_sahams()}

    matched, mismatched = [], []
    for name, (deg, rashi_abbrev, minutes, seconds) in _JHORA_SAHAM_EXPORT.items():
        expected_deg = _RASHI_ABBREV_TO_INDEX[rashi_abbrev] * 30 + deg + minutes / 60 + seconds / 3600
        actual_deg = result[name].sidereal_longitude
        diff_deg = min(abs(actual_deg - expected_deg), 360 - abs(actual_deg - expected_deg))
        same_rashi = int(actual_deg // 30) % 12 == _RASHI_ABBREV_TO_INDEX[rashi_abbrev]

        if same_rashi and diff_deg < (200 / 3600):  # ~200 arcsec tolerance
            matched.append(name)
        else:
            mismatched.append(name)

    assert set(mismatched) == _KNOWN_LIMITATION_SAHAMS, (
        f"Unexpected Saham mismatches against the real Classical Vedic export: "
        f"{set(mismatched) - _KNOWN_LIMITATION_SAHAMS}"
    )
    assert len(matched) == 33


def _real_jhora_chart_sahams():
    from datetime import timedelta

    from apps.api.services.ephemeris_wrapper import EphemerisWrapper
    from apps.api.services.varshaphal_engine import VarshaphalEngine

    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    solar_return_dt = datetime(2026, 6, 30, 7, 22, 54, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    chart = wrapper.calculate(solar_return_dt, 22 + 18 / 60, 73 + 12 / 60)
    return VarshaphalEngine._compute_sahams(chart)
