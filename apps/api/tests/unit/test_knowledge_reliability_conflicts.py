"""
Unit tests for Preserving Conflicting Evidence without Majority Voting.
"""

import pytest

from apps.api.domain.knowledge_reliability import (
    ConflictPreservationStatus,
    TechniqueFramework,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine


def test_conflict_preservation_retains_opposing_claims():
    """
    Ensures contradictory doctrinal claims are stored and retained without averaging or majority voting.
    """
    engine = KnowledgeReliabilityEngine()

    conflict = engine.register_conflict(
        conflict_id="CONF-ASPECT-STRENGTH-001",
        topic="Rashi Drishti vs Graha Drishti Aspect Strength in Narayana Dasha Timing",
        technique_framework=TechniqueFramework.JAIMINI,
        supporting_sources=[
            "Jaimini Upadesha Sutras Ch 1.2 (Sanjay Rath commentary)",
            "Jaimini Sutramritam (Iranganti Rangacharya)",
        ],
        contradicting_sources=[
            "BPHS Ch 9 (Santhanam Ed.)",
            "Phaladeepika Ch 15 (Gopesh Kumar Ojha)",
        ],
        empirical_findings=[
            "Benchmark EXP-BENCH-JAIMINI-001 showed 68% accuracy when Rashi Drishti is weighted primarily.",
            "Benchmark EXP-BENCH-PARASHARI-002 showed Graha Drishti dominant in vimshottari context.",
        ],
        status=ConflictPreservationStatus.ACTIVE_DISPUTE,
        notes="Preserve both positions separately. Future prediction engine must evaluate them according to active technique profile.",
    )

    retrieved = engine.get_conflict("CONF-ASPECT-STRENGTH-001")
    assert retrieved is not None
    assert len(retrieved.supporting_sources) == 2
    assert len(retrieved.contradicting_sources) == 2
    assert len(retrieved.empirical_findings) == 2
    assert retrieved.status == ConflictPreservationStatus.ACTIVE_DISPUTE
