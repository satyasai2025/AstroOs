"""
AstroOS — EphemerisWrapper Unit Tests (Task 3)

Tests the full Swiss Ephemeris wrapper:
  - datetime_to_jd conversion
  - longitude_to_rashi mapping
  - longitude_to_nakshatra mapping (including pada)
  - Planet position calculation (Sun at J2000.0)
  - Retrograde detection
  - Combustion detection
  - Tithi calculation
  - Yoga calculation
  - Karana calculation
  - Vara (weekday) calculation
  - Ayanamsa calculation
  - Full calculate() integration (panchanga + ascendant + planets)
"""

import math
from datetime import datetime, timezone

import pytest
import swisseph as swe

from apps.api.domain.ephemeris import (
    Ascendant,
    EphemerisResult,
    NakshatraInfo,
    PanchangaResult,
    SiderealPosition,
    TithiInfo,
    YogaInfo,
    KaranaInfo,
    VaraInfo,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
    _angular_distance,
)
from packages.shared.constants import (
    DEGREES_PER_NAKSHATRA,
    DEGREES_PER_RASHI,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_EPHE_PATH = "data/ephemeris"

@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    """Shared wrapper for all tests — uses Moshier fallback if no .se1 files."""
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


# ── datetime_to_jd ────────────────────────────────────────────────────────────

def test_datetime_to_jd_j2000():
    """
    J2000.0 epoch is 2000-01-01 12:00:00 UTC → JD 2451545.0.
    swe.utc_to_jd introduces a ΔT correction of ~64 seconds (~0.00074 days)
    for dates near J2000.0, so we allow ±5ms tolerance.
    """
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    assert abs(jd - 2451545.0) < 5e-3


def test_datetime_to_jd_requires_timezone():
    dt_naive = datetime(2000, 1, 1, 12, 0, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        datetime_to_jd(dt_naive)


def test_datetime_to_jd_unix_epoch():
    """Unix epoch 1970-01-01 00:00:00 UTC ≈ JD 2440587.5 (±10ms for ΔT)."""
    dt = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    assert abs(jd - 2440587.5) < 0.01


# ── longitude_to_rashi ────────────────────────────────────────────────────────

@pytest.mark.parametrize("lon,expected_rashi,expected_deg_approx", [
    (0.0,   "aries",   0.0),
    (15.0,  "aries",  15.0),
    (30.0,  "taurus",  0.0),
    (59.99, "taurus", 29.99),
    (60.0,  "gemini",  0.0),
    (270.0, "capricorn", 0.0),
    (359.9, "pisces",  29.9),
])
def test_longitude_to_rashi(lon, expected_rashi, expected_deg_approx):
    rashi, deg = longitude_to_rashi(lon)
    assert rashi == expected_rashi
    assert abs(deg - expected_deg_approx) < 0.01


def test_longitude_to_rashi_normalises_360():
    """360° should wrap to Aries 0°."""
    rashi, deg = longitude_to_rashi(360.0)
    assert rashi == "aries"
    assert abs(deg) < 1e-9


def test_longitude_to_rashi_negative_normalises():
    """Negative longitude should be normalised correctly."""
    rashi, deg = longitude_to_rashi(-1.0)
    # -1 mod 360 = 359 → Pisces 29°
    assert rashi == "pisces"
    assert abs(deg - 29.0) < 0.01


# ── longitude_to_nakshatra ────────────────────────────────────────────────────

def test_longitude_to_nakshatra_ashwini():
    """0° sidereal = Ashwini pada 1."""
    info = longitude_to_nakshatra(0.0)
    assert info.nakshatra == "ashwini"
    assert info.nakshatra_number == 1
    assert info.pada == 1
    assert info.lord == "ketu"


def test_longitude_to_nakshatra_revati():
    """The last pada of Revati is just before 360°."""
    info = longitude_to_nakshatra(359.9)
    assert info.nakshatra == "revati"
    assert info.nakshatra_number == 27
    assert info.pada == 4


def test_longitude_to_nakshatra_rohini():
    """Rohini starts at nakshatra 4 → 3 * 13.333° = 40°."""
    start = 3 * DEGREES_PER_NAKSHATRA
    info = longitude_to_nakshatra(start + 0.1)
    assert info.nakshatra == "rohini"
    assert info.nakshatra_number == 4


def test_longitude_to_nakshatra_pada_boundaries():
    """Each pada spans DEGREES_PER_NAKSHATRA / 4."""
    pada_size = DEGREES_PER_NAKSHATRA / 4
    base = 0.0  # Ashwini start
    for pada in range(1, 5):
        lon = base + (pada - 1) * pada_size + 0.001
        info = longitude_to_nakshatra(lon)
        assert info.nakshatra == "ashwini"
        assert info.pada == pada


# ── Angular distance ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("a,b,expected", [
    (0.0, 180.0, 180.0),
    (0.0,  90.0,  90.0),
    (350.0, 10.0,  20.0),
    (10.0, 350.0,  20.0),
    (0.0,   0.0,   0.0),
])
def test_angular_distance(a, b, expected):
    result = _angular_distance(a, b)
    assert abs(result - expected) < 1e-6


