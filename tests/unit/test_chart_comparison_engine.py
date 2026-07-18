"""
AstroOS — ChartComparisonEngine Unit Tests (Phase E)
"""

from __future__ import annotations

import pytest

from apps.api.domain.ai_phase_e import ChartComparisonResult, ComparisonDimension
from apps.api.domain.ephemeris import Ascendant, DignityType, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.services.chart_comparison_engine import ChartComparisonEngine


def _make_chart(
    asc_rashi: str = "aries",
    asc_deg: float = 10.0,
    sun_rashi: str = "aries",
    sun_house: int = 1,
    sun_retrograde: bool = False,
    moon_rashi: str = "taurus",
    moon_house: int = 2,
) -> D1Chart:
    planets = [
        SiderealPosition(planet="sun", sidereal_longitude=10.0, rashi=sun_rashi,
            rashi_degree=10.0, house_number=sun_house, nakshatra="ashwini", pada=1,
            is_retrograde=sun_retrograde, is_combust=False, combustion_orb=None,
            dignity=DignityType.OWN),
        SiderealPosition(planet="moon", sidereal_longitude=40.0, rashi=moon_rashi,
            rashi_degree=10.0, house_number=moon_house, nakshatra="rohini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="mars", sidereal_longitude=100.0, rashi="cancer",
            rashi_degree=10.0, house_number=5, nakshatra="pushya", pada=2,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.EXALTED),
        SiderealPosition(planet="jupiter", sidereal_longitude=200.0, rashi="libra",
            rashi_degree=15.0, house_number=7, nakshatra="swati", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="venus", sidereal_longitude=300.0, rashi="capricorn",
            rashi_degree=5.0, house_number=10, nakshatra="uttara ashadha", pada=4,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.OWN),
        SiderealPosition(planet="saturn", sidereal_longitude=350.0, rashi="pisces",
            rashi_degree=20.0, house_number=12, nakshatra="revati", pada=3,
            is_retrograde=True, is_combust=False, combustion_orb=None,
            dignity=DignityType.DEBILITATED),
    ]
    asc = Ascendant(longitude=10.0, sidereal_longitude=10.0, rashi=asc_rashi,
                    rashi_degree=asc_deg, nakshatra="ashwini", pada=1)
    houses = [HouseCusp(house_number=n, longitude=float(n * 30),
                        sidereal_longitude=float(n * 30), rashi="")
              for n in range(1, 13)]
    return D1Chart(ephemeris=None, ascendant=asc, houses=houses, planets=planets,
                   aspects=[], planet_strengths=[], panchanga=None,
                   ayanamsa_system="lahiri", house_system="W")


def _make_yogas(present_ids: set[str]) -> list[YogaResult]:
    """Create yoga results with specified IDs present."""
    all_yogas = [
        ("BPHS-RJ-001", "Raja Yoga", "raja"),
        ("BPHS-DH-001", "Dhana Yoga", "dhana"),
        ("BPHS-PM-001", "Ruchaka", "panch_mahapurusha"),
        ("BPHS-GK-001", "Gajakesari", "classical"),
    ]
    results = []
    for yid, name, cat in all_yogas:
        results.append(YogaResult(
            yoga_id=yid, name=name, category=cat,
            source_text="BPHS", rule_version="1.0",
            is_present=yid in present_ids,
            strength="full" if yid in present_ids else None,
            involved_planets=("mars",) if yid in present_ids else (),
            involved_houses=(1,) if yid in present_ids else (),
        ))
    return results


class TestCompare:
    def test_identical_charts(self):
        chart_a = _make_chart()
        chart_b = _make_chart()
        result = ChartComparisonEngine.compare(chart_a, chart_b)
        assert isinstance(result, ChartComparisonResult)
        assert result.overall_similarity >= 0.9  # very high for identical
        assert len(result.key_similarities) > 0
        assert len(result.key_differences) == 0

    def test_different_ascendants(self):
        # Rashi at maximum distance (aries vs libra) alone lands exactly on
        # the 0.4 "difference" boundary (rashi_sim=0, deg_sim=1.0 when the
        # degree is left equal) — also vary the degree so the two charts are
        # unambiguously different, not sitting on the threshold.
        chart_a = _make_chart(asc_rashi="aries", asc_deg=5.0)
        chart_b = _make_chart(asc_rashi="libra", asc_deg=25.0)
        result = ChartComparisonEngine.compare(chart_a, chart_b)
        asc_dims = [d for d in result.key_differences if d.dimension == "ascendant"]
        assert len(asc_dims) > 0
        assert asc_dims[0].similarity < 0.4

    def test_different_planet_placements(self):
        # Rashi + house both maximally different still only reaches exactly
        # the 0.4 boundary (degree/dignity/retrograde weights are fixed
        # equal at 0.4 combined) — also flip retrograde so Sun is
        # unambiguously below the "difference" threshold.
        chart_a = _make_chart(sun_rashi="aries", sun_house=1, sun_retrograde=False)
        chart_b = _make_chart(sun_rashi="libra", sun_house=7, sun_retrograde=True)
        result = ChartComparisonEngine.compare(chart_a, chart_b)
        sun_dims = [d for d in result.key_differences if d.dimension == "planet.sun"]
        assert any(d.similarity < 0.5 for d in sun_dims)

    def test_with_yoga_comparison(self):
        chart_a = _make_chart()
        chart_b = _make_chart()
        yogas_a = _make_yogas({"BPHS-RJ-001", "BPHS-GK-001"})
        yogas_b = _make_yogas({"BPHS-RJ-001", "BPHS-DH-001"})
        result = ChartComparisonEngine.compare(
            chart_a, chart_b, yogas_a=yogas_a, yogas_b=yogas_b,
        )
        # Should have yoga dimensions.
        yoga_dims = [d for d in result.key_differences if d.dimension.startswith("yoga.")]
        assert len(yoga_dims) > 0

    def test_same_yogas(self):
        chart_a = _make_chart()
        chart_b = _make_chart()
        yogas = _make_yogas({"BPHS-RJ-001", "BPHS-GK-001"})
        result = ChartComparisonEngine.compare(
            chart_a, chart_b, yogas_a=yogas, yogas_b=yogas,
        )
        yoga_dims = [d for d in result.key_similarities if d.dimension.startswith("yoga.")]
        assert len(yoga_dims) > 0

    def test_compatibility_notes_generated(self):
        chart_a = _make_chart()
        chart_b = _make_chart()
        result = ChartComparisonEngine.compare(chart_a, chart_b)
        assert len(result.compatibility_notes) > 0
        assert len(result.relationship_potential) > 0
        assert len(result.timing_synergies) > 0

    def test_different_charts_have_differences(self):
        # Rashi-only variation (degree left equal) keeps the ascendant right
        # at the 0.4 "difference" boundary — vary the degree too so at least
        # one dimension is unambiguously counted as a key difference.
        chart_a = _make_chart(asc_rashi="aries", asc_deg=5.0, moon_rashi="taurus")
        chart_b = _make_chart(asc_rashi="sagittarius", asc_deg=25.0, moon_rashi="scorpio")
        result = ChartComparisonEngine.compare(chart_a, chart_b)
        assert len(result.key_differences) > 0
        assert result.overall_similarity < 0.9


class TestComparisonDimension:
    def test_dimension_fields(self):
        dim = ComparisonDimension(
            dimension="planet.mars",
            chart_a_value="Aries H1",
            chart_b_value="Cancer H5",
            similarity=0.2,
            significance="medium",
            commentary="Mars is placed differently.",
        )
        assert dim.dimension == "planet.mars"
        assert dim.similarity == 0.2
        assert dim.significance == "medium"

    def test_default_commentary(self):
        dim = ComparisonDimension(
            dimension="test", chart_a_value="A", chart_b_value="B",
            similarity=0.5, significance="low",
        )
        assert dim.commentary == ""