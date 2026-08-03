"""
Unit tests for the reproducibility additions to
apps/api/services/pattern_discovery.py (Module 27, Phase 3c):
supporting_case_ids threading, lift_score, and find_contradicting_cases.

Pure in-memory logic — no DB, no ephemeris.
"""

from __future__ import annotations

from datetime import date

from apps.api.domain.research_case import ExtractedFeature, PatternDimension
from apps.api.services.pattern_discovery import PatternDiscoveryService


def make_feature(**overrides) -> ExtractedFeature:
    defaults = dict(
        feature_name="dasha_mahadasha",
        feature_value="Ju",
        feature_category="dasha",
        event_type="marriage",
        research_case_id="RC-1",
        event_date=date(2020, 1, 1),
    )
    defaults.update(overrides)
    return ExtractedFeature(**defaults)


def test_pattern_dimension_lift_score():
    dim = PatternDimension(dimension="dasha_mahadasha", value="Ju", frequency=0.4, count=4, expected_by_chance=0.2)
    assert dim.lift_score == 2.0


def test_pattern_dimension_lift_score_zero_base_rate():
    dim = PatternDimension(dimension="dasha_mahadasha", value="Ju", frequency=0.4, count=4, expected_by_chance=0.0)
    assert dim.lift_score == 0.0


def test_discover_threads_supporting_case_ids_for_single_dimension():
    # 5 of 10 marriage cases share dasha_mahadasha=Ju (50% within-type rate);
    # 20 unrelated promotion cases dilute the global base rate to ~17%, well
    # under the marriage rate — clears both MIN_FREQUENCY and MIN_SIGNIFICANCE.
    features = []
    for i in range(5):
        features.append(make_feature(research_case_id=f"RC-{i}", feature_value="Ju"))
    for i in range(5, 10):
        features.append(make_feature(research_case_id=f"RC-{i}", feature_value="Ve"))
    for i in range(10, 30):
        features.append(make_feature(research_case_id=f"RC-{i}", event_type="promotion", feature_value="Sa"))

    engine = PatternDiscoveryService()
    patterns = engine.discover(features, event_type="marriage", top_combos=5)

    ju_patterns = [p for p in patterns if p.dimensions[0].value == "Ju"]
    assert ju_patterns, "expected a discovered pattern for dasha_mahadasha=Ju"
    pattern = ju_patterns[0]
    assert pattern.supporting_case_ids == frozenset(f"RC-{i}" for i in range(5))
    assert pattern.lift_score == pattern.dimensions[0].lift_score


def test_find_contradicting_cases():
    # RC-1 exhibits dasha_mahadasha=Ju during a Divorce event (not Marriage) —
    # the astrological signature was present but the target event didn't occur.
    # RC-2 exhibits it during an actual Marriage — not contradicting.
    features = [
        make_feature(research_case_id="RC-1", event_type="divorce", feature_value="Ju"),
        make_feature(research_case_id="RC-2", event_type="marriage", feature_value="Ju"),
        make_feature(research_case_id="RC-3", event_type="promotion", feature_value="Ve"),
    ]
    dimensions = [
        PatternDimension(dimension="dasha_mahadasha", value="Ju", frequency=0.5, count=1, expected_by_chance=0.3)
    ]

    engine = PatternDiscoveryService()
    contradicting = engine.find_contradicting_cases(features, event_type="marriage", dimensions=dimensions)

    assert contradicting == ["RC-1"]


def test_find_contradicting_cases_requires_all_dimensions():
    # RC-1 only exhibits ONE of the two required dimensions among its
    # non-marriage features — should not count as contradicting.
    features = [
        make_feature(research_case_id="RC-1", event_type="divorce", feature_name="dasha_mahadasha", feature_value="Ju"),
        make_feature(research_case_id="RC-1", event_type="divorce", feature_name="transit_Sa_7th", feature_value="False"),
    ]
    dimensions = [
        PatternDimension(dimension="dasha_mahadasha", value="Ju", frequency=0.5, count=1, expected_by_chance=0.3),
        PatternDimension(dimension="transit_Sa_7th", value="True", frequency=0.5, count=1, expected_by_chance=0.3),
    ]

    engine = PatternDiscoveryService()
    contradicting = engine.find_contradicting_cases(features, event_type="marriage", dimensions=dimensions)

    assert contradicting == []
