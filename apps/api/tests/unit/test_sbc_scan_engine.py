"""
AstroOS — SBC Scan Engine Unit Tests (validation only; the real-ephemeris
scan itself is exercised manually, not in unit tests, same convention
as other ephemeris-backed services in this suite).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.sbc_scan_engine import SBCScanEngine


def test_rejects_step_days_below_1():
    engine = SBCScanEngine(report_service=None)  # not called before validation
    with pytest.raises(ValueError):
        engine.scan(
            "ashwini",
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 10, tzinfo=timezone.utc),
            step_days=0,
        )


def test_rejects_end_before_start():
    engine = SBCScanEngine(report_service=None)
    with pytest.raises(ValueError):
        engine.scan(
            "ashwini",
            datetime(2026, 1, 10, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
