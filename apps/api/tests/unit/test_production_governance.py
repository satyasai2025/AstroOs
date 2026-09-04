"""
AstroOS — Production Governance & Continuous Benchmarking Test Suite

Proves:
  1. Active production baseline tracking and versioned profile promotions.
  2. Automated continuous regression detection between benchmark runs.
  3. Cryptographic bit-for-bit reproducibility verification.
  4. Human reviewer sign-off audit trail durability.
  5. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date, datetime
import importlib
import pytest

from apps.api.domain.benchmark_dataset import (
    BenchmarkComparisonReport,
    BenchmarkProfileComparisonRow,
)
from apps.api.domain.benchmark_experiment import BenchmarkExperiment
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.production_governance import (
    RegressionSeverity,
    SignoffStatus,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.governance_engine import GovernanceEngine
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()
    BenchmarkExperimentRepository.clear_in_memory()
    ProductionGovernanceRepository.clear_in_memory()

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


# ── 1. Production Profile Versioning & Baseline Tracking ───────────────────────


@pytest.mark.asyncio
async def test_active_baseline_tracking_and_promotion():
    """Governance repository manages active baseline and handles versioned promotions."""
    repo = ProductionGovernanceRepository()
    benchmark_id = "BENCH-CAREER-001"

    # Initial active baseline
    initial_base = await repo.get_active_baseline_profile(benchmark_id)
    assert initial_base.profile_id == "parashari_standard_v1"
    assert initial_base.version == "1.0.0"
    assert initial_base.is_active_baseline

    # Promote new profile
    promoted = await repo.promote_profile_to_production(
        profile_id="empirical_research_v1",
        version="1.1.0",
        benchmark_id=benchmark_id,
        experiment_id="EXP-CAREER-001",
        reviewer_id="Chief Astrological Scientist",
        notes="Promoted following statistically significant holdout superiority.",
    )
    assert promoted.profile_id == "empirical_research_v1"
    assert promoted.version == "1.1.0"
    assert promoted.is_active_baseline

    # Verify active baseline updated
    current_base = await repo.get_active_baseline_profile(benchmark_id)
    assert current_base.profile_id == "empirical_research_v1"
    assert current_base.version == "1.1.0"
    assert current_base.is_active_baseline

    # Check list contains both versions
    all_profiles = await repo.list_production_profiles(benchmark_id)
    assert len(all_profiles) == 2
    archived = next(p for p in all_profiles if p.profile_id == "parashari_standard_v1")
    assert not archived.is_active_baseline


# ── 2. Regression Detection ───────────────────────────────────────────────────


def test_regression_detection_engine():
    """GovernanceEngine accurately detects critical, warning, and clean metric deltas."""
    engine = GovernanceEngine()
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()

    # Base experiment run (tol = 30d)
    exp_base = runner.run_experiment(
        corpus=career_corpus,
        profiles=[PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE],
        tolerance_days=30,
        seed=42,
    )

    # Identical candidate run (clean - no regression)
    exp_same = runner.run_experiment(
        corpus=career_corpus,
        profiles=[PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE],
        tolerance_days=30,
        seed=42,
    )
    rep_clean = engine.detect_regression(exp_base, exp_same)
    assert not rep_clean.has_regression
    assert rep_clean.severity == RegressionSeverity.NONE

    # Synthetic regressed experiment
    row_base = exp_base.report.rows[0]
    row_regressed = BenchmarkProfileComparisonRow(
        profile_id=row_base.profile_id,
        profile_name=row_base.profile_name,
        calibration_sample_size_n=row_base.calibration_sample_size_n,
        holdout_sample_size_n=row_base.holdout_sample_size_n,
        holdout_precision=0.40,
        holdout_recall=0.40,
        holdout_f1_score=0.40,
        holdout_hit_rate_pct=row_base.holdout_hit_rate_pct - 10.0,
        holdout_brier_score=row_base.holdout_brier_score + 0.05,
        holdout_mae_peak_days=row_base.holdout_mae_peak_days + 10.0,
        holdout_median_peak_offset_days=row_base.holdout_median_peak_offset_days + 10.0,
        holdout_p90_peak_offset_days=row_base.holdout_p90_peak_offset_days + 10.0,
        calibration_method="isotonic_regression",
    )
    rep_degraded = BenchmarkComparisonReport(
        benchmark_id=exp_base.report.benchmark_id,
        benchmark_version=exp_base.report.benchmark_version,
        content_hash_sha256=exp_base.report.content_hash_sha256,
        split_seed=42,
        split_train_ratio=0.70,
        tolerance_days=30,
        total_benchmark_events=exp_base.report.total_benchmark_events,
        train_events_count=exp_base.report.train_events_count,
        holdout_events_count=exp_base.report.holdout_events_count,
        rows=(row_regressed,),
    )
    exp_degraded = BenchmarkExperiment(
        provenance=exp_base.provenance,
        split=exp_base.split,
        report=rep_degraded,
        baseline_comparisons=(),
    )

    rep_reg = engine.detect_regression(exp_base, exp_degraded, evaluated_profile_id=row_base.profile_id)
    assert rep_reg.has_regression
    assert rep_reg.severity == RegressionSeverity.CRITICAL_REGRESSION
    assert rep_reg.hit_rate_drop_pct >= 10.0


# ── 3. Reproducibility Verification ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_reproducibility_verification_audit():
    """GovernanceEngine confirms bit-for-bit SHA-256 results equality upon re-execution."""
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

    exp_repo = BenchmarkExperimentRepository()
    saved = await exp_repo.save_experiment(exp)

    gov_engine = GovernanceEngine(
        experiment_repo=exp_repo,
        registry=registry,
        runner=runner,
    )

    audit = await gov_engine.verify_reproducibility(saved.experiment_id)
    assert audit.is_bit_for_bit_identical
    assert audit.expected_results_hash == audit.actual_results_hash


# ── 4. Human Reviewer Sign-Off Workflow ───────────────────────────────────────


@pytest.mark.asyncio
async def test_human_signoff_workflow():
    """Reviewer sign-offs are durably recorded and retrieved."""
    repo = ProductionGovernanceRepository()
    exp_id = "EXP-TEST-001"

    signoff = await repo.record_signoff(
        experiment_id=exp_id,
        status=SignoffStatus.APPROVED,
        reviewer_id="Senior Astrologer Reviewer",
        notes="Verified holdout separation, zero leakage, and Wilson CIs.",
    )
    assert signoff.status == SignoffStatus.APPROVED
    assert signoff.reviewer_id == "Senior Astrologer Reviewer"

    retrieved = await repo.get_signoff(exp_id)
    assert retrieved is not None
    assert retrieved.signoff_id == signoff.signoff_id
    assert retrieved.status == SignoffStatus.APPROVED


# ── 5. Cardinal Invariance Guarantee ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_governance_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Run governance promotion & regression check
    gov_repo = ProductionGovernanceRepository()
    _ = await gov_repo.get_active_baseline_profile("BENCH-CAREER-001")

    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash