"""
Unit tests for TripleDashaConfluenceEngine (Vimshottari + Sudarshana + Jaimini Chara Dasha).
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.domain.ephemeris import (
    Ascendant,
    EphemerisResult,
    HouseCusp,
    NakshatraInfo,
    PanchangaResult,
    SiderealPosition,
    TithiInfo,
    VaraInfo,
    YogaInfo,
    KaranaInfo,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.services.triple_dasha_confluence_engine import (
    TripleDashaConfluenceEngine,
    TripleDashaWindowConfluence,
)


def _make_mock_chart(lagna_rashi: str = "aries") -> D1Chart:
    planets = (
        SiderealPosition(planet="sun", sidereal_longitude=125.0, rashi="leo", rashi_degree=5.0, house_number=5, nakshatra="magha", pada=2, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="moon", sidereal_longitude=215.0, rashi="scorpio", rashi_degree=5.0, house_number=8, nakshatra="anuradha", pada=1, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="mars", sidereal_longitude=220.0, rashi="scorpio", rashi_degree=10.0, house_number=8, nakshatra="anuradha", pada=3, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="mercury", sidereal_longitude=140.0, rashi="virgo", rashi_degree=20.0, house_number=6, nakshatra="hasta", pada=4, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="jupiter", sidereal_longitude=95.0, rashi="cancer", rashi_degree=5.0, house_number=4, nakshatra="pushya", pada=1, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="venus", sidereal_longitude=165.0, rashi="virgo", rashi_degree=15.0, house_number=6, nakshatra="hasta", pada=2, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="saturn", sidereal_longitude=130.0, rashi="leo", rashi_degree=10.0, house_number=5, nakshatra="magha", pada=4, is_retrograde=False, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="rahu", sidereal_longitude=340.0, rashi="pisces", rashi_degree=10.0, house_number=12, nakshatra="uttarabhadra", pada=3, is_retrograde=True, is_combust=False, combustion_orb=None, dignity=None),
        SiderealPosition(planet="ketu", sidereal_longitude=160.0, rashi="virgo", rashi_degree=10.0, house_number=6, nakshatra="hasta", pada=1, is_retrograde=True, is_combust=False, combustion_orb=None, dignity=None),
    )
    asc = Ascendant(
        longitude=10.0,
        sidereal_longitude=10.0,
        rashi=lagna_rashi,
        rashi_degree=10.0,
        nakshatra="ashwini",
        pada=4,
        nakshatra_lord="ketu",
        sub_lord="saturn",
    )
    houses = tuple(HouseCusp(house_number=i, longitude=(i - 1) * 30.0, sidereal_longitude=(i - 1) * 30.0, rashi="aries") for i in range(1, 13))
    panchanga = PanchangaResult(
        tithi=TithiInfo(number=1, name="Pratipada", paksha="shukla", completion_percent=50.0),
        nakshatra=NakshatraInfo(nakshatra="Ashwini", nakshatra_number=1, pada=1, lord="Ketu", degree_in_nakshatra=5.0, degree_in_pada=1.0),
        yoga=YogaInfo(number=1, name="Vishkambha", completion_percent=50.0),
        karana=KaranaInfo(number=1, name="Bava", is_fixed=False),
        vara=VaraInfo(number=1, name="Ravivara", lord="sun"),
        julian_day=2451545.0,
        ayanamsa_deg=23.85,
    )
    eph = EphemerisResult(
        julian_day=2451545.0,
        ayanamsa_value=23.85,
        ayanamsa_system="lahiri",
        ascendant=asc,
        house_cusps=list(houses),
        planet_positions=list(planets),
        panchanga=panchanga,
    )
    return D1Chart(
        ascendant=asc,
        houses=houses,
        planets=planets,
        aspects=(),
        planet_strengths=(),
        panchanga=panchanga,
        ayanamsa_system="lahiri",
        house_system="placidus",
        ephemeris=eph,
    )


def test_triple_dasha_confluence_evaluation():
    engine = TripleDashaConfluenceEngine()
    chart = _make_mock_chart("aries")
    birth_dt = datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc)
    target_d = date(2024, 6, 1)

    result = engine.evaluate_window_confluence(
        chart=chart,
        target_date=target_d,
        birth_dt=birth_dt,
        mahadasha_lord="jupiter",
        antardasha_lord="sun",
        domain="career",
    )

    assert isinstance(result, TripleDashaWindowConfluence)
    assert result.confluence_level in ("TRIPLE_CONFLUENCE", "DUAL_CONFLUENCE", "SINGLE_ALIGNMENT")
    assert 0.0 <= result.confluence_score <= 1.0
    assert result.vimshottari_md == "jupiter"
    assert result.vimshottari_ad == "sun"
    assert 1 <= result.scd_active_house <= 12
    assert result.chara_dasha_rashi != ""
    assert "संगम" in result.actionable_synthesis_hi
    assert "Confluence" in result.actionable_synthesis_en
