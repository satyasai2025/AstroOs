"""
AstroOS — Benchmark -> Knowledge Governance Bridge

Connects the real prediction-rule benchmark system
(`apps.api.domain.benchmark_experiment.BenchmarkExperiment`, produced by
`apps.api.services.benchmark_runner.BenchmarkRunner`) to the knowledge
governance / validation system
(`apps.api.domain.knowledge_reliability.RuleValidationSummary`).

Before this module existed, every `RuleValidationSummary` in the codebase
was hand-constructed with manually-supplied numbers — nothing tied a
governance record back to an actual benchmark run. This module is the
ONLY place that derives a `RuleValidationSummary` from a real
`BenchmarkExperiment`.

Design rules (do not weaken these):

1. The only source of metrics is the `BenchmarkExperiment` object itself.
   There is no way to pass a precision/recall/F1/hit-rate/Brier/sample-size
   number directly — a caller who wants to fabricate a result has to
   fabricate an entire `BenchmarkExperiment` (with its nested
   `ExperimentProvenance`, `LockedDatasetSplit`, and
   `BenchmarkComparisonReport`), not just pass a float.

2. The decision function is pure and deterministic: same
   `(experiment, rule_id, policy, profile_id)` in, same
   `(RuleLifecycleState, EvidenceLevel)` out. No randomness, no
   wall-clock branching. (`validated_at` still records real time, but it
   does not participate in the decision.)

3. Insufficient sample size is checked FIRST, before any metric is even
   looked at, and always forces `RuleLifecycleState.UNVALIDATED` /
   `EvidenceLevel.INSUFFICIENT_DATA` — no formula can accidentally route
   around it.

4. This module can only ever construct `RuleLifecycleState.UNVALIDATED`,
   `RuleLifecycleState.VALIDATED`, or `RuleLifecycleState.CONTRADICTED`
   (`DOCUMENTED` is used only as the fallback carried over from the
   input record, never invented here). `PROMOTED` and `CANONICAL` are
   never referenced anywhere in this file's logic — promotion is a
   separate, explicitly human-gated governance action
   (`EXPECTED_PRE_PROMOTION_STATES == ["VALIDATED"]` in
   `knowledge_reliability.py`) that this bridge does not perform.

Mapping notes (why each field is filled the way it is):

  - `RuleValidationSummary` has no fields for precision, recall, F1, or
    MAE individually — only `empirical_hit_rate` and `brier_score`. It
    is a frozen dataclass we are not allowed to modify. Rather than
    silently dropping precision/recall/F1/MAE, `extract_full_metric_provenance`
    below returns the complete metric set as a plain dict, suitable for
    storage in `KnowledgeRuleReliabilityModel.validation_summary_json`
    (an open JSON column) alongside the summary — the one JSON-capable
    place in the persistence layer that can hold it without lossy
    mapping.
  - `applicable_cases` = total events in the locked benchmark corpus
    (train + holdout) — i.e. how many cases the rule's profile was
    actually run against.
  - `cases_tested` = holdout-only sample size — the unbiased,
    held-out count actually used to compute hit rate / Brier score.
    This is also what is compared against `policy.min_holdout_cases`.
  - `empirical_hit_rate` = `holdout_hit_rate_pct / 100.0` (the summary
    field is a 0..1 rate; the benchmark row stores a percentage).
  - `dataset_id` / `dataset_version` = the experiment's real
    `benchmark_id` / `benchmark_version`; `benchmark_experiment_id` =
    the experiment's real `experiment_id`. These are the provenance
    fields that make a summary traceable back to the exact run that
    produced it.

Decision logic for VALIDATED vs CONTRADICTED vs UNVALIDATED (once the
sample-size guard has passed):

  - VALIDATED: hit_rate >= policy.min_hit_rate AND
    brier_score <= policy.max_brier_score.
  - CONTRADICTED: hit_rate < 0.75 * policy.min_hit_rate — performing far
    enough below the policy floor to be a clear, unambiguous failure
    rather than a merely inconclusive result.
  - UNVALIDATED: anything in between (metrics below threshold but not
    clearly a contradiction). Conservative by design: this branch
    deliberately never produces VALIDATED.

`policy.max_counterexample_ratio` is deliberately NOT applied here. A
`BenchmarkProfileComparisonRow` carries no per-case counterexample list,
so the only available proxy would be (1 - hit_rate) — but using that
would make `max_counterexample_ratio` (default 0.15) silently override
and dead-code `min_hit_rate` (default 0.60), effectively demanding an
85% hit rate and marking a rule performing well above policy as
CONTRADICTED. Rather than fabricate a counterexample count the benchmark
never measured, this bridge leaves that policy dimension unevaluated;
enforcing it requires per-case outcome data the benchmark layer does not
currently produce.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from apps.api.domain.benchmark_experiment import BenchmarkExperiment
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    RuleLifecycleState,
    RuleValidationSummary,
    ValidationPolicy,
)


# A rule is treated as actively CONTRADICTED (rather than merely
# inconclusive) only when its holdout hit rate falls below this fraction of
# the policy floor. Deliberately conservative: the ambiguous middle band
# resolves to UNVALIDATED, never VALIDATED.
_CONTRADICTION_MARGIN = 0.75


class BenchmarkValidationBridgeError(Exception):
    """Raised when an experiment cannot be mapped to a validation summary."""


def _select_row(experiment: BenchmarkExperiment, profile_id: Optional[str]):
    rows = experiment.report.rows
    if not rows:
        raise BenchmarkValidationBridgeError(
            f"BenchmarkExperiment {experiment.provenance.experiment_id!r} has no comparison rows."
        )
    if profile_id is None:
        if len(rows) != 1:
            raise BenchmarkValidationBridgeError(
                "profile_id must be supplied when the experiment's report contains "
                f"more than one profile row (found {len(rows)})."
            )
        return rows[0]
    for row in rows:
        if row.profile_id == profile_id:
            return row
    raise BenchmarkValidationBridgeError(
        f"profile_id {profile_id!r} not found among experiment rows: "
        f"{[r.profile_id for r in rows]!r}"
    )


def _is_sample_size_sufficient(
    *,
    applicable_cases: int,
    holdout_cases: int,
    policy: ValidationPolicy,
) -> bool:
    if applicable_cases < policy.min_applicable_cases:
        return False
    if policy.require_holdout_split and holdout_cases < policy.min_holdout_cases:
        return False
    return True


@dataclass(frozen=True)
class _Derivation:
    """Internal: everything computed from (experiment, policy) before construction."""
    cases_tested: int
    applicable_cases: int
    supported_outcomes: int
    unsupported_outcomes: int
    hit_rate: float
    brier_score: float
    lifecycle_state: RuleLifecycleState
    evidence_level: EvidenceLevel


def _derive(
    experiment: BenchmarkExperiment,
    policy: ValidationPolicy,
    profile_id: Optional[str],
) -> _Derivation:
    """
    The single source of truth for the metric extraction + deterministic
    decision logic. Both public entry points call this so the decision rule
    is defined in exactly one place.
    """
    row = _select_row(experiment, profile_id)

    applicable_cases = experiment.report.total_benchmark_events
    holdout_cases = row.holdout_sample_size_n
    cases_tested = holdout_cases

    hit_rate = row.holdout_hit_rate_pct / 100.0
    brier_score = row.holdout_brier_score

    sufficient = _is_sample_size_sufficient(
        applicable_cases=applicable_cases,
        holdout_cases=holdout_cases,
        policy=policy,
    )

    supported_outcomes = round(cases_tested * hit_rate)
    unsupported_outcomes = cases_tested - supported_outcomes
    unsupported_ratio = (unsupported_outcomes / cases_tested) if cases_tested > 0 else 1.0

    if not sufficient:
        lifecycle_state = RuleLifecycleState.UNVALIDATED
        evidence_level = EvidenceLevel.INSUFFICIENT_DATA
    else:
        meets_hit_rate = hit_rate >= policy.min_hit_rate
        meets_brier = brier_score <= policy.max_brier_score

        if meets_hit_rate and meets_brier:
            lifecycle_state = RuleLifecycleState.VALIDATED
            if hit_rate >= policy.min_hit_rate + 0.15 and brier_score <= policy.max_brier_score * 0.6:
                evidence_level = EvidenceLevel.HIGH
            else:
                evidence_level = EvidenceLevel.MODERATE
        elif hit_rate < _CONTRADICTION_MARGIN * policy.min_hit_rate:
            # Performing far below the policy floor — a clear, unambiguous
            # failure signal rather than a merely-inconclusive result.
            lifecycle_state = RuleLifecycleState.CONTRADICTED
            evidence_level = EvidenceLevel.CONTRADICTED
        else:
            # Sufficient sample, but metrics fall short without being a
            # clear contradiction — conservative default, never VALIDATED.
            lifecycle_state = RuleLifecycleState.UNVALIDATED
            evidence_level = EvidenceLevel.LOW

    # Structural guarantee (requirement 6): this function must never be able
    # to return PROMOTED or CANONICAL.
    assert lifecycle_state not in (RuleLifecycleState.PROMOTED, RuleLifecycleState.CANONICAL)

    return _Derivation(
        cases_tested=cases_tested,
        applicable_cases=applicable_cases,
        supported_outcomes=supported_outcomes,
        unsupported_outcomes=unsupported_outcomes,
        hit_rate=hit_rate,
        brier_score=brier_score,
        lifecycle_state=lifecycle_state,
        evidence_level=evidence_level,
    )


def _build_summary(
    experiment: BenchmarkExperiment, rule_id: str, policy: ValidationPolicy, d: _Derivation
) -> RuleValidationSummary:
    return RuleValidationSummary(
        rule_id=rule_id,
        policy_id=policy.policy_id,
        cases_tested=d.cases_tested,
        applicable_cases=d.applicable_cases,
        supported_outcomes=d.supported_outcomes,
        unsupported_outcomes=d.unsupported_outcomes,
        indeterminate_cases=0,
        counterexamples=(),
        empirical_hit_rate=d.hit_rate,
        brier_score=d.brier_score,
        dataset_id=experiment.provenance.benchmark_id,
        dataset_version=experiment.provenance.benchmark_version,
        benchmark_experiment_id=experiment.provenance.experiment_id,
        validated_at=datetime.now(timezone.utc),
        validated_by_actor_id="BENCHMARK_VALIDATION_BRIDGE",
    )


def build_validation_summary_from_benchmark(
    experiment: BenchmarkExperiment,
    rule_id: str,
    policy: ValidationPolicy,
    profile_id: Optional[str] = None,
) -> RuleValidationSummary:
    """
    Derive a `RuleValidationSummary` entirely from a real `BenchmarkExperiment`.

    `profile_id` selects which comparison row (predictive profile) within the
    experiment's report corresponds to `rule_id`. It is required whenever the
    experiment compares more than one profile; it is an *identifier*, not a
    metric, so it does not weaken requirement 1 (no fabricated numbers).

    No precision/recall/F1/hit-rate/Brier/sample-size parameter exists on
    this function — every metric is read directly off `experiment`.
    """
    d = _derive(experiment, policy, profile_id)
    return _build_summary(experiment, rule_id, policy, d)


@dataclass(frozen=True)
class BridgeDecision:
    """The full output of the bridge: the summary plus the governance decision."""
    summary: RuleValidationSummary
    lifecycle_state: RuleLifecycleState
    evidence_level: EvidenceLevel


def build_validation_decision_from_benchmark(
    experiment: BenchmarkExperiment,
    rule_id: str,
    policy: ValidationPolicy,
    profile_id: Optional[str] = None,
) -> BridgeDecision:
    """
    Same derivation as `build_validation_summary_from_benchmark`, but also
    returns the governance decision (`RuleLifecycleState`, `EvidenceLevel`)
    that a caller would apply to the rule's `RuleReliabilityRecord`.

    This is the function most callers actually want — the two-part return
    keeps the pure metrics summary (`RuleValidationSummary`, which has no
    lifecycle field) separate from the governed decision
    (`RuleLifecycleState`/`EvidenceLevel`, which belongs to
    `RuleReliabilityRecord`), without inventing fields on either frozen
    dataclass.
    """
    d = _derive(experiment, policy, profile_id)
    summary = _build_summary(experiment, rule_id, policy, d)
    return BridgeDecision(summary=summary, lifecycle_state=d.lifecycle_state, evidence_level=d.evidence_level)


def extract_full_metric_provenance(
    experiment: BenchmarkExperiment,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns the complete metric set from `experiment` (precision, recall,
    F1, MAE, median/p90 offsets, etc.) that `RuleValidationSummary` has no
    dedicated field for. Intended for storage in
    `KnowledgeRuleReliabilityModel.validation_summary_json` (a free-form
    JSON column) alongside the mapped summary fields, so nothing is
    silently dropped between the benchmark and governance systems.
    """
    row = _select_row(experiment, profile_id)
    return {
        "profile_id": row.profile_id,
        "profile_name": row.profile_name,
        "holdout_precision": row.holdout_precision,
        "holdout_recall": row.holdout_recall,
        "holdout_f1_score": row.holdout_f1_score,
        "holdout_hit_rate_pct": row.holdout_hit_rate_pct,
        "holdout_brier_score": row.holdout_brier_score,
        "holdout_mae_peak_days": row.holdout_mae_peak_days,
        "holdout_median_peak_offset_days": row.holdout_median_peak_offset_days,
        "holdout_p90_peak_offset_days": row.holdout_p90_peak_offset_days,
        "calibration_sample_size_n": row.calibration_sample_size_n,
        "holdout_sample_size_n": row.holdout_sample_size_n,
        "calibration_method": row.calibration_method,
        "experiment_id": experiment.provenance.experiment_id,
        "benchmark_id": experiment.provenance.benchmark_id,
        "benchmark_version": experiment.provenance.benchmark_version,
        "content_hash_sha256": experiment.provenance.content_hash_sha256,
        "results_hash": experiment.provenance.results_hash,
    }


def _assert_no_metric_kwargs() -> None:
    """
    Structural self-check (used by tests / requirement 1): neither bridge
    function accepts any precision/recall/F1/hit-rate/Brier/sample-size
    parameter — only (experiment, rule_id, policy, profile_id).
    """
    forbidden = {
        "precision", "recall", "f1", "f1_score", "hit_rate", "brier_score",
        "sample_size", "cases_tested", "applicable_cases", "empirical_hit_rate",
    }
    for fn in (build_validation_summary_from_benchmark, build_validation_decision_from_benchmark):
        params = set(inspect.signature(fn).parameters.keys())
        overlap = params & forbidden
        if overlap:
            raise AssertionError(f"{fn.__name__} unexpectedly accepts metric parameters: {overlap}")


_assert_no_metric_kwargs()
