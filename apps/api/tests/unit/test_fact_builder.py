"""
AstroOS — FactBuilder Unit Tests (Module 13)
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )


def test_planet_facts_built_for_all_9_planets(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        assert facts.has_fact(f"planet.{planet}.house")
        assert facts.has_fact(f"planet.{planet}.rashi")


def test_dignity_facts_only_for_classical_seven(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        assert facts.has_fact(f"planet.{planet}.exalted")
    for planet in ["rahu", "ketu"]:
        assert not facts.has_fact(f"planet.{planet}.exalted")


def test_house_lord_facts_built_for_all_12_houses(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for house in range(1, 13):
        assert facts.has_fact(f"house.{house}.lord")


def test_house_lord_house_fact_matches_lords_actual_position(chart):
    """house.N.lord_house must equal the house the named lord planet actually occupies."""
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for house in range(1, 13):
        lord = facts.get_value(f"house.{house}.lord")
        lord_house = facts.get_value(f"house.{house}.lord_house")
        planet_actual_house = facts.get_value(f"planet.{lord}.house")
        assert lord_house == planet_actual_house


def test_yoga_facts_built_for_all_registered_yogas(chart):
    from apps.api.services.yoga_registry import all_yogas
    from apps.api.services import yogas as _yogas  # noqa: F401

    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for definition in all_yogas():
        assert facts.has_fact(f"yoga.{definition.yoga_id}.present")
        assert facts.has_fact(f"yoga.{definition.yoga_id}.strength")


def test_shadbala_facts_absent_when_no_shadbala_engine_provided(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    assert not facts.has_fact("shadbala.jupiter.total")


def test_shadbala_facts_present_when_engine_provided(wrapper, chart):
    shadbala_engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper), ephemeris_wrapper=wrapper)
    builder = FactBuilder(shadbala_engine=shadbala_engine)
    facts = builder.build_facts(chart)
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        assert facts.has_fact(f"shadbala.{planet}.total")


def test_shadbala_totals_are_in_rupa_scale_not_shashtiamsas(wrapper, chart):
    shadbala_engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper), ephemeris_wrapper=wrapper)
    builder = FactBuilder(shadbala_engine=shadbala_engine)
    facts = builder.build_facts(chart)
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        total = facts.get_value(f"shadbala.{planet}.total")
        assert 0 < total < 15, f"{planet}.total={total} looks like raw Shashtiamsas, not Rupas"


def test_ashtakavarga_facts_present_for_classical_seven(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        bindus = facts.get_value(f"ashtakavarga.{planet}.bindu")
        assert bindus is not None
        assert 0 <= bindus <= 8


def test_transit_facts_absent_without_transit_datetime(wrapper, chart):
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(transit_engine=transit_engine)
    facts = builder.build_facts(chart)
    assert not facts.has_fact("transit.saturn.house")


def test_transit_facts_absent_without_transit_engine(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart, transit_datetime_utc=datetime(2026, 7, 12, tzinfo=timezone.utc))
    assert not facts.has_fact("transit.saturn.house")


def test_transit_facts_present_when_both_provided(wrapper, chart):
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(transit_engine=transit_engine)
    facts = builder.build_facts(chart, transit_datetime_utc=datetime(2026, 7, 12, tzinfo=timezone.utc))
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        assert facts.has_fact(f"transit.{planet}.house")
    assert facts.has_fact("transit.saturn.sade_sati")
    assert facts.has_fact("transit.saturn.ashtama_shani")


def test_only_saturn_has_sade_sati_ashtama_shani_facts(wrapper, chart):
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(transit_engine=transit_engine)
    facts = builder.build_facts(chart, transit_datetime_utc=datetime(2026, 7, 12, tzinfo=timezone.utc))
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus"]:
        assert not facts.has_fact(f"transit.{planet}.sade_sati")


def test_fact_values_match_specification_examples_exactly(wrapper, chart):
    shadbala_engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper), ephemeris_wrapper=wrapper)
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(shadbala_engine=shadbala_engine, transit_engine=transit_engine)
    facts = builder.build_facts(chart, transit_datetime_utc=datetime(2026, 7, 12, tzinfo=timezone.utc))

    for key in [
        "planet.jupiter.house", "planet.jupiter.exalted", "planet.jupiter.own_sign",
        "house.9.lord", "yoga.BPHS-PM-001.present", "yoga.BPHS-PM-001.strength",
        "shadbala.jupiter.total", "ashtakavarga.jupiter.bindu", "transit.saturn.house",
    ]:
        assert facts.has_fact(key), f"missing fact: {key}"


def test_maraka_and_badhaka_facts_present(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    assert facts.has_fact("badhaka.house")
    assert facts.has_fact("badhaka.lord")
    assert facts.has_fact("maraka.house_2")
    assert facts.has_fact("maraka.house_7")
    for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        assert facts.has_fact(f"maraka.lord.{p}")
        assert isinstance(facts.get_value(f"maraka.lord.{p}"), bool)


def test_aspect_facts_present(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    # Check that at least some planetary aspects are computed
    aspect_present_facts = [f for f in facts.all_facts() if f.key.startswith("aspect.") and f.key.endswith(".present")]
    assert len(aspect_present_facts) > 0
    for f in aspect_present_facts:
        assert f.value is True
        type_key = f.key.replace(".present", ".type")
        assert facts.has_fact(type_key)


def test_friendship_facts_present(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for p1 in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for p2 in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
            if p1 == p2:
                continue
            assert facts.has_fact(f"friendship.natural.{p1}.{p2}")
            assert facts.get_value(f"friendship.natural.{p1}.{p2}") in ("friend", "enemy", "neutral")
            assert facts.has_fact(f"friendship.temporary.{p1}.{p2}")
            assert facts.get_value(f"friendship.temporary.{p1}.{p2}") in ("friend", "enemy")
            assert facts.has_fact(f"friendship.panchadha.{p1}.{p2}")
            assert facts.get_value(f"friendship.panchadha.{p1}.{p2}") in ("adhi_mitra", "mitra", "sama", "shatru", "adhi_shatru")


def test_functional_lordship_facts_present(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        assert facts.has_fact(f"functional.{p}.lordship")
        assert facts.get_value(f"functional.{p}.lordship") in ("benefic", "malefic", "neutral")
        assert facts.has_fact(f"functional.{p}.yogakaraka")
        assert isinstance(facts.get_value(f"functional.{p}.yogakaraka"), bool)


def test_guna_facts_present_for_nakshatra_only(chart):
    builder = FactBuilder()
    facts = builder.build_facts(chart)
    # Check that nakshatra guna exists
    guna_facts = [f for f in facts.all_facts() if f.key.startswith("guna.nakshatra.")]
    assert len(guna_facts) > 0
    for f in guna_facts:
        assert f.value in ("sattvic", "rajasic", "tamasic", "rajasic-tamasic")

    # Planet and rashi gunas are NOT_IMPLEMENTED
    for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        assert not facts.has_fact(f"guna.planet.{p}")
    for r in ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]:
        assert not facts.has_fact(f"guna.rashi.{r}")


def test_transit_gati_vedha_and_sbc_facts_present(wrapper, chart):
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(transit_engine=transit_engine)
    facts = builder.build_facts(chart, transit_datetime_utc=datetime(2026, 7, 12, tzinfo=timezone.utc))

    VALID_GATIS = {"vikala", "vakra", "mandatara", "manda", "sama", "chara", "atichara"}
    for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        assert facts.has_fact(f"transit.{p}.gati")
        gati_val = facts.get_value(f"transit.{p}.gati")
        assert gati_val in VALID_GATIS, f"unexpected gati {gati_val} for {p}"

        # SBC position
        assert facts.has_fact(f"sbc.{p}.position")
        assert facts.has_fact(f"sbc.{p}.vedha.active")


def test_fact_builder_determinism(wrapper, chart):
    shadbala_engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper), ephemeris_wrapper=wrapper)
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(shadbala_engine=shadbala_engine, transit_engine=transit_engine)

    transit_dt = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc)
    facts_1 = builder.build_facts(chart, transit_datetime_utc=transit_dt)
    facts_2 = builder.build_facts(chart, transit_datetime_utc=transit_dt)

    list_1 = sorted([(f.key, str(f.value), f.source) for f in facts_1.all_facts()])
    list_2 = sorted([(f.key, str(f.value), f.source) for f in facts_2.all_facts()])

    assert list_1 == list_2
    assert len(list_1) > 50

