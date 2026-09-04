"""
AstroOS — Benchmark -> Knowledge Governance WIRING tests (Phase 8).

apps/api/domain/benchmark_validation_bridge.py already converts a real
BenchmarkExperiment into a RuleValidationSummary, and
KnowledgeReliabilityEngine.transition_lifecycle() already accepts such a
summary — but until now nothing connected the two, so every summary reaching
governance was hand-built with manually supplied numbers.

KnowledgeReliabilityEngine.build_validation_summary_from_experiment() is that
connection. These tests exercise the END-TO-END path:

    BenchmarkExperiment (real object)
        -> engine.build_validation_summary_from_experiment()
        -> RuleValidationSummary (metrics + provenance, no hand-entered numbers)
        -> engine.transition_lifecycle()
        -> RuleReliabilityRecord with EvidenceLevel

and confirm the wiring does NOT weaken any pre-existing governance guard.
"""

from __future__ import annotations

import uuid
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
from apps.api.domain.knowledge_reliability import (
    ActorRole,
    EvidenceLevel,
    RuleLifecycleState,
    UnauthorizedLifecycleTransitionError,
    ValidationPolicy,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine

_PROFILE = "PROFILE-UNDER-TEST"
_BENCH_ID = "BM-RULE-WIRING"
_BENCH_VERSION = "1.0.0"
_EXPERIMENT_ID = "EXP-WIRING-0001"


def _row(*, hit_rate_pct: float, brier: float, holdout_n: int) -> BenchmarkProfileComparisonRow:
    return BenchmarkProfileComparisonRow(
        profile_id=_PROFILE,
        profile_name="Profile Under Test",
        calibration_sample_size_n=holdout_n * 2,
        holdout_sample_size_n=holdout_n,
        holdout_precision=0.8,
        holdout_recall=0.7,
        holdout_f1_score=0.75,
        holdout_hit_rate_pct=hit_rate_pct,
        holdout_brier_score=brier,
        holdout_mae_peak_days=10.0,
        holdout_median_peak_offset_days=8.0,
        holdout_p90_peak_offset_days=25.0,
        calibration_method="isotonic",
    )


def _experiment(*, hit_rate_pct: float, brier: float, holdout_n: int, total_events: int) -> BenchmarkExperiment:
    """Builds a REAL BenchmarkExperiment — not a mock of arbitrary shape."""
    row = _row(hit_rate_pct=hit_rate_pct, brier=brier, holdout_n=holdout_n)
    report = BenchmarkComparisonReport(
        benchmark_id=_BENCH_ID,
        benchmark_version=_BENCH_VERSION,
        content_hash_sha256="a" * 64,
        split_seed=42,
        split_train_ratio=0.7,
        tolerance_days=30,
        total_benchmark_events=total_events,
        train_events_count=total_events - holdout_n,
        holdout_events_count=holdout_n,
        rows=(row,),
        executed_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
    )
    provenance = ExperimentProvenance(
        experiment_id=_EXPERIMENT_ID,
        benchmark_id=_BENCH_ID,
        benchmark_version=_BENCH_VERSION,
        content_hash_sha256="a" * 64,
        split_seed=42,
        train_ratio=0.7,
        tolerance_days=30,
        profile_ids=(_PROFILE,),
        calibration_method="isotonic",
        software_version="test",
        timestamp=datetime(2026, 8, 26, tzinfo=timezone.utc),
        results_hash=BenchmarkExperiment.compute_results_hash(report),
    )
    split = LockedDatasetSplit(
        benchmark_id=_BENCH_ID,
        version=_BENCH_VERSION,
        content_hash_sha256="a" * 64,
        split_seed=42,
        train_ratio=0.7,
        train_event_ids=tuple(f"train-{i}" for i in range(total_events - holdout_n)),
        holdout_event_ids=tuple(f"hold-{i}" for i in range(holdout_n)),
        created_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
    )
    return BenchmarkExperiment(provenance=provenance, split=split, report=report)


@pytest.fixture
def engine() -> KnowledgeReliabilityEngine:
    return KnowledgeReliabilityEngine()


@pytest.fixture
def policy(engine: KnowledgeReliabilityEngine) -> ValidationPolicy:
    p = ValidationPolicy(
        policy_id="POLICY-WIRING",
        name="Wiring test policy",
        min_applicable_cases=30,
        min_holdout_cases=20,
        min_hit_rate=0.60,
        max_brier_score=0.25,
        max_counterexample_ratio=0.40,
        require_independent_replication=False,
        require_holdout_split=True,
    )
    engine.register_policy(p)
    return p


# ── The wiring itself ─────────────────────────────────────────────────────────

def test_summary_is_derived_from_experiment_not_hand_entered(engine, policy):
    """Every metric on the summary traces to the experiment object."""
    exp = _experiment(hit_rate_pct=75.0, brier=0.15, holdout_n=40, total_events=120)

    summary = engine.build_validation_summary_from_experiment(
        rule_id="RULE-WIRE-1", experiment=exp, policy_id=policy.policy_id,
    )

    assert summary.empirical_hit_rate == pytest.approx(0.75)
    assert summary.brier_score == pytest.approx(0.15)
    assert summary.cases_tested == 40           # holdout N
    assert summary.applicable_cases == 120      # total corpus events
    assert summary.policy_id == policy.policy_id
    assert summary.rule_id == "RULE-WIRE-1"


def test_provenance_survives_the_wiring(engine, policy):
    """The summary is traceable back to the exact benchmark run."""
    exp = _experiment(hit_rate_pct=75.0, brier=0.15, holdout_n=40, total_events=120)

    summary = engine.build_validation_summary_from_experiment(
        rule_id="RULE-WIRE-2", experiment=exp, policy_id=policy.policy_id,
    )

    assert summary.benchmark_experiment_id == _EXPERIMENT_ID
    assert summary.dataset_id == _BENCH_ID
    assert summary.dataset_version == _BENCH_VERSION


def test_unknown_policy_is_rejected(engine):
    exp = _experiment(hit_rate_pct=75.0, brier=0.15, holdout_n=40, total_events=120)
    with pytest.raises(Exception) as ei:
        engine.build_validation_summary_from_experiment(
            rule_id="RULE-WIRE-3", experiment=exp, policy_id="NO-SUCH-POLICY",
        )
    assert "NO-SUCH-POLICY" in str(ei.value)


# ── End-to-end into the governance state machine ─────────────────────────────

def _document_rule(engine: KnowledgeReliabilityEngine, rule_id: str) -> None:
    """Register a rule at DOCUMENTED via the engine's own documentation path."""
    from apps.api.domain.knowledge_reliability import TechniqueFramework

    engine.document_rule(
        rule_id=rule_id,
        rule_name=f"Test rule {rule_id}",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=uuid.uuid4(),
        passage_reference="test passage",
        original_text_excerpt="test excerpt",
        extracted_by_actor_id="tester",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id=rule_id,
    )


def test_end_to_end_benchmark_to_validated(engine, policy):
    """
    Full path: real experiment -> derived summary -> governed transition.
    A HUMAN_EXPERT actor with passing metrics reaches VALIDATED.
    """
    rule_id = "RULE-E2E-PASS"
    _document_rule(engine, rule_id)
    engine.transition_lifecycle(
        rule_id=rule_id, target_state=RuleLifecycleState.REVIEWED,
        actor_id="reviewer-1", actor_role=ActorRole.HUMAN_EXPERT,
    )

    exp = _experiment(hit_rate_pct=78.0, brier=0.12, holdout_n=40, total_events=120)
    summary = engine.build_validation_summary_from_experiment(
        rule_id=rule_id, experiment=exp, policy_id=policy.policy_id,
    )

    record = engine.transition_lifecycle(
        rule_id=rule_id,
        target_state=RuleLifecycleState.VALIDATED,
        actor_id="research-engine-1",
        actor_role=ActorRole.RESEARCH_ENGINE,
        validation_summary=summary,
        policy_id=policy.policy_id,
    )

    assert record.lifecycle_state == RuleLifecycleState.VALIDATED
    assert record.validation_summary is not None
    # provenance carried all the way into the governance record
    assert record.validation_summary.benchmark_experiment_id == _EXPERIMENT_ID
    assert record.evidence_level != EvidenceLevel.UNVALIDATED


def test_ai_actor_still_cannot_validate_through_this_path(engine, policy):
    """
    The wiring must not become a loophole: an AI actor is still barred from
    VALIDATED even when holding a perfectly good benchmark-derived summary.
    """
    rule_id = "RULE-E2E-AI"
    _document_rule(engine, rule_id)
    engine.transition_lifecycle(
        rule_id=rule_id, target_state=RuleLifecycleState.REVIEWED,
        actor_id="reviewer-1", actor_role=ActorRole.HUMAN_EXPERT,
    )

    exp = _experiment(hit_rate_pct=95.0, brier=0.02, holdout_n=40, total_events=120)
    summary = engine.build_validation_summary_from_experiment(
        rule_id=rule_id, experiment=exp, policy_id=policy.policy_id,
    )

    with pytest.raises(UnauthorizedLifecycleTransitionError):
        engine.transition_lifecycle(
            rule_id=rule_id,
            target_state=RuleLifecycleState.VALIDATED,
            actor_id="ai-agent-1",
            actor_role=ActorRole.AI_AGENT,
            validation_summary=summary,
            policy_id=policy.policy_id,
        )


def test_insufficient_sample_blocks_validation_end_to_end(engine, policy):
    """
    Sample-size protection survives the wiring: a tiny holdout with perfect
    metrics must not reach VALIDATED, even for a human expert.
    """
    rule_id = "RULE-E2E-SMALL"
    _document_rule(engine, rule_id)
    engine.transition_lifecycle(
        rule_id=rule_id, target_state=RuleLifecycleState.REVIEWED,
        actor_id="reviewer-1", actor_role=ActorRole.HUMAN_EXPERT,
    )

    # 5 total events, 2 holdout — far below policy minimums (30 / 20)
    exp = _experiment(hit_rate_pct=100.0, brier=0.0, holdout_n=2, total_events=5)
    summary = engine.build_validation_summary_from_experiment(
        rule_id=rule_id, experiment=exp, policy_id=policy.policy_id,
    )

    assert summary.applicable_cases < policy.min_applicable_cases

    # ValidationPolicyViolationError specifically — NOT an authority error.
    # Using RESEARCH_ENGINE (an actor that IS allowed to validate) ensures this
    # test fails on sample size, not on permissions; otherwise it would pass
    # for the wrong reason and silently stop testing the sample-size guard.
    from apps.api.domain.knowledge_reliability import ValidationPolicyViolationError

    with pytest.raises(ValidationPolicyViolationError):
        engine.transition_lifecycle(
            rule_id=rule_id,
            target_state=RuleLifecycleState.VALIDATED,
            actor_id="research-engine-1",
            actor_role=ActorRole.RESEARCH_ENGINE,
            validation_summary=summary,
            policy_id=policy.policy_id,
        )

    assert engine.get_rule(rule_id).lifecycle_state != RuleLifecycleState.VALIDATED
