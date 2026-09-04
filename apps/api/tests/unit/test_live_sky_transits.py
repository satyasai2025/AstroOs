from datetime import datetime, timezone
import pytest
from apps.api.services.live_sky_transit_engine import LiveSkyTransitEngine, LiveSkyTransitReport


def test_live_sky_transits_calculation():
    dt = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)
    natal_planets = {
        "Sun": 150.0,
        "Jupiter": 45.0,
    }

    report = LiveSkyTransitEngine.compute_current_sky(
        target_datetime=dt,
        natal_positions=natal_planets,
    )

    assert isinstance(report, LiveSkyTransitReport)
    assert len(report.planets) == 9
    planet_names = [p.name for p in report.planets]
    assert "Sun" in planet_names
    assert "Jupiter" in planet_names
    assert "Saturn" in planet_names
    assert "Rahu" in planet_names
    assert "Ketu" in planet_names

    # Check nakshatra and pada
    for p in report.planets:
        assert len(p.nakshatra) > 0
        assert 1 <= p.pada <= 4
        assert 0 <= p.degree_in_rashi < 30.0
