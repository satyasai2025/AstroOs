"""
AstroOS — Benchmark Corpus Loader Service

Automatically scans, audits, content-hashes, and registers canonical benchmark
corpora from apps/api/data/benchmarks/*.json into BenchmarkRegistry at startup.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from apps.api.domain.benchmark_dataset import (
    BenchmarkDefinition,
    LockedBenchmarkCorpus,
)
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.dataset_validator import DatasetValidator


_FILE_TO_BENCHMARK_ID = {
    "career_promotions_bench_v1.json": "BENCH-CAREER-001",
    "marriage_timing_bench_v1.json": "BENCH-MARRIAGE-001",
    "wealth_dhana_bench_v1.json": "BENCH-WEALTH-001",
    "transit_saturn_bench_v1.json": "BENCH-TRANSIT-001",
}


class BenchmarkCorpusLoader:
    """Loads and locks standardized benchmark datasets from filesystem data files."""

    def __init__(
        self,
        registry: Optional[BenchmarkRegistry] = None,
        validator: Optional[DatasetValidator] = None,
        data_dir: Optional[Path] = None,
    ) -> None:
        self._registry = registry or BenchmarkRegistry()
        self._validator = validator or DatasetValidator()
        self._data_dir = data_dir or (Path(__file__).parent.parent / "data" / "benchmarks")

    def load_and_lock_all_canonical_corpora(self) -> dict[str, LockedBenchmarkCorpus]:
        """
        Scans data directory, audits raw event records, generates SHA-256 checksums,
        and registers immutable LockedBenchmarkCorpus instances.
        """
        loaded: dict[str, LockedBenchmarkCorpus] = {}

        if not self._data_dir.exists():
            return loaded

        for json_file in self._data_dir.glob("*.json"):
            filename = json_file.name
            bench_id = _FILE_TO_BENCHMARK_ID.get(filename)
            if not bench_id:
                continue

            definition = self._registry.get_definition(bench_id)
            if not definition:
                continue

            try:
                with open(json_file, "r", encoding="utf-8-sig") as f:
                    raw_events = json.load(f)

                validation_result = self._validator.validate_and_audit(
                    raw_records=raw_events,
                    inclusion_criteria=definition.inclusion_criteria,
                )

                if len(validation_result.accepted_events) == 0:
                    continue

                corpus = LockedBenchmarkCorpus(
                    benchmark_id=bench_id,
                    version="1.0.0",
                    content_hash_sha256=validation_result.content_hash_sha256,
                    event_type=definition.event_type,
                    events=validation_result.accepted_events,
                    definition=definition,
                )

                # Lock in registry if not already locked
                existing = self._registry.get_locked_corpus(bench_id, "1.0.0")
                if existing is None:
                    self._registry.lock_corpus(corpus)
                loaded[bench_id] = corpus

            except Exception as e:
                print(f"[WARN] Failed to load canonical benchmark {filename}: {e}")

        return loaded