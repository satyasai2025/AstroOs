"""
AstroOS — Unit Test for DashaPeriodResponse Schema Validation
============================================================
Regression test for:
  - start_date / end_date as inexact datetimes (non-zero hour/min/sec)
  - duration_days as fractional float (e.g. 8.700052083333333)
  - Full DashaPeriodResponse and DashaTreeResponse Pydantic serialization
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.schemas.dasha import DashaPeriodResponse, DashaTreeResponse
from apps.api.routers.dasha import _serialise_period


def test_dasha_period_response_datetime_and_float_serialization():
    """Verify DashaPeriodResponse accepts inexact datetimes and fractional duration_days."""
    dt1 = datetime(1973, 1, 14, 15, 30, 24, 262, tzinfo=timezone.utc)
    dt2 = datetime(1973, 1, 23, 8, 18, 28, 500, tzinfo=timezone.utc)
    float_days = 8.700052083333333

    period = DashaPeriodResponse(
        lord="saturn",
        start_date=dt1,
        end_date=dt2,
        duration_days=float_days,
        level=2,
        sub_periods=[],
    )

    assert period.lord == "saturn"
    assert period.start_date == dt1
    assert period.end_date == dt2
    assert period.duration_days == float_days

    # Verify JSON serialization works without error
    json_data = period.model_dump(mode="json")
    assert "1973-01-14T15:30:24" in json_data["start_date"]
    assert json_data["duration_days"] == float_days


def test_dasha_tree_response_datetime_serialization():
    """Verify DashaTreeResponse accepts birth_date as datetime and nested periods."""
    dt1 = datetime(1973, 1, 14, 15, 30, 24, tzinfo=timezone.utc)
    dt2 = datetime(1989, 1, 14, 15, 30, 24, tzinfo=timezone.utc)

    sub = DashaPeriodResponse(
        lord="saturn",
        start_date=dt1,
        end_date=dt2,
        duration_days=5844.0,
        level=1,
        sub_periods=[],
    )

    tree = DashaTreeResponse(
        system="vimshottari",
        birth_date=dt1,
        trigger_planet="saturn",
        trigger_nakshatra="Pushya",
        trigger_nakshatra_number=8,
        mahadashas=[sub],
        max_depth=2,
        total_cycle_years=120.0,
    )

    json_data = tree.model_dump(mode="json")
    assert json_data["system"] == "vimshottari"
    assert len(json_data["mahadashas"]) == 1