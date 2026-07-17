"""
AstroOS — Ashtakavarga Engine Unit Tests (Module 10)
"""

import pytest

from apps.api.domain.ephemeris import Ascendant, DignityType, SiderealPosition
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine

_ALL_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


def _make_planet(planet, rashi):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi=rashi, rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _make_chart(rashi_by_planet, lagna_rashi):
    class _FakeChart:
        pass

    chart = _FakeChart()
    chart.planets = [_make_planet(p, r) for p, r in rashi_by_planet.items()]
    chart.ascendant = Ascendant(
        longitude=0.0, sidereal_longitude=0.0, rashi=lagna_rashi, rashi_degree=0.0,
        nakshatra="ashwini", pada=1,
    )
    return chart


def test_compute_bhinnashtakavarga_returns_7_results_with_correct_totals():
    chart = _make_chart({p: "leo" for p in _ALL_PLANETS}, lagna_rashi="cancer")
    engine = AshtakavargaEngine()
    results = engine.compute_bhinnashtakavarga(chart)
    assert len(results) == 7
    totals = {r.target_planet: r.total_bindus for r in results}
    assert totals == {
        "sun": 48, "moon": 49, "mars": 39, "mercury": 54,
        "jupiter": 56, "venus": 52, "saturn": 39,
    }


def test_compute_sarvashtakavarga_totals_337():
    chart = _make_chart({p: "libra" for p in _ALL_PLANETS}, lagna_rashi="aries")
    engine = AshtakavargaEngine()
    sav = engine.compute_sarvashtakavarga(chart)
    assert sav.total_bindus == 337


def test_verify_checksum_true_for_any_valid_chart():
    chart = _make_chart({p: "sagittarius" for p in _ALL_PLANETS}, lagna_rashi="gemini")
    engine = AshtakavargaEngine()
    assert engine.verify_checksum(chart) is True


def test_sarvashtakavarga_equals_sum_of_bhinnashtakavargas_per_rashi():
    chart = _make_chart({p: "capricorn" for p in _ALL_PLANETS}, lagna_rashi="virgo")
    engine = AshtakavargaEngine()
    bhinnas = engine.compute_bhinnashtakavarga(chart)
    sav = engine.compute_sarvashtakavarga(chart)
    for i in range(12):
        expected = sum(b.bindus_by_rashi[i] for b in bhinnas)
        assert sav.bindus_by_rashi[i] == expected


def test_ignores_rahu_ketu_as_contributors():
    chart_with_nodes = _make_chart({p: "aries" for p in _ALL_PLANETS}, lagna_rashi="aries")
    chart_without_nodes = _make_chart(
        {p: "aries" for p in _ALL_PLANETS if p not in ("rahu", "ketu")}, lagna_rashi="aries"
    )
    engine = AshtakavargaEngine()
    sav_with = engine.compute_sarvashtakavarga(chart_with_nodes)
    sav_without = engine.compute_sarvashtakavarga(chart_without_nodes)
    assert sav_with.bindus_by_rashi == sav_without.bindus_by_rashi


def test_checksum_holds_across_many_random_configurations():
    rashis_options = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    engine = AshtakavargaEngine()
    for seed in range(5):
        rashi_by_planet = {
            p: rashis_options[(i + seed) % 12] for i, p in enumerate(_ALL_PLANETS)
        }
        lagna = rashis_options[seed % 12]
        chart = _make_chart(rashi_by_planet, lagna)
        assert engine.verify_checksum(chart) is True


def test_compute_reduced_bhinnashtakavarga_returns_7_planets():
    chart = _make_chart({p: "leo" for p in _ALL_PLANETS}, lagna_rashi="cancer")
    engine = AshtakavargaEngine()
    reduced = engine.compute_reduced_bhinnashtakavarga(chart)
    assert len(reduced) == 7
    assert {r.target_planet for r in reduced} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }


def test_reduced_totals_never_exceed_unreduced_totals():
    """Reduction only ever removes bindus, never adds — a basic sanity invariant."""
    chart = _make_chart(
        {"sun": "aries", "moon": "taurus", "mars": "gemini", "mercury": "cancer",
         "jupiter": "leo", "venus": "virgo", "saturn": "libra",
         "rahu": "scorpio", "ketu": "sagittarius"},
        lagna_rashi="capricorn",
    )
    engine = AshtakavargaEngine()
    unreduced = {r.target_planet: r.total_bindus for r in engine.compute_bhinnashtakavarga(chart)}
    reduced = {r.target_planet: r.total_bindus for r in engine.compute_reduced_bhinnashtakavarga(chart)}
    for planet in unreduced:
        assert reduced[planet] <= unreduced[planet]


def test_reduced_values_never_negative():
    chart = _make_chart(
        {"sun": "aries", "moon": "taurus", "mars": "gemini", "mercury": "cancer",
         "jupiter": "leo", "venus": "virgo", "saturn": "libra",
         "rahu": "scorpio", "ketu": "sagittarius"},
        lagna_rashi="pisces",
    )
    engine = AshtakavargaEngine()
    for result in engine.compute_reduced_bhinnashtakavarga(chart):
        assert all(v >= 0 for v in result.bindus_by_rashi)
