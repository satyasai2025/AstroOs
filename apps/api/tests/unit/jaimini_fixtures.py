"""
AstroOS — Shared Jaimini Test Fixtures

Synthetic D1Chart/VargaChart builders for Jaimini engine unit tests.
Not a test module itself (no test_ prefix, not collected by pytest) —
imported by test_jaimini_*.py files to avoid each re-deriving the same
chart-construction boilerplate. Deliberately decouples house_number
(Bhava Chalit, unused by any Jaimini engine) from rashi — every fixture
fixes house_number=1 for every planet since only .rashi matters here.
"""

from apps.api.domain.divisional import VargaAscendant, VargaChart, VargaPosition
from apps.api.domain.ephemeris import (
    Ascendant,
    HouseCusp,
    KaranaInfo,
    NakshatraInfo,
    PanchangaResult,
    SiderealPosition,
    TithiInfo,
    VaraInfo,
    YogaInfo,
)
from apps.api.domain.horoscope import D1Chart

RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def make_planet(
    planet: str,
    rashi: str,
    rashi_degree: float = 15.0,
    speed_deg_per_day: float = 1.0,
    is_retrograde: bool = False,
    dignity=None,
) -> SiderealPosition:
    return SiderealPosition(
        planet=planet,
        sidereal_longitude=RASHI_LIST.index(rashi) * 30.0 + rashi_degree,
        rashi=rashi,
        rashi_degree=rashi_degree,
        house_number=1,
        nakshatra="ashwini",
        pada=1,
        is_retrograde=is_retrograde,
        is_combust=False,
        combustion_orb=None,
        dignity=dignity,
        speed_deg_per_day=speed_deg_per_day,
        rashi_house_number=1,
    )


def make_panchanga(paksha: str = "shukla") -> PanchangaResult:
    return PanchangaResult(
        tithi=TithiInfo(number=5, name="Panchami", paksha=paksha, completion_percent=50.0),
        nakshatra=NakshatraInfo(
            nakshatra="ashwini", nakshatra_number=1, pada=1, lord="ketu",
            degree_in_nakshatra=5.0, degree_in_pada=5.0,
        ),
        yoga=YogaInfo(number=1, name="Vishkambha", completion_percent=50.0),
        karana=KaranaInfo(number=1, name="Bava", is_fixed=False),
        vara=VaraInfo(number=1, name="Sunday", lord="sun"),
        julian_day=2448000.0,
        ayanamsa_deg=23.5,
    )


def make_d1_chart(
    lagna_rashi: str,
    planets: list[SiderealPosition],
    paksha: str = "shukla",
) -> D1Chart:
    lagna_index = RASHI_LIST.index(lagna_rashi)
    houses = [
        HouseCusp(
            house_number=i + 1,
            longitude=float(((lagna_index + i) % 12) * 30),
            sidereal_longitude=float(((lagna_index + i) % 12) * 30),
            rashi=RASHI_LIST[(lagna_index + i) % 12],
        )
        for i in range(12)
    ]
    ascendant = Ascendant(
        longitude=lagna_index * 30.0,
        sidereal_longitude=lagna_index * 30.0,
        rashi=lagna_rashi,
        rashi_degree=0.0,
        nakshatra="ashwini",
        pada=1,
    )
    return D1Chart(
        ephemeris=None,
        ascendant=ascendant,
        houses=houses,
        planets=planets,
        aspects=[],
        planet_strengths=[],
        panchanga=make_panchanga(paksha),
        ayanamsa_system="lahiri",
        house_system="W",
    )


def make_d9_chart(planet_signs: dict[str, str], lagna_rashi: str) -> VargaChart:
    """planet_signs: {planet_name: d9_varga_rashi}."""
    lagna_index = RASHI_LIST.index(lagna_rashi)
    ascendant = VargaAscendant(
        d1_sidereal_longitude=lagna_index * 30.0,
        d1_rashi=lagna_rashi,
        d1_rashi_degree=0.0,
        varga_rashi=lagna_rashi,
        varga_rashi_degree=0.0,
    )
    positions = tuple(
        VargaPosition(
            planet=planet,
            d1_sidereal_longitude=0.0,
            d1_rashi="aries",
            d1_rashi_degree=0.0,
            varga_rashi=rashi,
            varga_rashi_degree=0.0,
            varga_house_number=1,
            is_retrograde=False,
            is_combust=False,
            nakshatra="ashwini",
            pada=1,
        )
        for planet, rashi in planet_signs.items()
    )
    return VargaChart(
        varga="D9",
        divisor=9,
        ascendant=ascendant,
        planet_positions=positions,
        ayanamsa_system="lahiri",
        julian_day=2448000.0,
    )
