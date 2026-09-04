"""
AstroOS — Unit Tests for Benchmark Loader & Data Governance
"""

import pytest
from pathlib import Path
from benchmark.loader import load_benchmark, domain_report


def test_benchmark_loader_integrity():
    """Verify that benchmark dataset loads with strict governance rules."""
    train_set, test_set = load_benchmark(data_dir="data/benchmark", holdout_frac=0.20, seed=42)

    # 1. Check native counts (80% train, 20% test of 125 natives)
    assert len(train_set) == 100
    assert len(test_set) == 25

    # 2. Check no native leakage between train and test
    train_cids = {c["chart"]["case_id"] for c in train_set}
    test_cids = {c["chart"]["case_id"] for c in test_set}
    assert train_cids.isdisjoint(test_cids), "Data leakage! Natives present in both train and test sets"

    # 3. Check that every native has >= 1 verified event
    for c in train_set + test_set:
        assert len(c["events"]) >= 1
        for ev in c["events"]:
            assert ev["verified"] is True
            assert ev["precision"] in ("day", "month", "year")
            assert ev["source"] != ""

    # 4. Check domain gate: death domain has n >= 30 in train set
    death_events_train = sum(1 for c in train_set for ev in c["events"] if ev["event_type"] == "death")
    assert death_events_train >= 30, f"Expected n >= 30 death events in train set, got {death_events_train}"
