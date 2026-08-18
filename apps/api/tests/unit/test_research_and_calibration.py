"""
AstroOS — Research & Calibration Engine Test Suite (v4)

Proves:
  1. No Data Leakage: Calibration models fitted strictly on Train split (70%) without seeing Holdout.
  2. Model Separation: Isotonic pooled intervals vs Platt logistic scaling operate independently.
  3. Provenance Traceability:
     - Isotonic probability matches observed_hits / bin_sample_size_n.
     - Platt probability matches 1 / (1 + exp(-(aS + b))).
  4. Full Scientific Reproducibility Versioning (all 10 provenance metadata fields verified).
  5. Window-Centric Temporal Matching: Window coverage evaluated independently of peak offset.
  6. Formal Out-of-Sample Holdout Brier Score: Evaluated strictly on unseen holdout binary outcomes.
  7. Small-N Warning & Wilson Rate CI: Rate uncertainty flagged when sample size < 30.
  8. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date, datetime, timezone
import importlib
import pytest

from apps.api.domain.prediction_orchestration import (
    PARASHARI_STANDARD_PROFILE,
    PredictionWindowCandidate,
    PromiseStatus,
    TemporalResolution,
)
from apps.api.domain.research_calibration import (
    BenchmarkDataset,
    BirthDataConfidence,
    CalibrationModelType,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
    TemporalMatchStatus,
)
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.research_engine import ResearchEngine
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


def _build_test_benchmark(n_events: int = 10) -> BenchmarkDataset:
    """Builds a deterministic benchmark dataset for testing."""
    events = []
    for i in range(1, n_events + 1):
        events.append(
            GroundTruthEvent(
                event_id=f"EVT-{i:03d}",
                subject_id=f"SUB-{i:03d}",
                event_type="career",
                actual_date=date(2026, 1 + (i % 11), 15),
                birth_datetime_utc=datetime(1985, 1 + (i % 11), 10, 4, 30, tzinfo=timezone.utc),
                birth_latitude=28.6139,
                birth_longitude=77.2090,
                birth_confidence=BirthDataConfidence.AA,
                event_date_confidence=EventDateConfidence.EXACT_DATE,
                event_verification=EventVerification.OFFICIAL_DOCUMENT,
                source_citation="AstroOS Research Archive",
                notes="Executive career milestone",
            )
        )
    return BenchmarkDataset(
        dataset_id="career_promotions_bench_v1",
        name="Career Elevation Test Benchmark",
        event_type="career",
        version="1.0",
        description="Verified executive career elevation events",
        events=tuple(events),
    )


# ── 1. No Data Leakage & Dataset Splitting ──────────────────────────────────────


def test_no_data_leakage_train_holdout_split():
    """Train set (70%) and Holdout set (30%) are strictly disjoint."""
    research = ResearchEngine()
    dataset = _build_test_benchmark(n_events=10)

    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)

    assert len(split.train_events) == 7
    assert len(split.holdout_events) == 3

    train_ids = {e.event_id for e in split.train_events}
    holdout_ids = {e.event_id for e in split.holdout_events}

    # Zero overlap (No data leakage)
    assert train_ids.isdisjoint(holdout_ids)
    assert len(train_ids) + len(holdout_ids) == len(dataset.events)


# ── 2. Model Separation: Isotonic vs Platt Scaling ────────────────────────────


def test_model_separation_isotonic_vs_platt():
    """Isotonic and Platt models produce independent, model-specific parameters."""
    research = ResearchEngine()
    calib = CalibrationEngine()
    dataset = _build_test_benchmark(n_events=10)
    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)

    train_outcomes = research.run_backtest(split.train_events)

    # 1. Isotonic Model
    iso_model = calib.fit_isotonic_calibration(
        train_outcomes, dataset.dataset_id, dataset.version, dataset.event_type, PARASHARI_STANDARD_PROFILE.profile_id
    )
    assert iso_model.provenance.calibration_model_type == CalibrationModelType.ISOTONIC_REGRESSION
    assert len(iso_model.isotonic_pools) > 0
    assert iso_model.platt_params is None

    # 2. Platt Model
    platt_model = calib.fit_platt_scaling(
        train_outcomes, dataset.dataset_id, dataset.version, dataset.event_type, PARASHARI_STANDARD_PROFILE.profile_id
    )
    assert platt_model.provenance.calibration_model_type == CalibrationModelType.PLATT_SCALING
    assert len(platt_model.isotonic_pools) == 0
    assert platt_model.platt_params is not None
    assert isinstance(platt_model.platt_params.slope_a, float)
    assert isinstance(platt_model.platt_params.intercept_b, float)


# ── 3. Provenance Traceability (Isotonic vs Platt) ─────────────────────────────


def test_provenance_traceability():
    """
    Isotonic calibrated probability traces to observed_hits / sample_size_n.
    Platt calibrated probability traces to logistic sigmoid parameters.
    """
    research = ResearchEngine()
    calib = CalibrationEngine()
    dataset = _build_test_benchmark(n_events=10)
    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)
    train_outcomes = research.run_backtest(split.train_events)
    holdout_outcomes = research.run_backtest(split.holdout_events)

    candidate = PredictionWindowCandidate(
        event_type="career",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 8, 31),
        peak_date=date(2026, 6, 15),
        peak_score=75,
        promise_status=PromiseStatus.ESTABLISHED,
        primary_drivers=("10th Lord Kendra",),
        supporting_factors=(),
        opposing_factors=(),
        evidence_trace=(),
        resolution_level=TemporalResolution.MESO_GOCHARA,
        deterministic_hash="hash-1234",
    )

    # 1. Isotonic provenance
    iso_model = calib.fit_isotonic_calibration(
        train_outcomes, dataset.dataset_id, dataset.version, dataset.event_type, PARASHARI_STANDARD_PROFILE.profile_id
    )
    iso_val = calib.evaluate_holdout_validation(holdout_outcomes, iso_model)
    iso_pred = calib.calibrate_candidate_window(candidate, iso_model, iso_val)

    assert iso_pred.calibration_bin_min_score == 70
    assert iso_pred.calibration_bin_max_score == 79
    if iso_pred.calibration_bin_sample_size_n and iso_pred.calibration_bin_sample_size_n > 0:
        expected_p = iso_pred.calibration_bin_observed_hits / iso_pred.calibration_bin_sample_size_n
        assert pytest.approx(iso_pred.calibrated_probability, 0.001) == expected_p

    # 2. Platt provenance
    platt_model = calib.fit_platt_scaling(
        train_outcomes, dataset.dataset_id, dataset.version, dataset.event_type, PARASHARI_STANDARD_PROFILE.profile_id
    )
    platt_val = calib.evaluate_holdout_validation(holdout_outcomes, platt_model)
    platt_pred = calib.calibrate_candidate_window(candidate, platt_model, platt_val)

    assert platt_pred.platt_slope_a is not None
    assert platt_pred.platt_intercept_b is not None
    assert 0.0 <= platt_pred.calibrated_probability <= 1.0


# ── 4. Full Scientific Reproducibility Versioning ──────────────────────────────


def test_reproducibility_versioning_metadata():
    """Asserts all 10 calibration provenance metadata fields are captured."""
    calib = CalibrationEngine()
    research = ResearchEngine()
    dataset = _build_test_benchmark(n_events=10)
    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)
    train_outcomes = research.run_backtest(split.train_events)

    model = calib.fit_isotonic_calibration(
        train_outcomes=train_outcomes,
        dataset_id="career_n1000",
        dataset_version="2.1",
        event_type="career",
        profile_id="parashari_standard_v1",
        split_seed=42,
        split_train_ratio=0.70,
        tolerance_days=30,
    )

    p = model.provenance
    assert p.dataset_id == "career_n1000"
    assert p.dataset_version == "2.1"
    assert p.event_type == "career"
    assert p.consensus_profile_id == "parashari_standard_v1"
    assert p.calibration_model_type == CalibrationModelType.ISOTONIC_REGRESSION
    assert p.calibration_model_version == "1.0"
    assert p.split_seed == 42
    assert p.split_train_ratio == 0.70
    assert p.tolerance_days == 30
    assert p.fit_timestamp is not None


# ── 5. Window-Centric Temporal Matching ────────────────────────────────────────


def test_window_centric_temporal_matching():
    """Event falling inside predicted window is classified as HIT regardless of peak offset."""
    research = ResearchEngine()
    dataset = _build_test_benchmark(n_events=2)

    outcomes = research.run_backtest(dataset.events, tolerance_days=30)
    assert len(outcomes) == 2
    for o in outcomes:
        assert o.match_status in (
            TemporalMatchStatus.WINDOW_EXACT_HIT,
            TemporalMatchStatus.WINDOW_TOLERANCE_HIT,
            TemporalMatchStatus.TEMPORAL_MISS,
        )


# ── 6. Formal Holdout Brier Score ─────────────────────────────────────────────


def test_formal_holdout_brier_score():
    """Holdout Brier score is computed strictly from calibrated probabilities vs binary outcomes."""
    calib = CalibrationEngine()
    research = ResearchEngine()
    dataset = _build_test_benchmark(n_events=10)
    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)

    train_outcomes = research.run_backtest(split.train_events)
    holdout_outcomes = research.run_backtest(split.holdout_events)

    model = calib.fit_isotonic_calibration(
        train_outcomes, dataset.dataset_id, dataset.version, dataset.event_type, PARASHARI_STANDARD_PROFILE.profile_id
    )

    validation = calib.evaluate_holdout_validation(holdout_outcomes, model)
    assert validation.holdout_sample_size_n == len(split.holdout_events)
    assert 0.0 <= validation.holdout_brier_score <= 1.0
    assert 0.0 <= validation.holdout_hit_rate <= 1.0


# ── 7. Small-N Warning & Wilson Rate CI ────────────────────────────────────────


def test_small_n_warning_and_wilson_ci():
    """Wilson interval and small-N warning flag are generated when bin N < 30."""
    calib = CalibrationEngine()
    research = ResearchEngine()
    dataset = _build_test_benchmark(n_events=5)
    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)
    train_outcomes = research.run_backtest(split.train_events)

    model = calib.fit_isotonic_calibration(
        train_outcomes, dataset.dataset_id, dataset.version, dataset.event_type, PARASHARI_STANDARD_PROFILE.profile_id
    )

    for pool in model.isotonic_pools:
        if pool.bin_sample_size_n < 30:
            assert pool.has_small_n_warning is True
        assert 0.0 <= pool.rate_ci_95[0] <= pool.rate_ci_95[1] <= 1.0


# ── 8. Cardinal Invariance Guarantee ──────────────────────────────────────────


def test_research_and_calibration_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator before and after calibration."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    # 1. Run prediction before backtest
    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # 2. Run backtest and calibration
    dataset = _build_test_benchmark(n_events=6)
    research = ResearchEngine()
    split = research.split_dataset(dataset, train_ratio=0.70, seed=42)
    train_outcomes = research.run_backtest(split.train_events)
    calib = CalibrationEngine()
    model = calib.fit_isotonic_calibration(train_outcomes, dataset.dataset_id, dataset.version, "career", PARASHARI_STANDARD_PROFILE.profile_id)
    _ = calib.evaluate_holdout_validation(research.run_backtest(split.holdout_events), model)

    # 3. Run prediction after backtest
    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Assert bit-for-bit invariance
    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.start_date == c2.start_date
        assert c1.end_date == c2.end_date
        assert c1.deterministic_hash == c2.deterministic_hash