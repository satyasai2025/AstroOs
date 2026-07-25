"""
AstroOS — EnhancedQAResponder Unit Tests (Phase E)
"""

from __future__ import annotations

from datetime import date

import pytest

from apps.api.domain.ai import AIResponse
from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.ephemeris import Ascendant, DignityType, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.yoga import YogaResult
from apps.api.services.enhanced_qa_engine import EnhancedQAResponder


def _make_chart() -> D1Chart:
    planets = [
        SiderealPosition(planet="sun", sidereal_longitude=10.0, rashi="aries",
            rashi_degree=10.0, house_number=1, nakshatra="ashwini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.OWN),
        SiderealPosition(planet="moon", sidereal_longitude=40.0, rashi="taurus",
            rashi_degree=10.0, house_number=2, nakshatra="rohini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="mars", sidereal_longitude=100.0, rashi="cancer",
            rashi_degree=10.0, house_number=5, nakshatra="pushya", pada=2,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.EXALTED),
        SiderealPosition(planet="jupiter", sidereal_longitude=200.0, rashi="libra",
            rashi_degree=15.0, house_number=7, nakshatra="swati", pada=3,
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
    asc = Ascendant(longitude=10.0, sidereal_longitude=10.0, rashi="aries",
                    rashi_degree=10.0, nakshatra="ashwini", pada=1)
    houses = [HouseCusp(house_number=n, longitude=float(n * 30),
                        sidereal_longitude=float(n * 30), rashi="")
              for n in range(1, 13)]
    return D1Chart(ephemeris=None, ascendant=asc, houses=houses, planets=planets,
                   aspects=[], planet_strengths=[], panchanga=None,
                   ayanamsa_system="lahiri", house_system="W")


def _make_dasha_tree() -> DashaTree:
    sub = DashaPeriod(lord="sun", start_date=date(2020, 1, 1), end_date=date(2030, 1, 1),
                      duration_days=3653, level=2, sub_periods=())
    md = DashaPeriod(lord="venus", start_date=date(2000, 1, 1), end_date=date(2020, 1, 1),
                     duration_days=7305, level=1, sub_periods=[sub])
    return DashaTree(system="vimshottari", birth_date=date(1990, 1, 1),
                     trigger_planet="moon", trigger_nakshatra="rohini",
                     trigger_nakshatra_number=4, mahadashas=[md],
                     max_depth=2, total_cycle_years=120)


def _make_yogas() -> list[YogaResult]:
    return [
        YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="panch_mahapurusha",
                   source_text="BPHS", rule_version="1.0", is_present=True,
                   strength="full", involved_planets=("mars",), involved_houses=(1,)),
        YogaResult(yoga_id="BPHS-RJ-001", name="Raja Yoga", category="raja",
                   source_text="BPHS", rule_version="1.0", is_present=True,
                   strength="partial", involved_planets=("mars", "jupiter"), involved_houses=(1, 7)),
    ]


def _make_transits() -> list[TransitPlanetResult]:
    return [
        TransitPlanetResult(planet="saturn", transit_rashi="aquarius", house_from_natal_moon=8,
                            ashtakavarga_bindus=3, is_sade_sati=False, is_ashtama_shani=True),
        TransitPlanetResult(planet="jupiter", transit_rashi="pisces", house_from_natal_moon=12,
                            ashtakavarga_bindus=4, is_sade_sati=False, is_ashtama_shani=False),
    ]


class TestEnhancedQAResponder:
    def test_no_chart(self):
        result = EnhancedQAResponder.generate("Where is the Sun?")
        assert "Chart data is required" in result.body

    def test_ascendant_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What is the lagna?", chart)
        assert "aries" in result.body.lower()

    def test_planet_question_sun(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Tell me about the Sun", chart)
        assert "Sun" in result.body
        assert "aries" in result.body.lower()

    def test_planet_question_moon(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Where is Chandra?", chart)
        assert "Moon" in result.body

    def test_planet_question_jupiter(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What about Guru?", chart)
        assert "Jupiter" in result.body

    def test_yoga_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What yogas are present?", chart,
                                              yogas=_make_yogas())
        assert "Ruchaka" in result.body
        assert "Raja Yoga" in result.body

    def test_dasha_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What is the current dasha?", chart,
                                              dasha_tree=_make_dasha_tree())
        assert "dasha" in result.body.lower() or "period" in result.body.lower()
        assert "Sun" in result.body

    def test_transit_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Tell me about transits", chart,
                                              transits=_make_transits())
        assert "saturn" in result.body.lower() or "jupiter" in result.body.lower()

    def test_sade_sati_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Is Sade Sati active?", chart,
                                              transits=_make_transits())
        assert "Ashtama Shani" in result.body

    def test_strength_question(self):
        chart = _make_chart()
        shadbala = {"sun": 6.5, "moon": 4.2, "mars": 7.1, "mercury": 3.0,
                    "jupiter": 5.8, "venus": 6.0, "saturn": 2.5}
        result = EnhancedQAResponder.generate("How strong are the planets?", chart,
                                               shadbala_totals=shadbala)
        assert "Shadbala" in result.body or "Rupas" in result.body

    def test_retrograde_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Which planets are retrograde?", chart)
        assert "Saturn" in result.body
        assert "No planets" not in result.body

    def test_combustion_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Are any planets combust?", chart)
        assert "No planets" in result.body

    def test_aspect_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What aspects are there?", chart)
        assert "No aspect data" in result.body

    def test_house_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Tell me about house 1", chart)
        assert "House 1" in result.body

    def test_dignity_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Tell me about dignities", chart)
        assert "Exalted" in result.body or "Debilitated" in result.body

    def test_nakshatra_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What about nakshatras?", chart)
        assert "nakshatra" in result.body.lower()

    def test_general_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What can you tell me?", chart)
        assert "answer questions" in result.body.lower()

    def test_unknown_planet_question(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Tell me about Pluto", chart)
        assert "Which planet" in result.body

    def test_custom_names(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("Where is Mangal?", chart)
        assert "Mars" in result.body

    def test_version_is_2(self):
        chart = _make_chart()
        result = EnhancedQAResponder.generate("What is the ascendant?", chart)
        assert result.version == "2.0"