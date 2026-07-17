"""Tests for Deduplicator."""

import pytest
from apps.api.services.dataset_import.deduplicator import Deduplicator


class TestDeduplicator:
    def test_no_duplicates(self):
        dedup = Deduplicator(["name"])
        records = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        unique, report = dedup.deduplicate(records)
        assert len(unique) == 3
        assert report.duplicates_removed == 0

    def test_exact_duplicates(self):
        dedup = Deduplicator(["name"])
        records = [{"name": "A"}, {"name": "A"}, {"name": "B"}]
        unique, report = dedup.deduplicate(records)
        assert len(unique) == 2
        assert report.duplicates_removed == 1

    def test_multi_field_key(self):
        dedup = Deduplicator(["name", "age"])
        records = [
            {"name": "A", "age": 30},
            {"name": "A", "age": 30},
            {"name": "A", "age": 25},
        ]
        unique, report = dedup.deduplicate(records)
        assert len(unique) == 2
        assert report.duplicates_removed == 1

    def test_case_insensitive(self):
        dedup = Deduplicator(["name"])
        records = [{"name": "John"}, {"name": "john"}, {"name": "JOHN"}]
        unique, report = dedup.deduplicate(records)
        assert len(unique) == 1
        assert report.duplicates_removed == 2

    def test_empty_input(self):
        dedup = Deduplicator(["name"])
        unique, report = dedup.deduplicate([])
        assert len(unique) == 0
        assert report.total_records == 0

    def test_duplicate_pct(self):
        dedup = Deduplicator(["name"])
        records = [{"name": "A"}, {"name": "A"}, {"name": "A"}]
        _, report = dedup.deduplicate(records)
        assert report.duplicate_pct == pytest.approx(66.67, abs=0.1)