# ── Planet positions ──────────────────────────────────────────────────────────

def test_get_sun_position_j2000(wrapper):
    """Sun tropical longitude at J2000.0 should be ≈ 280.46°."""
    pos = wrapper.get_planet_position("sun", 2451545.0)
    assert pos.planet == "sun"
    assert 278.0 <= pos.longitude <= 283.0, f"Unexpected Sun lon: {pos.longitude}"
    assert not pos.is_retrograde


def test_get_moon_position_j2000(wrapper):
    """Moon position should be within 0–360° and non-retrograde."""
    pos = wrapper.get_planet_position("moon", 2451545.0)
    assert 0.0 <= pos.longitude < 360.0
    # Moon speed ~12–15° per day; check it's positive (not retrograde at J2000)
    assert pos.speed_deg_per_day > 0


def test_ketu_is_rahu_plus_180(wrapper):
    """Ketu longitude must equal Rahu + 180°."""
    jd = 2451545.0
    rahu = wrapper.get_planet_position("rahu", jd)
    ketu = wrapper.get_planet_position("ketu", jd)
    expected_ketu = (rahu.longitude + 180.0) % 360.0
    assert abs(ketu.longitude - expected_ketu) < 1e-6


def test_ketu_always_retrograde(wrapper):
    """Ketu should always be marked retrograde."""
    ketu = wrapper.get_planet_position("ketu", 2451545.0)
    assert ketu.is_retrograde is True


def test_get_all_planet_positions_returns_nine(wrapper):
    """All 9 Grahas must be returned."""
    positions = wrapper.get_all_planet_positions(2451545.0)
    expected = {"sun", "moon", "mars", "mercury", "jupiter",
                "venus", "saturn", "rahu", "ketu"}
    assert set(positions.keys()) == expected


# ── Retrograde ────────────────────────────────────────────────────────────────

