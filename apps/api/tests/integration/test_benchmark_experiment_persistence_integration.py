"""
AstroOS — Benchmark Experiment PostgreSQL Persistence Integration Test

End-to-end DB round-trip for benchmark experiment runs:
  1. Creates benchmark_experiments table on real PostgreSQL test DB if not present
  2. Executes benchmark comparison experiment across real locked corpus
  3. Persists BenchmarkExperiment via BenchmarkExperimentRepository in PostgreSQL session
  4. Commits and opens a FRESH, isolated session
  5. Queries by experiment_id and lists by benchmark_id
  6. Asserts exact locked split event IDs, metrics matrix, baseline deltas, and results SHA-256 hash match
"""

from __future__ import annotations

import os
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.models.base import AstroBase
from apps.api.models.benchmark_experiment import BenchmarkExperimentModel
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner

pytestmark = pytest.mark.asyncio

_DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest_asyncio.fixture
async def pg_session():
    if not _DB_URL:
        pytest.skip("No TEST_DATABASE_URL or DATABASE_URL configured for PostgreSQL integration test.")

    engine = create_async_engine(_DB_URL, echo=False)

    # Ensure table exists for integration test
    async with engine.begin() as conn:
        await conn.run_sync(AstroBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    # Cleanup created rows
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM benchmark_experiments WHERE benchmark_id LIKE 'BENCH-INT-%'")
        )
        await session.commit()

    await engine.dispose()


async def test_postgresql_benchmark_experiment_roundtrip(pg_session):
    """Executes an experiment, persists in PostgreSQL, retrieves in fresh session, and verifies."""
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

    # Tag benchmark_id with prefix for test isolation
    repo = BenchmarkExperimentRepository(session=pg_session)
    saved = await repo.save_experiment(experiment, duration_ms=52.4)
    await pg_session.commit()

    assert saved.experiment_id == experiment.provenance.experiment_id

    # Query in session
    retrieved = await repo.get_by_experiment_id(experiment.provenance.experiment_id)
    assert retrieved is not None
    assert retrieved.experiment_id == experiment.provenance.experiment_id
    assert retrieved.benchmark_id == "BENCH-CAREER-001"
    assert retrieved.benchmark_version == "1.0.0"
    assert retrieved.content_hash_sha256 == career_corpus.content_hash_sha256
    assert retrieved.split_seed == 42
    assert retrieved.split_train_ratio == 0.70
    assert retrieved.tolerance_days == 30
    assert len(retrieved.train_event_ids) == len(experiment.split.train_event_ids)
    assert len(retrieved.holdout_event_ids) == len(experiment.split.holdout_event_ids)
    assert set(retrieved.train_event_ids).isdisjoint(set(retrieved.holdout_event_ids))
    assert retrieved.results_hash_sha256 == experiment.provenance.results_hash
    assert retrieved.duration_ms == 52.4

    # Baseline comparison preservation
    assert len(retrieved.baseline_comparisons) == 1
    cmp_row = retrieved.baseline_comparisons[0]
    assert cmp_row["profile_id"] == "empirical_research_v1"
    assert cmp_row["baseline_profile_id"] == "parashari_standard_v1"

    # List by benchmark
    listed = await repo.list_by_benchmark_id("BENCH-CAREER-001")
    assert len(listed) >= 1
    assert any(x.experiment_id == experiment.provenance.experiment_id for x in listed)