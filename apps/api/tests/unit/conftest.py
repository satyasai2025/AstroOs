"""
Unit-test-only synthetic fixtures for Module 14 (Event Engine).
minimal_chart / natal_snapshot live in tests/conftest.py (shared with
tests/integration); this file adds fixtures only tests/unit needs.
"""

from __future__ import annotations

import uuid
from datetime import date

import os
import sys

import pytest

from apps.api.tests.conftest import require_test_db  # noqa: F401

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.events import EventRecord


def make_period(lord: str, start: date, end: date, level: int, sub=()) -> DashaPeriod:
    return DashaPeriod(
        lord=lord,
        start_date=start,
        end_date=end,
        duration_days=(end - start).days,
        level=level,
        sub_periods=sub,
    )


@pytest.fixture
def simple_dasha_tree() -> DashaTree:
    """
    A tiny, hand-built two-level Vimshottari-shaped tree: two Mahadashas
    back to back, the first with two Antardashas.
    """
    antardashas = (
        make_period("ketu", date(2000, 1, 1), date(2003, 1, 1), level=2),
        make_period("venus", date(2003, 1, 1), date(2010, 1, 1), level=2),
    )
    mahadashas = (
        make_period("jupiter", date(2000, 1, 1), date(2010, 1, 1), level=1, sub=antardashas),
        make_period("saturn", date(2010, 1, 1), date(2029, 1, 1), level=1),
    )
    return DashaTree(
        system="vimshottari",
        birth_date=date(2000, 1, 1),
        trigger_planet="jupiter",
        trigger_nakshatra="punarvasu",
        trigger_nakshatra_number=7,
        mahadashas=mahadashas,
        max_depth=2,
        total_cycle_years=120,
    )


@pytest.fixture
def event_record(natal_snapshot) -> EventRecord:
    return EventRecord(
        id=uuid.uuid4(),
        chart_id=natal_snapshot.chart_id,
        event_date=date(2005, 6, 15),
        title="Marriage",
        category="marriage",
        is_verified=True,
    )
