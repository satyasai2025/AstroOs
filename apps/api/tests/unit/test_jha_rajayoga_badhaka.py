"""
AstroOS — Unit Tests for Jha 44 Kendra-Trikona Rajayoga with Badhaka Obstruction
================================================================================
Provenance: kundalee-binary frmYogaHelp (DevMithila)
"राजयोग तभी कारगर होता है जब बाधक योग न हों!"
"""

import pytest

from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import AspectInfo
from apps.api.services.yoga_predicates import YogaContext
from apps.api.services.yogas.jha_rajayoga_badhaka import evaluate_jha_rajayoga_badhaka


def _build_test_context(
    lagna_rashi: str = "aries",
    house_occupants: dict[int, list[str]] = None,
    aspects: list[AspectInfo] = None,
) -> YogaContext:
    # Build 12 house cusps
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
              "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    l_idx = rashis.index(lagna_rashi)
    cusps = []
    for h in range(1, 13):
        r = rashis[(l_idx + h - 1) % 12]
        cusps.append(HouseCusp(
            house_number=h,
            longitude=h * 30.0,
            sidereal_longitude=h * 30.0,
            rashi=r,
        ))

    # Build planets
    planets = []
    occ_map = house_occupants or {}
    for h, p_list in occ_map.items():
        for p in p_list:
            r = cusps[h - 1].rashi
            planets.append(SiderealPosition(
                planet=p,
                sidereal_longitude=h * 30.0,
                rashi=r,
                rashi_degree=15.0,
                house_number=h,
                nakshatra="ashwini",
                pada=1,
                is_retrograde=False,
                is_combust=False,
                combustion_orb=None,
                dignity=None,
            ))

    class MockChart:
        def __init__(self):
            self.ascendant = Ascendant(
                longitude=0.0,
                sidereal_longitude=0.0,
                rashi=lagna_rashi,
                rashi_degree=0.0,
                nakshatra="ashwini",
                pada=1,
            )
            self.houses = cusps
            self.planets = planets
            self.aspects = aspects or []

    from apps.api.services.house_engine import HouseEngine
    return YogaContext.build(chart=MockChart(), house_engine=HouseEngine())


def test_jha_rajayoga_unobstructed():
    """Aries lagna: 1L Mars + 5L Sun conjunct in 5th house; Badhakesh Saturn in 3rd without aspect on them."""
    ctx = _build_test_context(
        lagna_rashi="aries", # Chara lagna -> Badhaka house 11 (Aquarius -> Saturn)
        house_occupants={
            5: ["mars", "sun"], # Kendra 1L Mars + Trikona 5L Sun conjunct
            3: ["saturn"],      # Badhakesh in 3rd house (no aspect on 5th house)
        },
        aspects=[],
    )

    res = evaluate_jha_rajayoga_badhaka(ctx)
    assert res.is_present is True
    assert res.strength == "full"
    # Sun and Mars Rajayoga must be Active and Unobstructed
    active_yogas = [y for y in res.satisfied if "ACTIVE" in y]
    assert len(active_yogas) > 0


def test_jha_rajayoga_obstructed_by_badhakesh():
    """Aries lagna (Chara): Badhaka is 11H (Aquarius -> Saturn). When Saturn conjoins Mars + Sun -> Obstructed."""
    ctx = _build_test_context(
        lagna_rashi="aries", # Chara lagna -> Badhakesh = Saturn (11H)
        house_occupants={
            5: ["mars", "sun", "saturn"], # Badhakesh Saturn directly conjoining the Rajayoga planets!
        },
        aspects=[],
    )

    res = evaluate_jha_rajayoga_badhaka(ctx)
    assert res.is_present is True
    # Must be flagged as OBSTRUCTED by Badhakesh!
    obstructed = [y for y in res.satisfied if "OBSTRUCTED by Badhakesh" in y]
    assert len(obstructed) > 0


def test_jha_rajayoga_sthira_lagna_9th_badhaka():
    """Leo lagna (Sthira): Badhaka is 9H (Aries -> Mars). 10L Venus + 5L Jupiter obstructed by 9L Badhakesh Mars."""
    # Test A: Unobstructed
    ctx_clean = _build_test_context(
        lagna_rashi="leo", # Sthira lagna -> Badhaka house = 9 (Aries -> Mars)
        house_occupants={
            10: ["venus", "jupiter"], # 10L Venus + 5L Jupiter conjunct in 10th
            3: ["mars"],              # Badhakesh Mars in 3rd without aspect on 10th
        },
        aspects=[],
    )
    res_clean = evaluate_jha_rajayoga_badhaka(ctx_clean)
    assert any("ACTIVE" in y for y in res_clean.satisfied)

    # Test B: Obstructed by Badhakesh Mars
    ctx_blocked = _build_test_context(
        lagna_rashi="leo",
        house_occupants={
            10: ["venus", "jupiter", "mars"], # Badhakesh Mars directly afflicting the Rajayoga!
        },
        aspects=[],
    )
    res_blocked = evaluate_jha_rajayoga_badhaka(ctx_blocked)
    obstructed = [y for y in res_blocked.satisfied if "OBSTRUCTED by Badhakesh Mars" in y]
    assert len(obstructed) > 0


def test_jha_rajayoga_dual_lagna_7th_badhaka():
    """Gemini lagna (Dual): Badhaka is 7H (Sagittarius -> Jupiter). 1L Mercury + 5L Venus obstructed by 7L Jupiter."""
    # Test A: Unobstructed
    ctx_clean = _build_test_context(
        lagna_rashi="gemini", # Dual lagna -> Badhaka house = 7 (Sagittarius -> Jupiter)
        house_occupants={
            1: ["mercury", "venus"], # 1L Mercury + 5L Venus conjunct in 1st house
            11: ["jupiter"],         # Badhakesh Jupiter in 11th house
        },
        aspects=[],
    )
    res_clean = evaluate_jha_rajayoga_badhaka(ctx_clean)
    assert any("ACTIVE" in y for y in res_clean.satisfied)

    # Test B: Obstructed by Badhakesh Jupiter
    ctx_blocked = _build_test_context(
        lagna_rashi="gemini",
        house_occupants={
            1: ["mercury", "venus", "jupiter"], # Badhakesh Jupiter directly afflicting the Rajayoga!
        },
        aspects=[],
    )
    res_blocked = evaluate_jha_rajayoga_badhaka(ctx_blocked)
    obstructed = [y for y in res_blocked.satisfied if "OBSTRUCTED by Badhakesh Jupiter" in y]
    assert len(obstructed) > 0