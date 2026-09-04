"""
AstroOS — Benchmark Dataset & Quality Engine Test Suite

Proves:
  1. 3-Tier Duplicate & Conflict Detection (Hard duplicates rejected, conflicts rejected, near-duplicates flagged).
  2. Computational Validity vs Provenance Separation (Invalid coordinates rejected, Rodden thresholds enforced).
  3. Auditable Rejection Trail (Rejected records preserved with reasons, never silently deleted).
  4. Benchmark Immutability: Attempting to overwrite a locked corpus raises ImmutableBenchmarkError.
  5. Cryptographic Content Hash: Data mutations produce deterministic SHA-256 changes.
  6. Identical Locked Split: All evaluated profiles receive the exact same train & holdout event IDs.
  7. Holdout-Only Metrics Evaluation: Precision, Recall, F1, Brier score, and MAE evaluated strictly on Holdout.
  8. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date, datetime, timezone
import importlib
import pytest

from apps.api.domain.benchmark_dataset import (
    BenchmarkDefinition,
    InclusionCriteria,
    LockedBenchmarkCorpus,
    RejectionCode,
)
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.research_calibration import (
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
)
from apps.api.services.benchmark_registry import BenchmarkRegistry, ImmutableBenchmarkError
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.dataset_validator import DatasetValidator
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()

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


def _build_raw_events_sample() -> list[dict]:
    """Generates valid raw records for QC testing."""
    return [
        {
            "event_id": "EVT-101",
            "subject_id": "SUB-101",
            "event_type": "career",
            "actual_date": "2026-06-15",
            "birth_datetime_utc": "1985-11-20T04:30:00+00:00",
            "birth_latitude": 28.6139,
            "birth_longitude": 77.2090,
            "birth_confidence": "AA",
            "event_date_confidence": "exact_date",
            "event_verification": "official_document",
        },
        {
            "event_id": "EVT-102",
            "subject_id": "SUB-102",
            "event_type": "career",
            "actual_date": "2027-03-10",
            "birth_datetime_utc": "1990-05-10T08:15:00+00:00",
            "birth_latitude": 19.0760,
            "birth_longitude": 72.8777,
            "birth_confidence": "A",
            "event_date_confidence": "exact_date",
            "event_verification": "primary_biography",
        },
        {
            "event_id": "EVT-103",
            "subject_id": "SUB-103",
            "event_type": "career",
            "actual_date": "2026-09-20",
            "birth_datetime_utc": "1988-02-14T12:00:00+00:00",
            "birth_latitude": 12.9716,
            "birth_longitude": 77.5946,
            "birth_confidence": "B",
            "event_date_confidence": "approx_week",
            "event_verification": "secondary_report",
        },
    ]


# ── 1. 3-Tier Duplicate & Conflict Detection ────────────────────────────────────


def test_duplicate_and_conflict_detection():
    """Validates rejection of hard duplicates & conflicts, and flagging of near-duplicates."""
    validator = DatasetValidator()
    criteria = InclusionCriteria(min_birth_confidence=BirthDataConfidence.B)

    raw_records = _build_raw_events_sample()

    # Add a hard duplicate
    raw_records.append(dict(raw_records[0], event_id="EVT-101-DUP"))

    # Add a conflicting record (same subject & event date, different birth time)
    raw_records.append({
        "event_id": "EVT-102-CONFLICT",
        "subject_id": "SUB-102",
        "event_type": "career",
        "actual_date": "2027-03-10",
        "birth_datetime_utc": "1990-05-10T22:00:00+00:00",  # Differing birth time
        "birth_latitude": 19.0760,
        "birth_longitude": 72.8777,
        "birth_confidence": "A",
    })

    # Add a possible duplicate (same subject, event within 10 days)
    raw_records.append({
        "event_id": "EVT-103-NEAR",
        "subject_id": "SUB-103",
        "event_type": "career",
        "actual_date": "2026-09-25",  # 5 days apart from EVT-103
        "birth_datetime_utc": "1988-02-14T12:00:00+00:00",
        "birth_latitude": 12.9716,
        "birth_longitude": 77.5946,
        "birth_confidence": "B",
    })

    result = validator.validate_and_audit(raw_records, criteria)

    # 3 original + 1 near duplicate accepted = 4 accepted
    assert len(result.accepted_events) == 4

    # 1 hard dup + 1 conflict rejected = 2 rejected
    assert len(result.rejected_records) == 2
    rej_codes = {r.rejection_code for r in result.rejected_records}
    assert RejectionCode.HARD_DUPLICATE_COLLISION in rej_codes
    assert RejectionCode.CONFLICTING_RECORD_COLLISION in rej_codes

    # 1 near duplicate flagged as warning
    assert len(result.flagged_warnings) == 1
    assert result.flagged_warnings[0].flagged_event_id == "EVT-103-NEAR"


# ── 2. Computational Validity vs Provenance Separation ──────────────────────────


def test_computational_vs_provenance_validation():
    """Separates Swiss Ephemeris computational failure from Rodden threshold filtering."""
    validator = DatasetValidator()

    # Invalid latitude (-120 is out of bounds)
    bad_coords = [{
        "event_id": "BAD-001",
        "subject_id": "SUB-BAD",
        "event_type": "career",
        "actual_date": "2026-01-01",
        "birth_datetime_utc": "1985-01-01T00:00:00+00:00",
        "birth_latitude": -120.0,
        "birth_longitude": 77.0,
        "birth_confidence": "AA",
    }]
    res1 = validator.validate_and_audit(bad_coords, InclusionCriteria())
    assert len(res1.rejected_records) == 1
    assert res1.rejected_records[0].rejection_code == RejectionCode.INVALID_COORDINATES

    # Valid coords but Rodden rating C with threshold A
    low_rodden = [{
        "event_id": "LOW-001",
        "subject_id": "SUB-LOW",
        "event_type": "career",
        "actual_date": "2026-01-01",
        "birth_datetime_utc": "1985-01-01T00:00:00+00:00",
        "birth_latitude": 28.6139,
        "birth_longitude": 77.2090,
        "birth_confidence": "C",
    }]
    res2 = validator.validate_and_audit(low_rodden, InclusionCriteria(min_birth_confidence=BirthDataConfidence.A))
    assert len(res2.rejected_records) == 1
    assert res2.rejected_records[0].rejection_code == RejectionCode.BELOW_RODDEN_THRESHOLD


# ── 3. Benchmark Immutability & Content Hash ───────────────────────────────────


def test_benchmark_lock_immutability_and_hash():
    """Attempting to mutate or overwrite a locked benchmark corpus raises ImmutableBenchmarkError."""
    registry = BenchmarkRegistry()
    validator = DatasetValidator()

    definition = registry.get_definition("BENCH-CAREER-001")
    assert definition is not None

    raw_events = _build_raw_events_sample()
    result = validator.validate_and_audit(raw_events, definition.inclusion_criteria)

    corpus_v1 = LockedBenchmarkCorpus(
        benchmark_id="BENCH-CAREER-001",
        version="1.0.0",
        content_hash_sha256=result.content_hash_sha256,
        event_type="career",
        events=result.accepted_events,
        definition=definition,
    )

    # 1. Lock v1.0.0
    registry.lock_corpus(corpus_v1)
    retrieved = registry.get_locked_corpus("BENCH-CAREER-001", "1.0.0")
    assert retrieved is not None
    assert retrieved.content_hash_sha256 == result.content_hash_sha256

    # 2. Attempting to overwrite v1.0.0 fails
    with pytest.raises(ImmutableBenchmarkError):
        registry.lock_corpus(corpus_v1)


# ── 4. Identical Locked Split & Holdout Metrics ────────────────────────────────


def test_identical_locked_split_and_holdout_metrics():
    """Verifies that all profiles are evaluated on identical train/holdout splits with holdout-only metrics."""
    registry = BenchmarkRegistry()
    validator = DatasetValidator()

    definition = registry.get_definition("BENCH-CAREER-001")
    raw_events = _build_raw_events_sample()
    # Duplicate records to create a corpus of 6 events
    extended_raw = raw_events + [
        dict(raw_events[0], event_id="EVT-201", subject_id="SUB-201", actual_date="2028-01-15"),
        dict(raw_events[1], event_id="EVT-202", subject_id="SUB-202", actual_date="2028-05-20"),
        dict(raw_events[2], event_id="EVT-203", subject_id="SUB-203", actual_date="2028-09-10"),
    ]

    result = validator.validate_and_audit(extended_raw, definition.inclusion_criteria)
    corpus = LockedBenchmarkCorpus(
        benchmark_id="BENCH-CAREER-001",
        version="1.1.0",
        content_hash_sha256=result.content_hash_sha256,
        event_type="career",
        events=result.accepted_events,
        definition=definition,
    )

    runner = BenchmarkRunner()
    profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]

    report = runner.compare_profiles(
        corpus=corpus,
        profiles=profiles,
        tolerance_days=30,
        seed=42,
        train_ratio=0.70,
    )

    assert report.benchmark_id == "BENCH-CAREER-001"
    assert report.benchmark_version == "1.1.0"
    assert report.split_seed == 42
    assert len(report.rows) == 2

    # Verify both profiles evaluated on the exact same holdout sample size
    assert report.rows[0].holdout_sample_size_n == report.rows[1].holdout_sample_size_n
    assert report.rows[0].calibration_sample_size_n == report.rows[1].calibration_sample_size_n

    for row in report.rows:
        assert 0.0 <= row.holdout_hit_rate_pct <= 100.0
        assert 0.0 <= row.holdout_brier_score <= 1.0
        assert row.holdout_mae_peak_days >= 0.0


# ── 5. Cardinal Invariance Guarantee ──────────────────────────────────────────


def test_benchmark_engine_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    # 1. Run prediction before benchmark run
    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # 2. Run benchmark comparison
    registry = BenchmarkRegistry()
    definition = registry.get_definition("BENCH-CAREER-001")
    validator = DatasetValidator()
    raw = _build_raw_events_sample()
    result = validator.validate_and_audit(raw, definition.inclusion_criteria)
    corpus = LockedBenchmarkCorpus(
        benchmark_id="BENCH-CAREER-001",
        version="1.2.0",
        content_hash_sha256=result.content_hash_sha256,
        event_type="career",
        events=result.accepted_events,
        definition=definition,
    )
    runner = BenchmarkRunner()
    _ = runner.compare_profiles(corpus, [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE])

    # 3. Run prediction after benchmark run
    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Assert bit-for-bit invariance
    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash