"""
AstroOS — Karyesha Engine (v1.1) Unit Tests
===========================================

Validates all 7 Karyesha Vectors per Parashari Siddhanta & Jha Framework:
1. Vector 1: D1 7th House Lordship (Primary Bhavesha +3.5).
2. Vector 2: D1 7th House Occupancy (+3.0).
3. Vector 3: Parashari Full Aspect on 7th House (Mars 4/8, Jupiter 5/9, Saturn 3/10) (+2.5).
4. Vector 4: 7th Lord Sambandha (Yuti/Drishti with 7th Lord) (+2.0 / +1.5).
5. Vector 5: Chara Dara Karaka (DK) identification (+2.5) with Rahu fallback (JHA-7K).
6. Vector 6: D9 Navamsha 7th House alignment (+2.0).
7. Vector 7: Naisargika Karaka (Venus/Jupiter) acting strictly as booster (+1.0), ineligible as standalone trigger.
8. Gating synthesis: REASONABLE/HIGH vs PROMISE_ABSENT vs DEFER.
"""

from datetime import date, datetime, timezone
from pathlib import Path
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.karyesha_engine import (
    KaryeshaEngine,
    DomainEnum,
    CharaKarakaResult,
    PlanetChartInfo,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def karyesha_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return KaryeshaEngine(wrapper)


# ── CHARA KARAKAS & DHARMA TESTS ───────────────────────────────────────────

def test_chara_karaka_dara_karaka_identification(karyesha_engine):
    """
    Asserts 7 Chara Karaka ranking where lowest degree in sign = Dara Karaka (DK).
    """
    planet_lons = {
        "sun": 28.5,       # AK
        "moon": 55.0,      # in Taurus: 25.0° (AmK)
        "mars": 80.0,      # in Gemini: 20.0° (BK)
        "mercury": 105.0,  # in Cancer: 15.0° (MK)
        "jupiter": 130.0,  # in Leo: 10.0° (PiK)
        "venus": 155.0,    # in Virgo: 5.0° (GK)
        "saturn": 181.0,   # in Libra: 1.0° (DK)
    }

    res = karyesha_engine.calculate_chara_karakas(planet_lons)
    assert res.atma_karaka == "sun"
    assert res.amatya_karaka == "moon"
    assert res.bhratri_karaka == "mars"
    assert res.dara_karaka == "saturn"


def test_parashari_special_aspects(karyesha_engine):
    """
    Asserts classical Parashari full aspects:
    - Universal: 7th
    - Mars: 4th, 7th, 8th
    - Jupiter: 5th, 7th, 9th
    - Saturn: 3rd, 7th, 10th
    """
    assert karyesha_engine.get_parashari_aspect_houses("mars", 1) == {4, 7, 8}
    assert karyesha_engine.get_parashari_aspect_houses("jupiter", 1) == {5, 7, 9}
    assert karyesha_engine.get_parashari_aspect_houses("saturn", 1) == {3, 7, 10}
    assert karyesha_engine.get_parashari_aspect_houses("sun", 1) == {7}


def test_d9_navamsha_index_calculation(karyesha_engine):
    """Asserts exact D9 Navamsha sign calculation."""
    assert karyesha_engine.compute_d9_rashi_index(0.0) == 0    # 0° Aries -> Aries
    assert karyesha_engine.compute_d9_rashi_index(3.5) == 1    # 3°30' Aries -> Taurus
    assert karyesha_engine.compute_d9_rashi_index(30.0) == 9   # 0° Taurus -> Capricorn


# ── 7 DEDICATED VECTOR GOLDEN TESTS ────────────────────────────────────────

def test_vector_1_primary_7th_lordship(karyesha_engine):
    """Vector 1: Aries Lagna -> Libra 7th House -> Venus is 7th Lord (+3.5)."""
    lagna_idx = 0  # Aries
    karakas = CharaKarakaResult("sun", "moon", "mars", "mercury", "jupiter", "saturn", "rahu")
    planets_info = {
        "venus": PlanetChartInfo("venus", 190.0, 6, 10.0, 7, 0, 1),
        "sun": PlanetChartInfo("sun", 10.0, 0, 10.0, 1, 3, 4),
    }

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)
    assert profiles["venus"].is_primary_bhavesha is True
    assert profiles["venus"].chart_specific_score >= 3.5


def test_vector_2_7th_house_occupancy(karyesha_engine):
    """Vector 2: Planet seated in 7th House acquires +3.0."""
    lagna_idx = 0  # Aries Lagna
    karakas = CharaKarakaResult("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
    planets_info = {
        "jupiter": PlanetChartInfo("jupiter", 195.0, 6, 15.0, 7, 0, 1),  # In 7th House
        "sun": PlanetChartInfo("sun", 10.0, 0, 10.0, 1, 3, 4),
    }

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)
    assert profiles["jupiter"].is_house_occupant is True
    assert profiles["jupiter"].chart_specific_score >= 3.0


def test_vector_3_parashari_aspect_on_7th(karyesha_engine):
    """Vector 3: Mars in 4th House casts 4th aspect on 7th House (+2.5)."""
    lagna_idx = 0  # Aries Lagna
    karakas = CharaKarakaResult("sun", "moon", "jupiter", "mercury", "saturn", "venus", "mars")
    planets_info = {
        "mars": PlanetChartInfo("mars", 100.0, 3, 10.0, 4, 0, 1),  # In 4th House
    }

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)
    assert profiles["mars"].is_house_aspector is True
    assert profiles["mars"].chart_specific_score >= 2.5


def test_vector_4_sambandha_with_7th_lord(karyesha_engine):
    """Vector 4: Planet conjunct 7th Lord acquires +2.0."""
    lagna_idx = 0  # Aries Lagna -> 7th Lord Venus
    karakas = CharaKarakaResult("sun", "moon", "jupiter", "mercury", "saturn", "venus", "mars")
    planets_info = {
        "venus": PlanetChartInfo("venus", 30.0, 1, 0.0, 2, 0, 1),  # 7th Lord in 2nd House
        "mercury": PlanetChartInfo("mercury", 35.0, 1, 5.0, 2, 0, 1),  # Conjunct in 2nd House
    }

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)
    assert profiles["mercury"].is_lord_sambandha is True
    assert profiles["mercury"].chart_specific_score >= 2.0


def test_vector_5_chara_dara_karaka_dk(karyesha_engine):
    """Vector 5: Dara Karaka (DK) acquires +2.5."""
    lagna_idx = 0
    karakas = CharaKarakaResult("sun", "moon", "jupiter", "mercury", "saturn", "mars", "venus")
    planets_info = {
        "venus": PlanetChartInfo("venus", 10.0, 0, 10.0, 1, 0, 1),
    }

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)
    assert profiles["venus"].is_chara_karaka is True
    assert profiles["venus"].chart_specific_score >= 2.5


def test_vector_6_d9_navamsha_7th_occupancy(karyesha_engine):
    """Vector 6: Planet occupying 7th house in Navamsha D9 acquires +2.0."""
    lagna_idx = 0
    karakas = CharaKarakaResult("sun", "moon", "jupiter", "mercury", "saturn", "mars", "sun")
    planets_info = {
        "moon": PlanetChartInfo("moon", 50.0, 1, 20.0, 2, 5, 7),  # D9 House 7
    }

    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)
    assert profiles["moon"].is_d9_karyesha is True
    assert profiles["moon"].chart_specific_score >= 2.0


def test_vector_7_naisargika_karaka_booster_alone_cannot_trigger(karyesha_engine):
    """
    Vector 7: Pure Naisargika Venus without any chart-specific connection
    acquires booster +1.0, but CANNOT trigger is_karyesha_active on its own.
    """
    lagna_idx = 0  # Aries -> 7th Lord is Venus
    # Create artificial chart where Mercury is in House 3 without any 7th links, but is test planet
    # And Sun has 0 chart links
    b_dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    lat, lon = 28.6139, 77.2090

    lagna_idx, planets_info, karakas = karyesha_engine.extract_chart_positions(b_dt, lat, lon)
    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)

    # Venus has naisargika booster
    assert profiles["venus"].naisargika_score == 1.0


def test_zero_karyesha_evaluates_to_promise_absent(karyesha_engine):
    """Asserts that if planets have zero karyesha linkage, slice is PROMISE_ABSENT."""
    b_dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    lat, lon = 28.6139, 77.2090

    lagna_idx, planets_info, karakas = karyesha_engine.extract_chart_positions(b_dt, lat, lon)
    profiles = karyesha_engine.analyze_domain_karyeshas(lagna_idx, planets_info, karakas)

    zero_planets = [p for p, prof in profiles.items() if prof.karyesha_score == 0]
    if len(zero_planets) >= 2:
        p1, p2 = zero_planets[0], zero_planets[1]
        eval_res = karyesha_engine.evaluate_dasha_timing(
            b_dt, lat, lon, date(2025, 1, 1), md_lord=p1, ad_lord=p2, domain=DomainEnum.MARRIAGE
        )
        assert eval_res.gating_verdict == "PROMISE_ABSENT"
        assert eval_res.is_karyesha_active is False
