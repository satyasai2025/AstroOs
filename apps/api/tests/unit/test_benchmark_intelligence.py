"""
AstroOS — Benchmark Intelligence & Descriptive Trend Analytics Test Suite

Proves:
  1. Mathematical Stability Index composite formula calculation & bounds [0.0, 1.0].
  2. Descriptive profile performance trajectory & summary statistics (mean, std dev, range).
  3. Corpus demographic composition & Rodden rating distributions.
  4. End-to-end intelligence report aggregation from persistence & registries.
  5. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date
import importlib
import pytest

from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.continuous_monitoring_repository import ContinuousMonitoringRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.intelligence_analytics_service import IntelligenceAnalyticsService
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()
    BenchmarkExperimentRepository.clear_in_memory()
    ProductionGovernanceRepository.clear_in_memory()
    ContinuousMonitoringRepository.clear_in_memory()

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


# ── 1. Mathematical Stability Index Formula ────────────────────────────────────


def test_stability_index_mathematical_formulation():
    """Validates the exact mathematical formula components and bounds for System Stability Index."""
    # Case 1: Perfectly consistent runs (0 std dev, 0 regressions)
    res_perfect = IntelligenceAnalyticsService.calculate_stability_index(
        hit_rates=[75.0, 75.0, 75.0, 75.0],
        brier_scores=[0.18, 0.18, 0.18, 0.18],
        regression_flags=[False, False, False, False],
    )
    assert res_perfect.composite_stability_index == 1.0
    assert res_perfect.hit_rate_stability_component == 1.0
    assert res_perfect.brier_stability_component == 1.0
    assert res_perfect.regression_free_component == 1.0
    assert res_perfect.std_hit_rate == 0.0
    assert res_perfect.std_brier == 0.0

    # Case 2: Volatile runs with regression
    res_volatile = IntelligenceAnalyticsService.calculate_stability_index(
        hit_rates=[60.0, 90.0],
        brier_scores=[0.10, 0.30],
        regression_flags=[False, True],
    )
    assert 0.0 <= res_volatile.composite_stability_index <= 1.0
    assert res_volatile.regression_free_component == 0.5
    assert res_volatile.std_hit_rate > 0.0
    assert res_volatile.std_brier > 0.0
    # S_hit penalty = max(0.0, 1.0 - 21.21 / 15.0) -> 0.0
    assert res_volatile.hit_rate_stability_component == 0.0


# ── 2. Descriptive Trajectory & Summary Statistics ────────────────────────────


@pytest.mark.asyncio
async def test_descriptive_profile_trajectory_aggregation():
    """Intelligence service aggregates empirical holdout observations without causal assertions."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    exp_repo = BenchmarkExperimentRepository()

    # Save 2 distinct historical runs
    exp1 = runner.run_experiment(career_corpus, [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE], tolerance_days=30, seed=42)
    exp2 = runner.run_experiment(career_corpus, [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE], tolerance_days=15, seed=100)

    await exp_repo.save_experiment(exp1, duration_ms=120.0)
    await exp_repo.save_experiment(exp2, duration_ms=130.0)

    service = IntelligenceAnalyticsService(
        experiment_repo=exp_repo,
        registry=registry,
        runner=runner,
    )

    report = await service.generate_intelligence_report("BENCH-CAREER-001")
    assert report.benchmark_id == "BENCH-CAREER-001"
    assert report.total_experiments == 2
    assert "parashari_standard_v1" in report.profile_summaries
    assert "empirical_research_v1" in report.profile_summaries

    p_summary = report.profile_summaries["empirical_research_v1"]
    assert p_summary.total_evaluations == 2
    assert len(p_summary.trajectory) == 2
    assert p_summary.min_hit_rate_pct <= p_summary.mean_hit_rate_pct <= p_summary.max_hit_rate_pct
    assert p_summary.min_brier_score <= p_summary.mean_brier_score <= p_summary.max_brier_score


# ── 3. Corpus Demographics & Quality Composition ──────────────────────────────


@pytest.mark.asyncio
async def test_corpus_demographics_aggregation():
    """Intelligence service computes Rodden ratings and source verification distribution."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    loader.load_and_lock_all_canonical_corpora()

    service = IntelligenceAnalyticsService(registry=registry)
    report = await service.generate_intelligence_report("BENCH-CAREER-001")

    demographics = report.corpus_demographics
    assert demographics.total_verified_events > 0
    assert demographics.content_hash_sha256 != ""
    assert len(demographics.birth_confidence_distribution) > 0
    assert len(demographics.event_verification_distribution) > 0


# ── 4. Cardinal Invariance Guarantee ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_intelligence_analytics_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Generate intelligence analytics report
    service = IntelligenceAnalyticsService()
    _ = await service.generate_intelligence_report("BENCH-CAREER-001")

    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash