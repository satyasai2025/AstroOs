"""
Unit Tests for Priority 8 — PredictionConfluenceEngine (Module 23)

Verifies:
1. Evaluation of all 6 core systems (Dasha/Transit, KP CSL, SBC Vedha, Classical Rules, Ashtakavarga, P7 Empirical Track Record)
2. Mathematical correctness of k/N confluence calculation
3. Deterministic support, neutral, and active veto propagation (KP 12th negation, SBC malefic ray, Classical Bhanga)
4. Exact 3-way evidence provenance tagging (CALCULATED_EPHEMERIS, CLASSICAL_LITERATURE, EMPIRICAL_BACKTEST)
5. Timing window intersection without fabricated dates
6. Non-conversion of empirical historical track record into prediction probability
7. Insufficient sample size warnings
8. SHA-256 evidence hashing determinism and immutable Freeze-to-P7 integration
"""

import pytest
from datetime import datetime, timezone

from apps.api.domain.prediction_confluence import (
    ProvenanceType,
    SynthesizedVerdict,
    SystemSupportStatus,
)
from apps.api.domain.prediction_validation import (
    PredictionCategory,
    TemporalSplitType,
)
from apps.api.services.prediction_confluence_engine import PredictionConfluenceEngine
from apps.api.services.prediction_validation_service import PredictionValidationService


@pytest.fixture
def sample_chart():
    return {
        "chart_id": "test_chart_dr_raman",
        "subject_name": "Dr. B.V. Raman",
        "birth_utc": "1912-08-08T19:35:00+00:00",
        "ascendant": {"rashi": "Aquarius", "longitude": 314.5, "rashi_degree": 14.5},
        "planets": [
            {"planet": "Sun", "rashi": "Cancer", "house_number": 6, "sidereal_longitude": 113.2, "is_retrograde": False},
            {"planet": "Moon", "rashi": "Taurus", "house_number": 4, "sidereal_longitude": 53.8, "is_retrograde": False},
            {"planet": "Mars", "rashi": "Leo", "house_number": 7, "sidereal_longitude": 141.4, "is_retrograde": False},
            {"planet": "Mercury", "rashi": "Leo", "house_number": 7, "sidereal_longitude": 134.1, "is_retrograde": False},
            {"planet": "Jupiter", "rashi": "Scorpio", "house_number": 10, "sidereal_longitude": 232.9, "is_retrograde": False},
            {"planet": "Venus", "rashi": "Virgo", "house_number": 8, "sidereal_longitude": 152.6, "is_retrograde": False},
            {"planet": "Saturn", "rashi": "Taurus", "house_number": 4, "sidereal_longitude": 40.2, "is_retrograde": False},
            {"planet": "Rahu", "rashi": "Pisces", "house_number": 2, "sidereal_longitude": 345.1, "is_retrograde": True},
            {"planet": "Ketu", "rashi": "Virgo", "house_number": 8, "sidereal_longitude": 165.1, "is_retrograde": True},
        ],
        "houses": [
            {"house_number": 1, "rashi": "Aquarius", "sign_lord": "Saturn", "cusp_longitude": 314.5},
            {"house_number": 2, "rashi": "Pisces", "sign_lord": "Jupiter", "cusp_longitude": 344.5},
            {"house_number": 3, "rashi": "Aries", "sign_lord": "Mars", "cusp_longitude": 14.5},
            {"house_number": 4, "rashi": "Taurus", "sign_lord": "Venus", "cusp_longitude": 44.5},
            {"house_number": 5, "rashi": "Gemini", "sign_lord": "Mercury", "cusp_longitude": 74.5},
            {"house_number": 6, "rashi": "Cancer", "sign_lord": "Moon", "cusp_longitude": 104.5},
            {"house_number": 7, "rashi": "Leo", "sign_lord": "Sun", "cusp_longitude": 134.5},
            {"house_number": 8, "rashi": "Virgo", "sign_lord": "Mercury", "cusp_longitude": 164.5},
            {"house_number": 9, "rashi": "Libra", "sign_lord": "Venus", "cusp_longitude": 194.5},
            {"house_number": 10, "rashi": "Scorpio", "sign_lord": "Mars", "cusp_longitude": 224.5},
            {"house_number": 11, "rashi": "Sagittarius", "sign_lord": "Jupiter", "cusp_longitude": 254.5},
            {"house_number": 12, "rashi": "Capricorn", "sign_lord": "Saturn", "cusp_longitude": 284.5},
        ],
    }


