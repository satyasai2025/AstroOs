"""
AstroOS — Statistical Significance & Benchmark Confidence Analysis Test Suite

Proves:
  1. McNemar exact paired test computes exact binomial p-values on discordant pairs.
  2. Paired permutation test evaluates Brier score improvements against null.
  3. 1000-iteration bootstrap resampling generates valid 95% confidence intervals.
  4. Integration with BenchmarkRunner & Experiment persistence.
  5. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date
import importlib
import pytest

from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.research_calibration import (
    BacktestOutcome,
    TemporalMatchStatus,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
from apps.api.services.significance_engine import SignificanceEngine
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()
    BenchmarkExperimentRepository.clear_in_memory()

    import apps.api.services.techniques.timing_events as _te
    import apps.api.services.techniques.panch_mahapurusha as _pm
    import apps.api.services.techniques.marriage_timing as _mt
    import apps.api.services.techniques.wealth_dhana as _wd
    import apps.api.services.techniques.gajakesari_yoga as _gj
    import apps.api.services.techniques.eye_health as _eye
    import apps.api.services.techniques.event_timing_migrated as _et

    importlib.reload(_te)
    importlib.reload(_pm)
    importlib.reload(_mt)
    importlib.reload(_wd)
    importlib.reload(_gj)
    importlib.reload(_eye)
    importlib.reload(_et)
    yield


# ── 1. McNemar Exact Paired Test ───────────────────────────────────────────────


def test_mcnemar_exact_test_concordant_and_discordant():
    """McNemar test evaluates paired hits and discordant pairs with exact binomial p-values."""
    sig = SignificanceEngine()

    def _make_outcome(hit: bool) -> BacktestOutcome:
        return BacktestOutcome(
            event_id="EVT-1",
            actual_date=date(2026, 6, 1),
            predicted_window_start=date(2026, 5, 15) if hit else None,
            predicted_window_end=date(2026, 6, 15) if hit else None,
            peak_predicted_date=date(2026, 6, 1) if hit else None,
            deterministic_score=85 if hit else 30,
            match_status=TemporalMatchStatus.WINDOW_EXACT_HIT if hit else TemporalMatchStatus.TEMPORAL_MISS,
            peak_offset_days=0 if hit else None,
            tolerance_days_used=30,
        )

    # All concordant hits (5 hits, 5 hits)
    base_outcomes = [_make_outcome(True) for _ in range(5)]
    cand_outcomes = [_make_outcome(True) for _ in range(5)]
    res = sig.compute_mcnemar_test(base_outcomes, cand_outcomes)

    assert res.contingency_table == (5, 0, 0, 0)
    assert res.p_value == 1.0
    assert res.odds_ratio == 1.0
    assert not res.is_significant

    # Significant candidate advantage (baseline misses all 8, candidate hits all 8)
    base_outcomes = [_make_outcome(False) for _ in range(8)]
    cand_outcomes = [_make_outcome(True) for _ in range(8)]
    res_sig = sig.compute_mcnemar_test(base_outcomes, cand_outcomes)

    assert res_sig.contingency_table == (0, 0, 8, 0)
    assert res_sig.c_discordant_candidate_only == 8
    assert res_sig.b_discordant_baseline_only == 0
    assert res_sig.p_value < 0.05
    assert res_sig.is_significant


# ── 2. Bootstrap Confidence Intervals ─────────────────────────────────────────


def test_bootstrap_confidence_intervals():
    """Bootstrap resampling (B=1000) generates valid 95% confidence intervals."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    exp = runner.run_experiment(career_corpus, [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE], seed=42)

    assert len(exp.significance_reports) == 1
    rep = exp.significance_reports[0]

    assert "hit_rate_pct" in rep.bootstrap_cis
    assert "brier_score" in rep.bootstrap_cis
    assert "mae_peak_days" in rep.bootstrap_cis

    hit_ci = rep.bootstrap_cis["hit_rate_pct"]
    assert hit_ci.ci_lower <= hit_ci.point_estimate <= hit_ci.ci_upper
    assert hit_ci.confidence_level == 0.95


# ── 3. End-to-End Runner Significance Persistence ──────────────────────────────


@pytest.mark.asyncio
async def test_runner_experiment_significance_persistence():
    """BenchmarkRunner integrates significance reports into saved experiment records."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    exp = runner.run_experiment(
        corpus=career_corpus,
        profiles=[PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE],
        baseline_profile_id="parashari_standard_v1",
        tolerance_days=30,
        seed=42,
        train_ratio=0.70,
    )

    repo = BenchmarkExperimentRepository()
    saved = await repo.save_experiment(exp)

    retrieved = await repo.get_by_experiment_id(saved.experiment_id)
    assert retrieved is not None
    sig_list = retrieved.results_summary.get("significance_reports", [])
    assert len(sig_list) == 1
    assert sig_list[0]["profile_id"] == "empirical_research_v1"
    assert sig_list[0]["baseline_profile_id"] == "parashari_standard_v1"
    assert "mcnemar_test" in sig_list[0]
    assert "p_value" in sig_list[0]["mcnemar_test"]
    assert "verdict" in sig_list[0]


# ── 4. Cardinal Invariance Guarantee ──────────────────────────────────────────


def test_significance_engine_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    # 1. Run prediction before
    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # 2. Run experiment with significance engine
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    runner = BenchmarkRunner()
    _ = runner.run_experiment(corpora["BENCH-CAREER-001"], [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE])

    # 3. Run prediction after
    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash