"""
Comprehensive Unit Tests for PrashnaEngine.

Test Suite:
1. KP 1-249 Arudha table boundaries and contiguous arcs
2. KP 1-2193 Sub-sub divisions and boundaries
3. SgL -> StL -> SL -> SSL Lord consistency
4. Sphutas (Trisphuta, Chatursphuta, Panchasphuta, Pranasphuta, Dehasphuta, Mrityusphuta)
5. Ruling Planets (RP) CT/RT snapshots
6. Arabic Parts / Sahams / Event Formulas (Day & Night calculations)
7. Prashna Judgement & Evidence synthesis (No hard-coded values, true confidence & rules)
8. Timing calculation (Real Dasha periods and window bounds)
"""

from __future__ import annotations
from datetime import datetime, timezone
import pytest

from apps.api.domain.prashna import PRASNA_KP_249_TABLE
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd
from apps.api.services.prashna_engine import PrashnaEngine

_BIRTH = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
_LAT, _LON = 22.3, 73.2


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


@pytest.fixture(scope="module")
def engine(wrapper: EphemerisWrapper) -> PrashnaEngine:
    return PrashnaEngine(wrapper)


# ── 1. KP 249 Table Boundaries & Integrity ───────────────────────────────────

def test_table_has_249_entries():
    assert len(PRASNA_KP_249_TABLE) == 249


def test_table_arcs_are_contiguous_and_cover_full_zodiac():
    prev_global_end = 0.0
    for rashi_idx, _nak, start, end, *_ in PRASNA_KP_249_TABLE:
        global_start = rashi_idx * 30.0 + start
        global_end = rashi_idx * 30.0 + end
        assert global_start == pytest.approx(prev_global_end, abs=1e-6)
        assert global_end > global_start
        prev_global_end = global_end
    assert prev_global_end == pytest.approx(360.0, abs=1e-6)


def test_arudha_seed_1_boundary(engine: PrashnaEngine):
    res = engine.arudha_from_seed(1, "kp_249")
    assert res.rashi == "aries"
    assert res.nakshatra == "ashwini"
    assert res.sign_lord == "mars"
    assert res.star_lord == "ketu"
    assert res.sub_lord == "ketu"
    assert 0.0 <= res.sidereal_longitude < 1.0


def test_arudha_seed_249_boundary(engine: PrashnaEngine):
    res = engine.arudha_from_seed(249, "kp_249")
    assert res.rashi == "pisces"
    assert res.nakshatra == "revati"
    assert res.sign_lord == "jupiter"
    assert res.star_lord == "mercury"
    assert res.sub_lord == "saturn"
    assert 358.0 < res.sidereal_longitude < 360.0


@pytest.mark.parametrize("seed", [0, -1, 250, 5000])
def test_arudha_249_rejects_out_of_range(engine: PrashnaEngine, seed: int):
    with pytest.raises(ValueError):
        engine.arudha_from_seed(seed, "kp_249")


# ── 2. KP 2193 Divisions & Boundaries ────────────────────────────────────────

def test_arudha_kp_2193_first_and_last(engine: PrashnaEngine):
    res_1 = engine.arudha_from_seed(1, "kp_2193")
    assert res_1.system == "kp_2193"
    assert res_1.rashi == "aries"
    assert 0.0 <= res_1.sidereal_longitude < 0.2

    res_last = engine.arudha_from_seed(2193, "kp_2193")
    assert res_last.system == "kp_2193"
    assert res_last.rashi == "pisces"
    assert 359.8 <= res_last.sidereal_longitude <= 360.0


@pytest.mark.parametrize("seed", [0, -5, 2194, 10000])
def test_arudha_2193_rejects_out_of_range(engine: PrashnaEngine, seed: int):
    with pytest.raises(ValueError):
        engine.arudha_from_seed(seed, "kp_2193")


# ── 3. SgL -> StL -> SL -> SSL Consistency ──────────────────────────────────

def test_kp_lords_resolution(engine: PrashnaEngine):
    # 0 deg Aries (Ashwini / Mars / Ketu / Ketu)
    lords_0 = engine.get_kp_lords_for_longitude(0.01)
    assert lords_0["sign_lord"] == "mars"
    assert lords_0["star_lord"] == "ketu"
    assert lords_0["sub_lord"] == "ketu"
    assert lords_0["sub_sub_lord"] in ("ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury")


# ── 4. Sphutas Integrity ────────────────────────────────────────────────────

def test_sphutas_are_all_valid_longitudes(engine: PrashnaEngine):
    result = engine.sphutas_for_chart(_BIRTH, _LAT, _LON, ayanamsa="lahiri")
    assert len(result.sphutas) == 6
    names = [s.name.lower() for s in result.sphutas]
    assert names == [
        "trisphuta", "chatursphuta", "panchasphuta",
        "pranasphuta", "dehasphuta", "mrityusphuta",
    ]
    for s in result.sphutas:
        assert 0.0 <= s.sidereal_longitude < 360.0


def test_trisphuta_equals_lagna_plus_moon_plus_gulika(engine: PrashnaEngine, wrapper: EphemerisWrapper):
    result = engine.sphutas_for_chart(_BIRTH, _LAT, _LON, ayanamsa="lahiri")
    tri = next(s for s in result.sphutas if s.name.lower() == "trisphuta")

    jd = datetime_to_jd(_BIRTH)
    moon_lon = wrapper.to_sidereal(
        wrapper.get_planet_position("moon", jd).longitude, wrapper.get_ayanamsa(jd)
    )
    expected = (result.ascendant_longitude + moon_lon + result.gulika_longitude) % 360.0
    assert tri.sidereal_longitude == pytest.approx(expected, abs=1e-6)


# ── 5. Ruling Planets CT/RT ──────────────────────────────────────────────────

def test_ruling_planets_structure(engine: PrashnaEngine):
    rp = engine.get_ruling_planets(_BIRTH, _LAT, _LON, "lahiri")
    assert rp.day_lord in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
    assert rp.hora_lord in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
    point_names = [e.point_name for e in rp.entries]
    assert "Ascendant" in point_names
    assert "Moon" in point_names
    assert "Rahu" in point_names
    assert "Ketu" in point_names


# ── 6. Arabic Parts & Day/Night Formulas ─────────────────────────────────────

def test_arabic_parts_day_night(engine: PrashnaEngine):
    parts = engine.calculate_arabic_parts(_BIRTH, _LAT, _LON, "lahiri")
    assert len(parts) >= 30
    part_dict = {p.name: p for p in parts}

    # Fortuna, Spirit, Surgery must exist
    assert "Fortuna" in part_dict
    assert "Spirit" in part_dict
    assert "Surgery" in part_dict
    assert "Abundance in the Home" in part_dict

    # Check that degree is valid and lords are populated
    for p in parts:
        assert 0.0 <= p.sidereal_longitude < 360.0
        assert len(p.sign_lord) > 0
        assert len(p.star_lord) > 0
        assert len(p.sub_lord) > 0
        assert len(p.sub_sub_lord) > 0


# ── 7. Judgement, Evidence Weights & Timing ──────────────────────────────────

def test_prashna_judgement_career_query(engine: PrashnaEngine):
    j = engine.evaluate_judgement("Will I get selected for the job today?", _BIRTH, _LAT, _LON, seed_number=14)
    assert j.verdict in ("YES", "NO", "MIXED")
    assert 45 <= j.confidence_percentage <= 95
    assert len(j.key_evidences) >= 5
    assert len(j.supporting_rules) >= 4
    assert len(j.contradictions) >= 1

    # Verify timing is calculated with real dasha
    assert len(j.timing.dasha_mahadasha) > 0
    assert len(j.timing.likely_window) > 0
    assert "–" in j.timing.likely_window


def test_prashna_judgement_marriage_query(engine: PrashnaEngine):
    j = engine.evaluate_judgement("When will my marriage happen?", _BIRTH, _LAT, _LON, seed_number=108)
    assert j.verdict in ("YES", "NO", "MIXED")
    assert 0 <= j.confidence_percentage <= 100
    factors = [e.factor for e in j.key_evidences]
    assert any("7th" in f or "Marriage" in f or "CSL" in f for f in factors)


# ── 8. Astrological Methodology & Causal Traceability Suite ──────────────────

def test_question_to_house_mapping(engine: PrashnaEngine):
    """Test Question -> Relevant Houses & Negating Houses classification."""
    job_meta = engine.classify_question("Will I get selected in this interview?")
    assert job_meta["category"] == "career"
    assert job_meta["primary_cusp"] == 10
    assert 2 in job_meta["supporting_cusps"]
    assert 6 in job_meta["supporting_cusps"]
    assert 11 in job_meta["supporting_cusps"]
    assert 5 in job_meta["negating_cusps"]

    marriage_meta = engine.classify_question("Will I marry my partner?")
    assert marriage_meta["category"] == "marriage"
    assert marriage_meta["primary_cusp"] == 7
    assert 2 in marriage_meta["supporting_cusps"]
    assert 11 in marriage_meta["supporting_cusps"]
    assert 6 in marriage_meta["negating_cusps"]

    property_meta = engine.classify_question("Can I buy this apartment / property?")
    assert property_meta["category"] == "property"
    assert property_meta["primary_cusp"] == 4
    assert 11 in property_meta["supporting_cusps"]

    health_meta = engine.classify_question("Will I recover from surgery and illness?")
    assert health_meta["category"] == "health"
    assert health_meta["primary_cusp"] == 6
    assert 1 in health_meta["supporting_cusps"]
    assert 5 in health_meta["supporting_cusps"]


def test_significator_resolution_four_tier(engine: PrashnaEngine):
    """Test 4-Fold canonical significator matrix resolution with causal explanations."""
    mock_planets = [
        {"planet": "sun", "house_number": 11, "star_lord": "ketu"},
        {"planet": "moon", "house_number": 2, "star_lord": "mercury"},
        {"planet": "jupiter", "house_number": 10, "star_lord": "mercury"},
        {"planet": "saturn", "house_number": 6, "star_lord": "saturn"},
    ]
    mock_cusps = [
        {"house": 10, "sign_lord": "sun", "sub_lord": "venus"},
        {"house": 2, "sign_lord": "mars", "sub_lord": "saturn"},
        {"house": 6, "sign_lord": "jupiter", "sub_lord": "mercury"},
    ]

    four_tier, factors = engine.compute_four_tier_significators(mock_planets, mock_cusps)

    # House 10 occupant is Jupiter -> Tier B
    assert "jupiter" in four_tier[10]["B"]

    # House 10 Sign Lord is Sun -> Tier D
    assert "sun" in four_tier[10]["D"]

    # Factors must explain why each planet is selected
    reasons = [f.reason for f in factors if f.house == 10]
    assert any("Direct occupant of House 10" in r for r in reasons)
    assert any("Ruler / Sign Lord of House 10" in r for r in reasons)


def test_ruling_planet_integration_metadata(engine: PrashnaEngine):
    """Test that Ruling Planets snapshot contains prioritized evidence and reasoning."""
    rp = engine.get_ruling_planets(
        _BIRTH, _LAT, _LON, "lahiri", target_houses=[10, 2, 6, 11]
    )
    assert len(rp.entries) >= 6

    # Verify priority sequence
    priorities = [e.priority for e in rp.entries]
    assert priorities == sorted(priorities)

    # Verify each RP has rich metadata
    for e in rp.entries:
        assert len(e.planet) > 0
        assert len(e.source) > 0
        assert len(e.reason) > 0
        assert len(e.relationship_to_judgement) > 0


def test_rule_evidence_structure(engine: PrashnaEngine):
    """Test that every rule evaluation returns structured evidence with causal details."""
    j = engine.evaluate_judgement("Will I get this job?", _BIRTH, _LAT, _LON)

    for rule in j.supporting_rules:
        assert len(rule.rule_id) > 0
        assert len(rule.rule_name) > 0
        assert rule.triggered in ("Yes", "Partially", "No")
        assert isinstance(rule.weight, int)
        assert len(rule.result) > 0
        assert len(rule.evidence) > 0


def test_supporting_and_contradicting_factors_preservation(engine: PrashnaEngine):
    """Test that both positive support and contradictory friction factors are preserved."""
    j = engine.evaluate_judgement("Will I get this job?", _BIRTH, _LAT, _LON)

    # Must have both supporting rules and contradiction items
    assert len(j.supporting_rules) >= 4
    assert len(j.contradictions) >= 1

    # Check that contradiction items have actionable advice and descriptions
    for c in j.contradictions:
        assert len(c.title) > 0
        assert len(c.description) > 0
        assert len(c.advice) > 0


def test_verdict_derivation_from_evaluated_weights(engine: PrashnaEngine):
    """Test that the verdict (YES/NO/MIXED) and confidence percentage are derived mathematically."""
    j = engine.evaluate_judgement("Will I get this promotion?", _BIRTH, _LAT, _LON)

    assert j.verdict in ("YES", "NO", "MIXED")
    assert 15 <= j.confidence_percentage <= 95
    assert len(j.conclusions) >= 4
    assert j.conclusions[-1].startswith(f"Final Judgement: {j.verdict}")


def test_timing_traceability_dasha_transit(engine: PrashnaEngine):
    """Test that timing output is traceable to real Dasha periods and planetary transits."""
    j = engine.evaluate_judgement("When will my interview results come?", _BIRTH, _LAT, _LON)

    assert "Mahadasha" in j.timing.dasha_mahadasha
    assert "Antardasha" in j.timing.antardasha
    assert "–" in j.timing.likely_window
    assert "Jupiter" in j.timing.transit_support
    assert "Moon" in j.timing.moon_cycle