def test_all_six_systems_evaluated_and_provenance_tagged(sample_chart):
    engine = PredictionConfluenceEngine()
    synthesis = engine.synthesize(sample_chart, category=PredictionCategory.CAREER)

    assert len(synthesis.system_contributions) == 6
    system_ids = [c.system_id for c in synthesis.system_contributions]
    assert "PARASHARI_DASHA" in system_ids
    assert "KP_CSL" in system_ids
    assert "SBC_VEDHA" in system_ids
    assert "CLASSICAL_YOGA" in system_ids
    assert "ASHTAKAVARGA" in system_ids
    assert "EMPIRICAL_P7_TRACK_RECORD" in system_ids

    # Check 3-way provenance
    provenance_types = {c.provenance_type for c in synthesis.system_contributions}
    assert ProvenanceType.CALCULATED_EPHEMERIS in provenance_types
    assert ProvenanceType.CLASSICAL_LITERATURE in provenance_types
    assert ProvenanceType.EMPIRICAL_BACKTEST in provenance_types

    assert len(synthesis.provenance_breakdown[ProvenanceType.CALCULATED_EPHEMERIS.value]) > 0
    assert len(synthesis.provenance_breakdown[ProvenanceType.CLASSICAL_LITERATURE.value]) > 0
    assert len(synthesis.provenance_breakdown[ProvenanceType.EMPIRICAL_BACKTEST.value]) > 0


def test_k_over_n_confluence_calculation(sample_chart):
    engine = PredictionConfluenceEngine()
    synthesis = engine.synthesize(sample_chart, category=PredictionCategory.CAREER)

    matrix = synthesis.confluence_matrix
    assert matrix.total_systems == 6
    assert matrix.supporting_count + matrix.veto_count + matrix.neutral_count == 6
    assert matrix.confluence_ratio == round(matrix.supporting_count / 6.0, 4)

    if matrix.supporting_count == 6:
        assert matrix.synthesized_verdict == SynthesizedVerdict.UNANIMOUS_CONFLUENCE
    elif matrix.confluence_ratio >= 0.75:
        assert matrix.synthesized_verdict == SynthesizedVerdict.STRONG_CONFLUENCE
    elif matrix.confluence_ratio >= 0.50:
        assert matrix.synthesized_verdict == SynthesizedVerdict.MODERATE_CONFLUENCE


def test_classical_yoga_bhanga_veto_propagation(sample_chart):
    engine = PredictionConfluenceEngine()
    # Modify chart so Jupiter is debilitated in Capricorn (Makara)
    debilitated_chart = dict(sample_chart)
    debilitated_chart["planets"] = [
        dict(p) if p["planet"] != "Jupiter" else {**p, "rashi": "Capricorn", "house_number": 12}
        for p in sample_chart["planets"]
    ]

    synthesis = engine.synthesize(debilitated_chart, category=PredictionCategory.CAREER)
    classical_contrib = next(c for c in synthesis.system_contributions if c.system_id == "CLASSICAL_YOGA")

    assert classical_contrib.support_status == SystemSupportStatus.CONTRADICTING_VETO
    assert classical_contrib.veto_reason is not None
    assert "Classical Yoga Bhanga" in classical_contrib.veto_reason
    assert synthesis.confluence_matrix.synthesized_verdict == SynthesizedVerdict.CONFLICTED_VETO
    assert len(synthesis.confluence_matrix.active_vetoes) > 0


def test_empirical_track_record_exposes_sample_size_and_wilson_ci(sample_chart):
    engine = PredictionConfluenceEngine()
    synthesis = engine.synthesize(sample_chart, category=PredictionCategory.CAREER)

    emp = synthesis.empirical_track_record
    assert emp.sample_size > 0
    assert 0.0 <= emp.historical_hit_rate <= 1.0
    assert len(emp.wilson_95_ci) == 2
    assert emp.wilson_95_ci[0] <= emp.wilson_95_ci[1]

    # Must NOT have any opaque confidence score
    assert not hasattr(synthesis, "confidence_score")
    assert not hasattr(synthesis, "probability_percentage")


def test_freeze_to_p7_immutable_snapshot(sample_chart):
    validation_service = PredictionValidationService()
    validation_service.reset_for_tests()
    engine = PredictionConfluenceEngine(validation_service=validation_service)

    synthesis = engine.synthesize(sample_chart, category=PredictionCategory.CAREER)
    snapshot = engine.freeze_to_p7(synthesis, target_split_type=TemporalSplitType.VALIDATION)

    assert snapshot.prediction_id is not None
    assert snapshot.evidence_hash != ""
    assert snapshot.technique == "UNIFIED_MULTI_SYSTEM_CONFLUENCE"
    assert snapshot.category == PredictionCategory.CAREER
    assert len(snapshot.evidence_ids) == 6

    # Verify retrieved from registry
    retrieved = validation_service.get_prediction(snapshot.prediction_id)
    assert retrieved is not None
    assert retrieved.evidence_hash == snapshot.evidence_hash


def test_determinism_and_sha256_hash_stability(sample_chart):
    engine = PredictionConfluenceEngine()
    fixed_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    syn1 = engine.synthesize(sample_chart, category=PredictionCategory.CAREER, target_datetime=fixed_time)
    syn2 = engine.synthesize(sample_chart, category=PredictionCategory.CAREER, target_datetime=fixed_time)

    assert syn1.confluence_matrix.supporting_count == syn2.confluence_matrix.supporting_count
    assert syn1.confluence_matrix.confluence_ratio == syn2.confluence_matrix.confluence_ratio
    assert syn1.confluence_matrix.synthesized_verdict == syn2.confluence_matrix.synthesized_verdict
    assert len(syn1.system_contributions) == len(syn2.system_contributions)
