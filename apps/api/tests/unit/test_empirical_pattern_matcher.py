import pytest
from apps.api.services.empirical_pattern_matcher import EmpiricalPatternMatcher, EmpiricalMatchResult


def test_empirical_pattern_matcher_loads():
    patterns = EmpiricalPatternMatcher.load_patterns()
    assert isinstance(patterns, list)
    assert len(patterns) > 0


def test_empirical_pattern_matcher_marriage_rule():
    # Test Rahu Mahadasha matching for Marriage domain
    result = EmpiricalPatternMatcher.match_window(
        event_domain="marriage",
        mahadasha_lord="rahu",
    )
    assert result is not None
    assert result.is_matched is True
    assert result.matched_event_type == "MARRIAGE"
    assert result.sample_size >= 4000
    assert result.lift_ratio >= 1.2
    assert "🔬 Empirically Proven Signature" in result.evidence_badge


def test_empirical_pattern_matcher_child_birth():
    # Test Moon Mahadasha matching for Child Birth
    result = EmpiricalPatternMatcher.match_window(
        event_domain="wealth",  # child birth mapped under wealth/family
        mahadasha_lord="moon",
    )
    assert result is not None
    assert result.matched_event_type == "CHILD BIRTH"
    assert result.sample_size >= 700
    assert result.lift_ratio >= 1.4


def test_empirical_pattern_matcher_unmatched():
    # Unmatched scenario
    result = EmpiricalPatternMatcher.match_window(
        event_domain="speculation",
        mahadasha_lord="unknown_lord_xyz",
    )
    assert result is None
