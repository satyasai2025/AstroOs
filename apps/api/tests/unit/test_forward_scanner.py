"""Smoke tests for ForwardScanner orchestrator (Phase 1)."""
import os
import sys
from datetime import date, datetime, timezone

import pytest

# Add repo root to path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from apps.api.services.forward_scanner import (  # noqa: E402
    ForwardCandidate,
    ForwardScanResult,
    ForwardScanner,
    quick_scan,
)


def test_module_imports():
    assert ForwardCandidate is not None
    assert ForwardScanResult is not None
    assert ForwardScanner is not None
    assert callable(quick_scan)


def test_empty_result_well_formed():
    scanner = ForwardScanner()
    result = ForwardScanResult(
        chart_id="test_chart",
        target_start=date(2024, 1, 1),
        target_end=date(2024, 12, 31),
        event_types_evaluated=("marriage",),
        candidates=(),
        total_slices_evaluated=0,
        deterministic_signature=ForwardScanner._deterministic_signature(()),
        uncertainty_disclosure="test",
    )
    assert result.candidates == ()
    assert result.deterministic_signature == ""
    assert result.uncertainty_disclosure == "test"
    assert result.scan_version == "forward_v1"


def test_deterministic_signature_independent_of_input_order():
    c1 = ForwardCandidate(
        event_type="marriage",
        signature_id="sig_low",
        timing_window_start=date(2024, 1, 1),
        timing_window_end=date(2024, 3, 1),
        peak_score=50,
        confidence=0.55,
        promise_status="strong",
        primary_drivers=("d1",),
        supporting_factors=(),
        opposing_factors=(),
        classical_source="BPHS Ch.19",
        evidence_fact_keys=("k1",),
        uncertainty_disclosure="x",
    )
    c2 = ForwardCandidate(
        event_type="marriage",
        signature_id="sig_high",
        timing_window_start=date(2024, 6, 1),
        timing_window_end=date(2024, 9, 1),
        peak_score=80,
        confidence=0.83,
        promise_status="very_strong",
        primary_drivers=("d2",),
        supporting_factors=(),
        opposing_factors=(),
        classical_source="BPHS Ch.19",
        evidence_fact_keys=("k2", "k3"),
        uncertainty_disclosure="x",
    )
    sig_a = ForwardScanner._deterministic_signature((c1, c2))
    sig_b = ForwardScanner._deterministic_signature((c2, c1))
    assert sig_a == sig_b


def test_forward_candidate_is_frozen():
    c = ForwardCandidate(
        event_type="marriage",
        signature_id="s",
        timing_window_start=date(2024, 1, 1),
        timing_window_end=date(2024, 2, 1),
        peak_score=50,
        confidence=0.5,
        promise_status="ok",
        primary_drivers=(),
        supporting_factors=(),
        opposing_factors=(),
        classical_source="BPHS",
        evidence_fact_keys=(),
        uncertainty_disclosure="d",
    )
    with pytest.raises(Exception):
        c.confidence = 0.9  # type: ignore[misc]
