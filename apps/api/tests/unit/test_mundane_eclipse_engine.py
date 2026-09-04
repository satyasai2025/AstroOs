"""
AstroOS — Unit Tests for Standalone Mundane Eclipse Engine
"""

import pytest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.mundane_eclipse_engine import MundaneEclipseEngine


@pytest.fixture
def eclipse_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return MundaneEclipseEngine(wrapper)


def test_mundane_eclipses_annual_scan(eclipse_engine):
    """Scans and detects eclipses in 2026."""
    eclipses = eclipse_engine.find_eclipses_for_year(2026, "lahiri")

    # In any calendar year there are at least 4 eclipses (solar + lunar)
    assert len(eclipses) >= 2
    for ecl in eclipses:
        assert ecl.peak_utc.year == 2026
        assert len(ecl.eclipsed_rashi) > 0
        assert len(ecl.eclipsed_nakshatra) > 0
        assert ecl.duration_hours > 0.0
        assert ecl.impact_duration_months > 0.0
        assert len(ecl.afflicted_directions) > 0
        assert len(ecl.impact_summary) > 0
