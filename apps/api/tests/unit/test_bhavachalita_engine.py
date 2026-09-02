"""
Unit tests for Vishamabhava Bhaavachalita Engine.
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.bhavachalita_engine import VishamabhavaEngine


def test_bhavachalita_basic_structure():
    engine = VishamabhavaEngine()
    # Raj DOB: 30 June 1971, 04:57:40 AM IST -> 29 June 1971 23:27:40 UTC
    dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    chart = engine.compute_bhavachalita(
        birth_datetime=dt,
        latitude=22.30,
        longitude=73.18,
    )

    assert len(chart.houses) == 12
    assert chart.lagna_madhya > 0
    assert chart.madhya_lagna > 0

    # House 1 should be Taurus (Vrishabha)
    h1 = chart.houses[0]
    assert h1.house_number == 1
    assert h1.primary_rashi.lower() == "taurus"
    assert h1.primary_lord == "Venus"

    # Total span of all 12 houses should be ~360 degrees
    total_spans = sum(h.total_span_deg for h in chart.houses)
    assert abs(total_spans - 360.0) < 0.1

    # Check planet placements
    assert "Mars" in chart.planet_bhava_placements
    assert "Saturn" in chart.planet_bhava_placements