def test_saturn_retrograde_august_2024(wrapper):
    """Saturn was clearly retrograde throughout August 2024."""
    dt = datetime(2024, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    pos = wrapper.get_planet_position("saturn", jd)
    assert pos.is_retrograde, f"Saturn should be retrograde Aug 2024, speed={pos.speed_deg_per_day}"


def test_mars_not_retrograde_j2000(wrapper):
    """Mars was direct (not retrograde) at J2000.0."""
    pos = wrapper.get_planet_position("mars", 2451545.0)
    assert not pos.is_retrograde


# ── Combustion ────────────────────────────────────────────────────────────────

def test_combust_mercury_close_to_sun(wrapper):
    """Mercury within 10° of Sun should be combust."""
    sun_lon = 341.0
    mercury_lon = 344.0   # 3° from Sun — well within 14° orb
    combust, orb = wrapper.is_combust("mercury", mercury_lon, sun_lon)
    assert combust is True
    assert orb is not None and orb < 14.0


def test_not_combust_mercury_far_from_sun(wrapper):
    """Mercury 90° from Sun should not be combust."""
    combust, orb = wrapper.is_combust("mercury", 180.0, 90.0)
    assert combust is False


def test_sun_never_combust(wrapper):
    """Sun cannot be combust with itself."""
    combust, orb = wrapper.is_combust("sun", 0.0, 0.0)
    assert combust is False
    assert orb is None


def test_rahu_never_combust(wrapper):
    """Rahu is never considered combust."""
    combust, orb = wrapper.is_combust("rahu", 0.0, 0.0)
    assert combust is False


# ── Ayanamsa ─────────────────────────────────────────────────────────────────

def test_ayanamsa_j2000_lahiri(wrapper):
    """Lahiri ayanamsa at J2000.0 should be ≈ 23.85°."""
    val = wrapper.get_ayanamsa(2451545.0)
    assert 23.0 <= val <= 24.5, f"Unexpected Lahiri ayanamsa: {val}"


# ── Tithi ─────────────────────────────────────────────────────────────────────
# Tithi formula: diff = (Moon - Sun) mod 360; tithi = floor(diff / 12) + 1
# Tithi boundaries: Tithi N occupies [12*(N-1), 12*N)
# At exactly 180°: floor(180/12)+1 = 15+1 = 16  → first tithi of Krishna Paksha

def test_tithi_late_shukla_14():
    """Moon 168° ahead of Sun → Tithi 15 (Chaturdashi, still shukla)."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = wrapper.get_tithi(moon_lon=168.0, sun_lon=0.0)
    assert tithi.number == 15
    assert tithi.paksha == "shukla"


def test_tithi_krishna_1_at_180():
    """
    Moon exactly 180° ahead of Sun → Tithi 16.
    180° is the boundary: Purnima ends at 180°, Krishna Pratipada begins.
    """
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = wrapper.get_tithi(moon_lon=180.0, sun_lon=0.0)
    assert tithi.number == 16
    assert tithi.paksha == "krishna"


def test_tithi_amavasya():
    """Moon ≈ 348° ahead of Sun → tithi 30 (Amavasya)."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = wrapper.get_tithi(moon_lon=348.0, sun_lon=0.0)
    assert tithi.number == 30


def test_tithi_number_range():
    """Tithi must always be between 1 and 30."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    for diff in range(0, 360, 12):
        tithi = wrapper.get_tithi(moon_lon=float(diff), sun_lon=0.0)
        assert 1 <= tithi.number <= 30


def test_tithi_shukla_paksha():
    """Tithis 1–15 are Shukla Paksha; 24° diff → Tithi 3 (floor(24/12)+1=3)."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = wrapper.get_tithi(moon_lon=24.0, sun_lon=0.0)
    assert tithi.paksha == "shukla"
    assert tithi.number == 3


def test_tithi_krishna_paksha():
    """Tithis 16–30 are Krishna Paksha."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = wrapper.get_tithi(moon_lon=192.0, sun_lon=0.0)
    assert tithi.paksha == "krishna"


# ── Yoga ─────────────────────────────────────────────────────────────────────

def test_yoga_number_range():
    """Yoga number must be 1–27."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    for sun in range(0, 360, 30):
        for moon in range(0, 360, 30):
            yoga = wrapper.get_yoga(float(moon), float(sun))
            assert 1 <= yoga.number <= 27


def test_yoga_vishkambha():
    """0° + 0° → combined = 0° → Vishkambha (yoga 1)."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    yoga = wrapper.get_yoga(0.0, 0.0)
    assert yoga.number == 1
    assert yoga.name == "Vishkambha"


# ── Karana ────────────────────────────────────────────────────────────────────

def test_karana_first_is_kimstughna():
    """First Karana of tithi 1 is Kimstughna (fixed)."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = TithiInfo(number=1, name="Pratipada", paksha="shukla", completion_percent=10.0)
    karana = wrapper.get_karana(tithi)
    assert karana.name == "Kimstughna"
    assert karana.is_fixed is True


def test_karana_second_half_tithi1():
    """Second half of Pratipada → movable Bava."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    tithi = TithiInfo(number=1, name="Pratipada", paksha="shukla", completion_percent=60.0)
    karana = wrapper.get_karana(tithi)
    assert karana.name == "Bava"
    assert karana.is_fixed is False


# ── Vara ──────────────────────────────────────────────────────────────────────

def test_vara_j2000_is_saturday():
    """J2000.0 (2000-01-01) was a Saturday."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    vara = wrapper.get_vara(2451545.0)
    assert vara.name == "Saturday"
    assert vara.lord == "saturn"


def test_vara_number_range():
    """Vara number must be 0–6."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    for offset in range(7):
        vara = wrapper.get_vara(2451545.0 + offset)
        assert 0 <= vara.number <= 6


# ── Full calculate() integration ──────────────────────────────────────────────

def test_calculate_returns_ephemeris_result():
    """calculate() must return an EphemerisResult with all fields populated."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    dt = datetime(2000, 1, 1, 5, 30, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=28.6139, longitude=77.2090)

    assert isinstance(result, EphemerisResult)
    assert result.julian_day > 0
    assert 0.0 < result.ayanamsa_value < 30.0
    assert isinstance(result.ascendant, Ascendant)
    assert len(result.house_cusps) == 12
    assert len(result.planet_positions) == 9
    assert isinstance(result.panchanga, PanchangaResult)


def test_calculate_all_nine_planets_present():
    """calculate() must include all 9 Grahas."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    dt = datetime(1990, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=19.0760, longitude=72.8777)

    planet_names = {p.planet for p in result.planet_positions}
    expected = {"sun", "moon", "mars", "mercury", "jupiter",
                "venus", "saturn", "rahu", "ketu"}
    assert planet_names == expected


def test_calculate_house_numbers_are_1_to_12():
    """Every planet's house_number must be between 1 and 12."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    dt = datetime(1985, 3, 20, 8, 0, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=13.0827, longitude=80.2707)

    for p in result.planet_positions:
        assert 1 <= p.house_number <= 12, f"{p.planet} has invalid house {p.house_number}"


def test_calculate_lagna_rashi_is_valid():
    """Ascendant rashi must be one of the 12 signs."""
    _VALID_RASHIS = {
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    }
    wrapper = EphemerisWrapper(_EPHE_PATH)
    dt = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=51.5074, longitude=-0.1278)

    assert result.ascendant.rashi in _VALID_RASHIS


def test_calculate_panchanga_tithi_in_range():
    """Tithi must be 1–30 in any full calculation."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    dt = datetime(2023, 10, 14, 12, 0, 0, tzinfo=timezone.utc)
    result = wrapper.calculate(dt=dt, latitude=0.0, longitude=0.0)

    assert 1 <= result.panchanga.tithi.number <= 30


def test_calculate_kp_ayanamsa():
    """calculate() must work with KP ayanamsa and produce a different ayanamsa value."""
    wrapper = EphemerisWrapper(_EPHE_PATH)
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    result_lahiri = wrapper.calculate(dt=dt, latitude=0.0, longitude=0.0, ayanamsa="lahiri")
    result_kp = wrapper.calculate(dt=dt, latitude=0.0, longitude=0.0, ayanamsa="kp")

    # KP and Lahiri ayanamsa values differ slightly
    assert abs(result_lahiri.ayanamsa_value - result_kp.ayanamsa_value) > 0.001
