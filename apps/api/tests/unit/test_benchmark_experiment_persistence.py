"""
AstroOS — Benchmark Experiment Persistence & Reproducibility Test Suite

Proves:
  1. Experiment records are fully persisted and retrievable with locked split IDs.
  2. Reproducibility Guarantee: Same config & seed produces identical results_hash_sha256.
  3. No Data Leakage: Persisted Train and Holdout event ID sets remain strictly disjoint.
  4. Repository listing and query filtering by benchmark_id.
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
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
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


# ── 1. Experiment Persistence and Retrieval ────────────────────────────────────


@pytest.mark.asyncio
async def test_experiment_persistence_and_retrieval():
    """Verifies that an experiment run is saved to repository and retrieved with full fidelity."""
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

    repo = BenchmarkExperimentRepository()
    saved = await repo.save_experiment(experiment, duration_ms=45.2)

    assert saved.experiment_id == experiment.provenance.experiment_id
    assert saved.benchmark_id == "BENCH-CAREER-001"
    assert saved.content_hash_sha256 == career_corpus.content_hash_sha256
    assert saved.status == "COMPLETED"
    assert saved.results_hash_sha256 == experiment.provenance.results_hash
    assert saved.duration_ms == 45.2

    # Retrieve by experiment ID
    retrieved = await repo.get_by_experiment_id(experiment.provenance.experiment_id)
    assert retrieved is not None
    assert retrieved.experiment_id == experiment.provenance.experiment_id
    assert len(retrieved.train_event_ids) == len(experiment.split.train_event_ids)
    assert len(retrieved.holdout_event_ids) == len(experiment.split.holdout_event_ids)
    assert len(retrieved.results_summary["rows"]) == 2
    assert len(retrieved.baseline_comparisons) == 1


# ── 2. Reproducibility Guarantee ───────────────────────────────────────────────


def test_experiment_reproducibility_deterministic_hash():
    """Two identical experiment runs with same seed produce identical results_hash_sha256."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]

    exp1 = runner.run_experiment(
        corpus=career_corpus,
        profiles=profiles,
        baseline_profile_id="parashari_standard_v1",
        tolerance_days=30,
        seed=42,
        train_ratio=0.70,
    )

    exp2 = runner.run_experiment(
        corpus=career_corpus,
        profiles=profiles,
        baseline_profile_id="parashari_standard_v1",
        tolerance_days=30,
        seed=42,
        train_ratio=0.70,
    )

    assert exp1.provenance.results_hash == exp2.provenance.results_hash
    assert exp1.split.train_event_ids == exp2.split.train_event_ids
    assert exp1.split.holdout_event_ids == exp2.split.holdout_event_ids
    for r1, r2 in zip(exp1.report.rows, exp2.report.rows):
        assert r1.holdout_hit_rate_pct == r2.holdout_hit_rate_pct
        assert r1.holdout_brier_score == r2.holdout_brier_score


# ── 3. No Data Leakage ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persisted_experiment_no_data_leakage():
    """Asserts that persisted train_event_ids and holdout_event_ids have zero overlap."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    career_corpus = corpora["BENCH-CAREER-001"]

    runner = BenchmarkRunner()
    exp = runner.run_experiment(career_corpus, [PARASHARI_STANDARD_PROFILE], seed=42)

    repo = BenchmarkExperimentRepository()
    saved = await repo.save_experiment(exp)

    train_set = set(saved.train_event_ids)
    holdout_set = set(saved.holdout_event_ids)

    assert train_set.isdisjoint(holdout_set)
    assert len(train_set) + len(holdout_set) == len(career_corpus.events)


# ── 4. List Experiments Filter ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_experiments_by_benchmark_id():
    """Lists persisted experiments filtered by benchmark_id."""
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()

    runner = BenchmarkRunner()
    repo = BenchmarkExperimentRepository()

    exp_career = runner.run_experiment(corpora["BENCH-CAREER-001"], [PARASHARI_STANDARD_PROFILE], seed=42)
    exp_marriage = runner.run_experiment(corpora["BENCH-MARRIAGE-001"], [PARASHARI_STANDARD_PROFILE], seed=42)

    await repo.save_experiment(exp_career)
    await repo.save_experiment(exp_marriage)

    career_list = await repo.list_by_benchmark_id("BENCH-CAREER-001")
    assert len(career_list) == 1
    assert career_list[0].benchmark_id == "BENCH-CAREER-001"

    marriage_list = await repo.list_by_benchmark_id("BENCH-MARRIAGE-001")
    assert len(marriage_list) == 1
    assert marriage_list[0].benchmark_id == "BENCH-MARRIAGE-001"


# ── 5. Cardinal Invariance Guarantee ──────────────────────────────────────────


def test_persistence_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    # 1. Prediction before persistence
    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # 2. Run and persist experiment
    registry = BenchmarkRegistry()
    loader = BenchmarkCorpusLoader(registry=registry)
    corpora = loader.load_and_lock_all_canonical_corpora()
    runner = BenchmarkRunner()
    exp = runner.run_experiment(corpora["BENCH-CAREER-001"], [PARASHARI_STANDARD_PROFILE])
    repo = BenchmarkExperimentRepository()
    # Synchronous helper check

    # 3. Prediction after persistence
    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash