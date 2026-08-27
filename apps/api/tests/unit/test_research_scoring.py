"""
Unit tests — Research scoring: coverage-adjusted lift and ensemble verdict.
"""

from __future__ import annotations

import pytest

from packages.shared.research_scoring import (
    EnsembleVerdict,
    TechniqueScore,
    corpus_summary,
    rank_techniques,
)


class TestTechniqueScoreBasics:
    def test_perfect_recall_full_coverage(self):
        s = TechniqueScore("sbc_vedha", hits=10, total_events=10,
                           windows_scanned=100, total_windows=100)
        assert s.recall == pytest.approx(1.0)
        assert s.coverage == pytest.approx(1.0)
        assert s.lift == pytest.approx(1.0)

    def test_lift_above_one_when_recall_exceeds_coverage(self):
        # Found 8/10 events while scanning only 50% of windows -> lift=1.6
        s = TechniqueScore("latta", hits=8, total_events=10,
                           windows_scanned=50, total_windows=100)
        assert s.lift == pytest.approx(1.6)

    def test_lift_below_one_when_recall_below_coverage(self):
        # Found 2/10 events while scanning 80% of windows -> lift=0.25
        s = TechniqueScore("tara", hits=2, total_events=10,
                           windows_scanned=80, total_windows=100)
        assert s.lift == pytest.approx(0.25)

    def test_zero_hits_gives_zero_lift(self):
        s = TechniqueScore("progressed_saturn", hits=0, total_events=10,
                           windows_scanned=60, total_windows=100)
        assert s.lift == pytest.approx(0.0)
        assert s.recall == pytest.approx(0.0)

    def test_zero_windows_scanned_gives_zero_lift(self):
        s = TechniqueScore("sbc_vedha", hits=0, total_events=10,
                           windows_scanned=0, total_windows=100)
        assert s.lift == pytest.approx(0.0)
        assert s.coverage == pytest.approx(0.0)

    def test_zero_total_events_gives_zero_recall(self):
        s = TechniqueScore("latta", hits=0, total_events=0,
                           windows_scanned=50, total_windows=100)
        assert s.recall == pytest.approx(0.0)

    def test_precision_formula(self):
        # 8 hits in 50 scanned windows
        s = TechniqueScore("latta", hits=8, total_events=10,
                           windows_scanned=50, total_windows=100)
        assert s.precision == pytest.approx(8 / 50)


class TestTechniqueScoreValidation:
    def test_hits_exceeds_total_events_raises(self):
        with pytest.raises(ValueError, match="hits cannot exceed total_events"):
            TechniqueScore("x", hits=11, total_events=10,
                           windows_scanned=50, total_windows=100)

    def test_windows_scanned_exceeds_total_windows_raises(self):
        with pytest.raises(ValueError, match="windows_scanned cannot exceed total_windows"):
            TechniqueScore("x", hits=5, total_events=10,
                           windows_scanned=101, total_windows=100)

    def test_zero_total_windows_raises(self):
        with pytest.raises(ValueError, match="total_windows must be > 0"):
            TechniqueScore("x", hits=0, total_events=10,
                           windows_scanned=0, total_windows=0)

    def test_negative_hits_raises(self):
        with pytest.raises(ValueError, match="hits must be >= 0"):
            TechniqueScore("x", hits=-1, total_events=10,
                           windows_scanned=50, total_windows=100)


class TestEnsembleVerdict:
    def test_yes_when_3_techniques_agree(self):
        v = EnsembleVerdict(
            window_id="w1",
            techniques_fired=("sbc_vedha", "latta", "yearly_tara"),
            min_techniques=3,
        )
        assert v.verdict == "YES"
        assert v.is_yes is True

    def test_no_when_only_2_agree(self):
        v = EnsembleVerdict(
            window_id="w2",
            techniques_fired=("sbc_vedha", "latta"),
            min_techniques=3,
        )
        assert v.verdict == "NO"
        assert v.is_yes is False

    def test_no_when_zero_agree(self):
        v = EnsembleVerdict(window_id="w3", techniques_fired=(), min_techniques=3)
        assert v.verdict == "NO"

    def test_duplicate_techniques_counted_once(self):
        # Same technique appearing twice should not inflate count
        v = EnsembleVerdict(
            window_id="w4",
            techniques_fired=("sbc_vedha", "sbc_vedha", "latta"),
            min_techniques=3,
        )
        # Only 2 distinct techniques -> NO
        assert v.technique_count == 2
        assert v.verdict == "NO"

    def test_custom_threshold(self):
        v = EnsembleVerdict(
            window_id="w5",
            techniques_fired=("sbc_vedha", "latta"),
            min_techniques=2,
        )
        assert v.verdict == "YES"


class TestRankTechniques:
    def test_higher_lift_ranked_first(self):
        s1 = TechniqueScore("a", hits=2, total_events=10,
                            windows_scanned=20, total_windows=100)  # lift=1.0
        s2 = TechniqueScore("b", hits=8, total_events=10,
                            windows_scanned=50, total_windows=100)  # lift=1.6
        ranked = rank_techniques([s1, s2])
        assert ranked[0].technique == "b"

    def test_tie_broken_by_recall_then_name(self):
        s1 = TechniqueScore("z", hits=5, total_events=10,
                            windows_scanned=50, total_windows=100)  # recall=0.5, lift=1.0
        s2 = TechniqueScore("a", hits=5, total_events=10,
                            windows_scanned=50, total_windows=100)  # recall=0.5, lift=1.0
        ranked = rank_techniques([s1, s2])
        # Same lift+recall -> alphabetical by name
        assert ranked[0].technique == "a"


class TestCorpusSummary:
    def test_empty_input(self):
        result = corpus_summary([])
        assert result["mean_lift"] == pytest.approx(0.0)

    def test_mean_lift_calculated(self):
        s1 = TechniqueScore("a", hits=10, total_events=10,
                            windows_scanned=100, total_windows=100)  # lift=1.0
        s2 = TechniqueScore("b", hits=8, total_events=10,
                            windows_scanned=50, total_windows=100)   # lift=1.6
        result = corpus_summary([s1, s2])
        assert result["mean_lift"] == pytest.approx(1.3)
        assert result["max_lift"] == pytest.approx(1.6)
        assert result["min_lift"] == pytest.approx(1.0)
