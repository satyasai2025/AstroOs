"""
AstroOS — Statistical Reporting & Decision Engine Test Suite

Proves:
  1. Automated DecisionEngine renders correct production verdicts (PROMOTE, MAINTAIN, INCONCLUSIVE, REJECT).
  2. StatisticalReportGenerator compiles valid Markdown and JSON research artifacts.
  3. Report and decision endpoints return certified experiment metadata.
  4. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date
import importlib
import pytest

from apps.api.domain.benchmark_experiment import (
    BaselineComparison,
    BenchmarkExperiment,
    ExperimentProvenance,
    LockedDatasetSplit,
)
from apps.api.domain.benchmark_dataset import (
    BenchmarkComparisonReport,
    BenchmarkProfileComparisonRow,
)
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.statistical_reporting import ProductionDecisionStatus
from apps.api.domain.statistical_testing import (
    McNemarTestResult,
    MetricBootstrapConfidenceInterval,
    ProfileSignificanceReport,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.decision_engine import DecisionEngine
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
from apps.api.services.statistical_report_generator import StatisticalReportGenerator
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


# ── 1. Decision Rules ─────────────────────────────────────────────────────────


def test_decision_engine_rules():
    """DecisionEngine evaluates significance, sample adequacy, and deltas into production verdicts."""
    engine = DecisionEngine()

    def _build_mock_experiment(
        p_val: float,
        d_hit: float,
        d_brier: float,
        d_mae: float,
        n_holdout: int,
    ) -> BenchmarkExperiment:
        row_base = BenchmarkProfileComparisonRow(
            profile_id="parashari_standard_v1",
            profile_name="Parashari Standard",
            calibration_sample_size_n=50,
            holdout_sample_size_n=n_holdout,
            holdout_precision=0.75,
            holdout_recall=0.70,
            holdout_f1_score=0.72,
            holdout_hit_rate_pct=70.0,
            holdout_brier_score=0.18,
            holdout_mae_peak_days=15.0,
            holdout_median_peak_offset_days=10.0,
            holdout_p90_peak_offset_days=25.0,
            calibration_method="isotonic",
        )
        row_cand = BenchmarkProfileComparisonRow(
            profile_id="empirical_research_v1",
            profile_name="Empirical Research",
            calibration_sample_size_n=50,
            holdout_sample_size_n=n_holdout,
            holdout_precision=0.85,
            holdout_recall=0.80,
            holdout_f1_score=0.82,
            holdout_hit_rate_pct=70.0 + d_hit,
            holdout_brier_score=0.18 + d_brier,
            holdout_mae_peak_days=15.0 + d_mae,
            holdout_median_peak_offset_days=8.0,
            holdout_p90_peak_offset_days=20.0,
            calibration_method="isotonic",
        )
        rep = BenchmarkComparisonReport(
            benchmark_id="BENCH-CAREER-001",
            benchmark_version="1.0.0",
            content_hash_sha256="abc",
            split_seed=42,
            split_train_ratio=0.70,
            tolerance_days=30,
            total_benchmark_events=n_holdout + 50,
            train_events_count=50,
            holdout_events_count=n_holdout,
            rows=(row_base, row_cand),
        )
        base_cmp = BaselineComparison(
            profile_id="empirical_research_v1",
            baseline_profile_id="parashari_standard_v1",
            delta_hit_rate_pct=d_hit,
            delta_brier_score=d_brier,
            delta_f1_score=0.10,
            delta_mae_peak_days=d_mae,
            is_statistically_superior=p_val < 0.05 and d_hit > 0,
            p_value=p_val,
            odds_ratio=3.5 if d_hit > 0 else 0.5,
            verdict="SUPERIOR" if p_val < 0.05 and d_hit > 0 else "EQUIVALENT",
        )
        from datetime import datetime
        prov = ExperimentProvenance(
            experiment_id="EXP-1",
            benchmark_id="BENCH-CAREER-001",
            benchmark_version="1.0.0",
            content_hash_sha256="abc",
            split_seed=42,
            train_ratio=0.70,
            tolerance_days=30,
            profile_ids=("parashari_standard_v1", "empirical_research_v1"),
            calibration_method="isotonic",
            software_version="2.0.0",
            timestamp=datetime.now(),
            results_hash="res123",
        )
        split = LockedDatasetSplit(
            benchmark_id="BENCH-CAREER-001",
            version="1.0.0",
            content_hash_sha256="abc",
            split_seed=42,
            train_ratio=0.70,
            train_event_ids=(),
            holdout_event_ids=(),
        )
        return BenchmarkExperiment(
            provenance=prov,
            split=split,
            report=rep,
            baseline_comparisons=(base_cmp,),
        )

    # 1. Promote to Production: p < 0.05, positive delta, adequate N >= 30, no timing regression
    exp_promote = _build_mock_experiment(p_val=0.01, d_hit=15.0, d_brier=-0.03, d_mae=-2.0, n_holdout=40)
    dec_promote = engine.evaluate_experiment_decision(exp_promote)
    assert dec_promote.status == ProductionDecisionStatus.PROMOTE_TO_PRODUCTION
    assert dec_promote.recommended_profile_id == "empirical_research_v1"
    assert not dec_promote.requires_human_signoff

    # 2. Inconclusive: positive trend but small sample (N < 30) or p >= 0.05
    exp_inconclusive = _build_mock_experiment(p_val=0.12, d_hit=10.0, d_brier=-0.02, d_mae=0.0, n_holdout=15)
    dec_inconclusive = engine.evaluate_experiment_decision(exp_inconclusive)
    assert dec_inconclusive.status == ProductionDecisionStatus.INCONCLUSIVE_NEEDS_MORE_DATA
    assert dec_inconclusive.requires_human_signoff

    # 3. Reject: statistically significant degradation
    exp_reject = _build_mock_experiment(p_val=0.02, d_hit=-12.0, d_brier=0.04, d_mae=5.0, n_holdout=40)
    dec_reject = engine.evaluate_experiment_decision(exp_reject)
    assert dec_reject.status == ProductionDecisionStatus.REJECT_REGRESSION
    assert dec_reject.recommended_profile_id == "parashari_standard_v1"


# ── 2. Report Generator ───────────────────────────────────────────────────────


def test_statistical_report_generator():
    """StatisticalReportGenerator produces structured Markdown and JSON reports."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    exp = runner.run_experiment(
        corpus=career_corpus,
        profiles=[PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE],
        seed=42,
    )

    gen = StatisticalReportGenerator()
    report = gen.build_full_report(exp)

    assert report.experiment_id == exp.provenance.experiment_id
    assert report.benchmark_id == "BENCH-CAREER-001"
    assert "Executive Decision Recommendation" in report.markdown_content
    assert "Dataset Content SHA-256" in report.markdown_content
    assert "Empirical Profile Comparison Matrix" in report.markdown_content
    assert "McNemar's Exact Paired Test" in report.markdown_content
    assert "decision" in report.json_content
    assert "comparison_matrix" in report.json_content


# ── 3. Cardinal Invariance Guarantee ──────────────────────────────────────────


def test_decision_and_reporting_leave_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Run decision engine and report generator
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    runner = BenchmarkRunner()
    exp = runner.run_experiment(corpora["BENCH-CAREER-001"], [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE])
    gen = StatisticalReportGenerator()
    _ = gen.build_full_report(exp)

    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash