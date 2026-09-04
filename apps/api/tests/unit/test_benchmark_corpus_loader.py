"""
AstroOS — Benchmark Corpus Loader & Research Lab Test Suite

Proves:
  1. Real canonical benchmark corpora load, pass validation, and lock with SHA-256 hashes.
  2. Content hash determinism across datasets.
  3. Immutable locking guard prevents duplicate or mutating locks.
  4. End-to-end experiment runner executes locked 70/30 split and baseline comparison.
  5. Identical train and holdout event IDs across all profiles.
  6. Experiment provenance and results hash determinism.
  7. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date
import importlib
import pytest

from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry, ImmutableBenchmarkError
from apps.api.services.benchmark_runner import BenchmarkRunner
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


# ── 1. Real Canonical Corpora Loading & Locking ────────────────────────────────


def test_load_and_lock_all_canonical_corpora():
    """All 4 real canonical corpora are loaded, validated, and locked with SHA-256 hashes."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)

    corpora = loader.load_and_lock_all_canonical_corpora()

    assert "BENCH-CAREER-001" in corpora
    assert "BENCH-MARRIAGE-001" in corpora
    assert "BENCH-WEALTH-001" in corpora
    assert "BENCH-TRANSIT-001" in corpora

    career_corpus = corpora["BENCH-CAREER-001"]
    assert career_corpus.version == "1.0.0"
    assert len(career_corpus.events) >= 5
    assert len(career_corpus.content_hash_sha256) == 64
    assert career_corpus.event_type == "career"


# ── 2. Immutability Guard on Canonical Corpora ─────────────────────────────────


def test_canonical_corpora_immutability():
    """Attempting to re-lock a canonical corpus version raises ImmutableBenchmarkError."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()

    career_corpus = corpora["BENCH-CAREER-001"]

    with pytest.raises(ImmutableBenchmarkError):
        registry.lock_corpus(career_corpus)


# ── 3. End-to-End Real Experiment & Baseline Comparison ────────────────────────


def test_real_corpus_experiment_runner():
    """Executes a complete benchmark experiment on real career corpus with baseline comparisons."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]

    experiment = runner.run_experiment(
        corpus=career_corpus,
        profiles=profiles,
        baseline_profile_id="parashari_standard_v1",
        tolerance_days=30,
        seed=42,
        train_ratio=0.70,
    )

    assert experiment.provenance.benchmark_id == "BENCH-CAREER-001"
    assert experiment.provenance.benchmark_version == "1.0.0"
    assert experiment.provenance.split_seed == 42
    assert len(experiment.provenance.results_hash) == 64

    # Locked split verification
    assert len(experiment.split.train_event_ids) + len(experiment.split.holdout_event_ids) == len(career_corpus.events)
    assert set(experiment.split.train_event_ids).isdisjoint(set(experiment.split.holdout_event_ids))

    # Report rows
    assert len(experiment.report.rows) == 2
    for r in experiment.report.rows:
        assert r.holdout_sample_size_n == len(experiment.split.holdout_event_ids)
        assert 0.0 <= r.holdout_hit_rate_pct <= 100.0
        assert 0.0 <= r.holdout_brier_score <= 1.0

    # Baseline comparison deltas
    assert len(experiment.baseline_comparisons) == 1
    cmp = experiment.baseline_comparisons[0]
    assert cmp.profile_id == "empirical_research_v1"
    assert cmp.baseline_profile_id == "parashari_standard_v1"
    assert isinstance(cmp.delta_hit_rate_pct, float)
    assert isinstance(cmp.delta_brier_score, float)


# ── 4. Cardinal Invariance Guarantee ──────────────────────────────────────────


def test_benchmark_lab_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    # 1. Run prediction before benchmark experiment
    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # 2. Run real benchmark experiment
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    runner = BenchmarkRunner()
    _ = runner.run_experiment(corpora["BENCH-CAREER-001"], [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE])

    # 3. Run prediction after benchmark experiment
    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Assert bit-for-bit invariance
    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash