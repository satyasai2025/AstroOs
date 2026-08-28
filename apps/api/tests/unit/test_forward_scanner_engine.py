"""
Unit tests for PhalitaForwardScanner (Phase 6 Prospective Event Scanning).
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.phalita_core.forward_scanner_engine import (
    PhalitaForwardScanner,
    ProspectivePredictionWindow,
)


def test_prospective_scanner_execution():
    """Verify prospective scanning on sample chart without errors or NaNs."""
    scanner = PhalitaForwardScanner()

    # Sample birth details: 1990-01-01 12:00:00 UTC at New Delhi
    birth_dt = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    lat, lon = 28.6139, 77.2090

    windows = scanner.scan_prospective_windows(
        birth_dt=birth_dt,
        latitude=lat,
        longitude=lon,
        scan_start_date=date(2026, 1, 1),
        scan_horizon_years=3,
        domain="career",
        min_probability_threshold=0.0,
    )

    assert isinstance(windows, list)
    assert len(windows) > 0

    first_w = windows[0]
    assert isinstance(first_w, ProspectivePredictionWindow)
    assert first_w.domain == "career"
    assert first_w.window_start <= first_w.window_end
    assert 0.0 <= first_w.calibrated_probability <= 1.0
    assert first_w.active_mahadasha != ""
    assert first_w.active_antardasha != ""
    assert "structural_d1" in first_w.router_attention
