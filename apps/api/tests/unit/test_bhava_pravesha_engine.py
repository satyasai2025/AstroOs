"""
AstroOS — Unit Tests for 24-Hour Bhava Pravesha Engine
======================================================
Provenance: Kundalee Binary gochar.kkk / Bhaavaanta.VBP (Vinay Jha)
Title: 24-Hour Bhaava Praveshas Of Planets
"""

from datetime import date, datetime, timezone
import re
import pytest

from apps.api.domain.bhava_pravesha import DailyBhavaPraveshaSchedule
from apps.api.services.bhava_pravesha_engine import BhavaPraveshaEngine


@pytest.fixture
def engine():
    return BhavaPraveshaEngine()


def test_bhava_pravesha_engine_24h_schedule(engine):
    """Verify that a 24-hour run produces ingress events across houses for all planets."""
    target_date = date(2026, 9, 4)
    lat = 28.6139
    lon = 77.2090

    schedule = engine.compute_daily_schedule(
        target_date=target_date,
        latitude=lat,
        longitude=lon,
        timezone_offset_hours=5.5,
        timezone_name="IST",
        coarse_step_minutes=15,
        bisection_tolerance_seconds=1.0,
    )

    assert isinstance(schedule, DailyBhavaPraveshaSchedule)
    assert schedule.provenance == "kundalee-binary gochar.kkk (BhaavantKundalis)"
    assert schedule.rule_version == "1.0"
    assert schedule.timezone_name == "IST"
    assert schedule.timezone_offset_hours == 5.5

    # Total events across 9 planets in 24 hours should be substantial (~80 to 110 events)
    assert schedule.total_events_count >= 80
    assert len(schedule.chronological_events) == schedule.total_events_count

    # Check key planets
    for p in ["sun", "moon", "mars", "jupiter", "saturn"]:
        assert p in schedule.events_by_planet
        p_events = schedule.events_by_planet[p]
        assert len(p_events) >= 8  # should enter most houses as Lagna rotates 360 deg


def test_bhava_pravesha_timing_and_chaining_invariant(engine):
    """
    Verify Jha's Siddhantic Invariant:
    'भावप्रवेश कुण्डली का प्रभाव अगली भावप्रवेश कुण्डली तक रहता है।'
    Each event's active_until_utc must seamlessly link to the next event's ingress time.
    """
    target_date = date(2026, 9, 4)
    schedule = engine.compute_daily_schedule(
        target_date=target_date,
        latitude=28.6139,
        longitude=77.2090,
        timezone_offset_hours=5.5,
        coarse_step_minutes=20,
    )

    time_regex = re.compile(r"^\d{2}:\d{2}:\d{2}$")

    for p, p_events in schedule.events_by_planet.items():
        if not p_events:
            continue
        for idx in range(len(p_events) - 1):
            curr_ev = p_events[idx]
            next_ev = p_events[idx + 1]

            # Monotonicity
            assert curr_ev.ingress_datetime_utc < next_ev.ingress_datetime_utc

            # Jha Ingress Invariant chaining
            assert curr_ev.active_until_utc == next_ev.ingress_datetime_utc
            assert curr_ev.duration_minutes > 0.0

            # Valid format HH:MM:SS
            assert time_regex.match(curr_ev.ingress_time_local_str)
            assert 1 <= curr_ev.entered_house <= 12


def test_bhava_pravesha_multi_timezone_support(engine):
    """Verify that custom markets / timezones (e.g. New York Stock Exchange) are supported."""
    target_date = date(2026, 9, 4)
    # New York coordinates and daylight saving offset (-4.0 in September)
    ny_lat = 40.7128
    ny_lon = -74.0060
    ny_tz = -4.0

    schedule_ny = engine.compute_daily_schedule(
        target_date=target_date,
        latitude=ny_lat,
        longitude=ny_lon,
        timezone_offset_hours=ny_tz,
        timezone_name="EDT",
        coarse_step_minutes=30,
    )

    assert schedule_ny.timezone_name == "EDT"
    assert schedule_ny.timezone_offset_hours == -4.0
    assert schedule_ny.total_events_count > 0
    # First chronological event must have valid time string
    first_ev = schedule_ny.chronological_events[0]
    assert len(first_ev.ingress_time_local_str) == 8
