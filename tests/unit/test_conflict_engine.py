"""
AstroOS — Conflict Engine Unit Tests (Phase D, Module 19 Extension)

`KnowledgeEngine.load_conflicts` / `load_conflict` read doctrinal
conflict YAMLs from knowledge/conflicts/. These tests verify the YAML
catalogue loads, parses into KnowledgeConflict domain objects, and
returns sensible results for present/missing IDs. No mock — exercises
the real YAML files committed to the repo.
"""

from __future__ import annotations

import pytest

from apps.api.domain.conflict import (
    ConflictEvidence,
    ConflictPosition,
    ConflictResolution,
    KnowledgeConflict,
)
from apps.api.services.knowledge_engine import KnowledgeEngine


@pytest.fixture
def engine() -> KnowledgeEngine:
    # The two conflict loaders never touch the repo, so no mock needed.
    return KnowledgeEngine(repo=None)


class TestLoadConflicts:
    def test_loads_all_conflicts(self, engine):
        conflicts = engine.load_conflicts()
        # catalogue index declares 7 conflicts.
        assert len(conflicts) >= 7
        assert all(isinstance(c, KnowledgeConflict) for c in conflicts)

    def test_conflict_ids_unique(self, engine):
        conflicts = engine.load_conflicts()
        ids = [c.id for c in conflicts]
        assert len(set(ids)) == len(ids)

    def test_conflict_has_positions_evidence_resolution(self, engine):
        conflicts = engine.load_conflicts()
        # conflict.001 is known to carry all three sections.
        first = next(c for c in conflicts if c.id == "conflict.001")
        assert first.name
        assert len(first.positions) == 3
        assert all(isinstance(p, ConflictPosition) for p in first.positions)
        assert isinstance(first.evidence, ConflictEvidence)
        assert isinstance(first.resolution, ConflictResolution)
        # Parashari whole-sign position should have adherents + arguments.
        parashari = first.positions[0]
        assert parashari.tradition == "Parashari"
        assert len(parashari.arguments) > 0
        assert len(parashari.adherents) > 0

    def test_resolution_status_populated(self, engine):
        conflicts = engine.load_conflicts()
        statuses = {c.resolution.status for c in conflicts}
        # Catalogue tracks resolved / partially-resolved / unresolved.
        assert statuses <= {"resolved", "partially-resolved", "unresolved"}
        assert "partially-resolved" in statuses


class TestLoadSingleConflict:
    def test_load_single_known_conflict(self, engine):
        conflict = engine.load_conflict("conflict.001")
        assert conflict is not None
        assert isinstance(conflict, KnowledgeConflict)
        assert conflict.id == "conflict.001"
        assert conflict.domain == "bhava"

    def test_load_single_unknown_returns_none(self, engine):
        assert engine.load_conflict("does.not.exist") is None
