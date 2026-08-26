"""
Tests for apps.api.domain.benchmark_validation_bridge — the governance
bridge connecting real BenchmarkExperiment results to RuleValidationSummary
/ RuleLifecycleState / EvidenceLevel.

Each test maps directly to one of the six hard requirements from the task:
  1. no fabricated-metric parameters exist on the bridge functions
  2. all metrics preserved (mapped fields + JSON provenance extraction)
  3. provenance (experiment/corpus IDs) preserved exactly
  4. deterministic decision
  5. insufficient sample size never produces VALIDATED
  6. never CANONICAL/PROMOTED
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest

from apps.api.domain.benchmark_dataset import (
    BenchmarkComparisonReport,
    BenchmarkProfileComparisonRow,
)
from apps.api.domain.benchmark_experiment import (
    BenchmarkExperiment,
    ExperimentProvenance,
    LockedDatasetSplit,
)
from apps.api.domain.benchmark_validation_bridge import (
    BenchmarkValidationBridgeError,
    BridgeDecision,
    build_validation_decision_from_benchmark,
    build_validation_summary_from_benchmark,
    extract_full_metric_provenance,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    RuleLifecycleState,
    ValidationPolicy,
)


def _make_row(
    profile_id: str = "PARASHARI_STANDARD",
    holdout_n: int = 150,
    hit_rate_pct: float = 78.0,
    brier: float = 0.15,
) -> BenchmarkProfileComparisonRow:
    return BenchmarkProfileComparisonRow(
        profile_id=profile_id,
        profile_name="Parashari Standard",
        calibration_sample_size_n=350,
        holdout_sample_size_n=holdout_n,
        holdout_precision=0.80,
        holdout_recall=0.75,
        holdout_f1_score=0.77,
        holdout_hit_rate_pct=hit_rate_pct,
        holdout_brier_score=brier,
        holdout_mae_peak_days=4.2,
        holdout_median_peak_offset_days=3.0,
        holdout_p90_peak_offset_days=9.5,
        calibration_method="isotonic",
    )


def _make_experiment(
    rows,
    experiment_id: str = "EXP-TEST-0001",
    benchmark_id: str = "career_promotions_bench_v1",
    benchmark_version: str = "1.0.0",
    total_events: int = 500,
    train_events: int = 350,
    holdout_events: int = 150,
) -> BenchmarkExperiment:
    report = BenchmarkComparisonReport(
        benchmark_id=benchmark_id,
        benchmark_version=benchmark_version,
        content_hash_sha256="a" * 64,
        split_seed=42,
        split_train_ratio=0.7,
        tolerance_days=7,
        total_benchmark_events=total_events,
        train_events_count=train_events,
        holdout_events_count=holdout_events,
        rows=tuple(rows),
        executed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    provenance = ExperimentProvenance(
        experiment_id=experiment_id,
        benchmark_id=benchmark_id,
        benchmark_version=benchmark_version,
        content_hash_sha256="a" * 64,
        split_seed=42,
        train_ratio=0.7,
        tolerance_days=7,
        profile_ids=tuple(r.profile_id for r in rows),
        calibration_method="isotonic",
        software_version="test-0.0.1",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        results_hash="b" * 64,
    )
    split = LockedDatasetSplit(
        benchmark_id=benchmark_id,
        version=benchmark_version,
        content_hash_sha256="a" * 64,
        split_seed=42,
        train_ratio=0.7,
        train_event_ids=tuple(f"EVT-{i}" for i in range(train_events)),
        holdout_event_ids=tuple(f"EVT-H-{i}" for i in range(holdout_events)),
    )
    return BenchmarkExperiment(provenance=provenance, split=split, report=report)


_POLICY = ValidationPolicy(
    policy_id="POLICY-DEFAULT",
    name="Default Validation Policy",
    min_applicable_cases=30,
    min_holdout_cases=100,
    min_hit_rate=0.60,
    max_brier_score=0.25,
    max_counterexample_ratio=0.15,
    require_independent_replication=True,
    require_holdout_split=True,
)


# ── Requirement 1: no fabricated-metric parameters ──────────────────────────

def test_bridge_functions_accept_no_metric_parameters():
    forbidden = {
        "precision", "recall", "f1", "f1_score", "hit_rate", "brier_score",
        "sample_size", "cases_tested", "applicable_cases", "empirical_hit_rate",
    }
    for fn in (build_validation_summary_from_benchmark, build_validation_decision_from_benchmark):
        params = set(inspect.signature(fn).parameters.keys())
        assert params & forbidden == set(), (
            f"{fn.__name__} unexpectedly accepts metric parameters: {params & forbidden}"
        )
        # The only parameters allowed are identifiers/objects, never raw metrics.
        assert params == {"experiment", "rule_id", "policy", "profile_id"}


def test_bridge_rejects_arbitrary_kwargs():
    with pytest.raises(TypeError):
        build_validation_summary_from_benchmark(  # type: ignore[call-arg]
            experiment=_make_experiment([_make_row()]),
            rule_id="RULE-1",
            policy=_POLICY,
            hit_rate=0.99,  # fabricated metric — must be rejected at the type level
        )


# ── Requirement 2/3: metrics + provenance preserved ─────────────────────────

def test_sufficient_sample_good_metrics_produces_validated_with_preserved_metrics():
    row = _make_row(hit_rate_pct=78.0, brier=0.15, holdout_n=150)
    experiment = _make_experiment([row], experiment_id="EXP-GOOD-0001")

    decision = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)

    assert decision.lifecycle_state == RuleLifecycleState.VALIDATED
    assert decision.evidence_level in (EvidenceLevel.HIGH, EvidenceLevel.MODERATE)

    summary = decision.summary
    assert summary.cases_tested == 150
    assert summary.applicable_cases == 500
    assert summary.empirical_hit_rate == pytest.approx(0.78)
    assert summary.brier_score == pytest.approx(0.15)
    assert summary.rule_id == "RULE-3"
    assert summary.policy_id == _POLICY.policy_id


def test_provenance_matches_source_experiment_exactly():
    row = _make_row()
    experiment = _make_experiment(
        [row],
        experiment_id="EXP-PROV-9999",
        benchmark_id="marriage_timing_bench_v1",
        benchmark_version="2.3.1",
    )

    summary = build_validation_summary_from_benchmark(experiment, "RULE-X", _POLICY)

    assert summary.benchmark_experiment_id == "EXP-PROV-9999"
    assert summary.dataset_id == "marriage_timing_bench_v1"
    assert summary.dataset_version == "2.3.1"


def test_full_metric_provenance_extraction_preserves_precision_recall_f1():
    row = _make_row()
    experiment = _make_experiment([row], experiment_id="EXP-META-0001")

    meta = extract_full_metric_provenance(experiment)

    assert meta["holdout_precision"] == row.holdout_precision
    assert meta["holdout_recall"] == row.holdout_recall
    assert meta["holdout_f1_score"] == row.holdout_f1_score
    assert meta["experiment_id"] == "EXP-META-0001"
    assert meta["benchmark_id"] == experiment.provenance.benchmark_id
    assert meta["results_hash"] == experiment.provenance.results_hash


# ── Requirement 5: insufficient sample size never produces VALIDATED ────────

def test_insufficient_applicable_cases_never_validated_even_with_perfect_metrics():
    row = _make_row(hit_rate_pct=100.0, brier=0.0, holdout_n=150)
    experiment = _make_experiment([row], total_events=10)  # below min_applicable_cases=30

    decision = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)

    assert decision.lifecycle_state != RuleLifecycleState.VALIDATED
    assert decision.lifecycle_state == RuleLifecycleState.UNVALIDATED
    assert decision.evidence_level == EvidenceLevel.INSUFFICIENT_DATA


def test_insufficient_holdout_cases_never_validated_even_with_perfect_metrics():
    row = _make_row(hit_rate_pct=100.0, brier=0.0, holdout_n=10)  # below min_holdout_cases=100
    experiment = _make_experiment([row], total_events=500, holdout_events=10)

    decision = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)

    assert decision.lifecycle_state != RuleLifecycleState.VALIDATED
    assert decision.lifecycle_state == RuleLifecycleState.UNVALIDATED
    assert decision.evidence_level == EvidenceLevel.INSUFFICIENT_DATA


# ── Requirement 6: never CANONICAL or PROMOTED ───────────────────────────────

@pytest.mark.parametrize(
    "hit_rate_pct,brier,holdout_n,total_events",
    [
        (95.0, 0.05, 150, 500),   # excellent metrics, sufficient sample
        (10.0, 0.90, 150, 500),   # terrible metrics, sufficient sample
        (78.0, 0.15, 5, 10),      # good metrics, insufficient sample
        (50.0, 0.25, 100, 30),    # borderline metrics, borderline sample
    ],
)
def test_never_produces_canonical_or_promoted(hit_rate_pct, brier, holdout_n, total_events):
    row = _make_row(hit_rate_pct=hit_rate_pct, brier=brier, holdout_n=holdout_n)
    experiment = _make_experiment([row], total_events=total_events, holdout_events=holdout_n)

    decision = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)

    assert decision.lifecycle_state not in (
        RuleLifecycleState.CANONICAL,
        RuleLifecycleState.PROMOTED,
    )


def test_clear_contradiction_maps_to_contradicted_not_canonical():
    row = _make_row(hit_rate_pct=20.0, brier=0.4, holdout_n=150)
    experiment = _make_experiment([row], total_events=500)

    decision = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)

    assert decision.lifecycle_state == RuleLifecycleState.CONTRADICTED
    assert decision.lifecycle_state not in (
        RuleLifecycleState.CANONICAL,
        RuleLifecycleState.PROMOTED,
    )


# ── Requirement 4: deterministic ─────────────────────────────────────────────

def test_deterministic_same_input_same_output():
    row = _make_row(hit_rate_pct=78.0, brier=0.15, holdout_n=150)
    experiment = _make_experiment([row], experiment_id="EXP-DETERMINISM-0001")

    d1 = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)
    d2 = build_validation_decision_from_benchmark(experiment, "RULE-3", _POLICY)

    assert d1.lifecycle_state == d2.lifecycle_state
    assert d1.evidence_level == d2.evidence_level
    assert d1.summary.cases_tested == d2.summary.cases_tested
    assert d1.summary.applicable_cases == d2.summary.applicable_cases
    assert d1.summary.empirical_hit_rate == d2.summary.empirical_hit_rate
    assert d1.summary.brier_score == d2.summary.brier_score
    assert d1.summary.benchmark_experiment_id == d2.summary.benchmark_experiment_id
    assert d1.summary.dataset_id == d2.summary.dataset_id
    # validated_at is real wall-clock time and intentionally excluded from
    # the determinism guarantee — only the decision itself must be stable.


# ── Multi-profile selection / error handling ─────────────────────────────────

def test_multi_profile_experiment_requires_profile_id():
    rows = [_make_row(profile_id="PROFILE_A"), _make_row(profile_id="PROFILE_B")]
    experiment = _make_experiment(rows)

    with pytest.raises(BenchmarkValidationBridgeError):
        build_validation_summary_from_benchmark(experiment, "RULE-3", _POLICY)

    # Explicit profile_id resolves it correctly.
    summary = build_validation_summary_from_benchmark(
        experiment, "RULE-3", _POLICY, profile_id="PROFILE_B"
    )
    assert summary.rule_id == "RULE-3"


def test_empty_rows_raises():
    experiment = _make_experiment([])
    with pytest.raises(BenchmarkValidationBridgeError):
        build_validation_summary_from_benchmark(experiment, "RULE-3", _POLICY)
