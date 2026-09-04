"""
AstroOS — Birth-chart report dasha integrity.

Guards a real defect found in the Foundation report: the builder used to derive
the Vimshottari tree inline, and its first (partial) mahadasha used a fraction
formula that let the antardashas run far past the mahadasha's own end. For an
8 Aug 1912 chart the Mars mahadasha ended in 1919 while its antardashas ran to
2027 — 72 overflowing sub-periods across the nine mahadashas.

The fix was not to patch the formula but to stop recomputing dasha in the
report layer at all, per the report tier spec:

    "Report builders must NOT recalculate: ... Dasha ...
     They only assemble already-validated canonical outputs."

These tests assert both the invariant and the sourcing.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.config import get_settings
from apps.api.services.birth_chart_report_builder import BirthChartReportBuilder
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

# The chart that exposed the bug (Prof. B. V. Raman: 8 Aug 1912, Bangalore).
BORN = datetime(1912, 8, 8, 14, 8, tzinfo=timezone.utc)
LAT, LON = 12.59, 77.35


def _parse(d: str) -> datetime:
    return datetime.strptime(d, "%d %b %Y")


@pytest.fixture(scope="module")
def report() -> dict:
    settings = get_settings()
    wrapper = EphemerisWrapper(
        ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri", node_type="mean"
    )
    chart = HoroscopeEngine(wrapper).generate_d1(
        birth_datetime_utc=BORN, latitude=LAT, longitude=LON,
        ayanamsa="lahiri", house_system="W", node_type="mean",
    )
    return BirthChartReportBuilder(wrapper).build_report_data(
        chart=chart, subject_name="Test", gender="Male",
        birth_datetime_utc=BORN, latitude=LAT, longitude=LON,
    )


def test_antardashas_never_outlast_their_mahadasha(report):
    """The core invariant the old inline maths broke 72 times over."""
    overflowing = [
        (md["mahadasha"], ad["lord"], ad["end"], md["end"])
        for md in report["dasha_timeline"]
        for ad in md["antardashas"]
        if _parse(ad["end"]) > _parse(md["end"])
    ]
    assert not overflowing, (
        f"{len(overflowing)} antardasha(s) end after their mahadasha: "
        f"{overflowing[:3]}"
    )


def test_antardashas_tile_their_mahadasha_without_gaps(report):
    """First AD starts with the MD, last AD ends with it, no gaps between."""
    for md in report["dasha_timeline"]:
        ads = md["antardashas"]
        assert ads, f"{md['mahadasha']} mahadasha has no antardashas"
        assert ads[0]["start"] == md["start"]
        assert ads[-1]["end"] == md["end"]
        for prev, nxt in zip(ads, ads[1:]):
            assert prev["end"] == nxt["start"], (
                f"gap between {prev['lord']} and {nxt['lord']} "
                f"in {md['mahadasha']} mahadasha"
            )


def test_each_mahadasha_has_nine_antardashas(report):
    for md in report["dasha_timeline"]:
        assert len(md["antardashas"]) == 9, (
            f"{md['mahadasha']} has {len(md['antardashas'])} antardashas, expected 9"
        )


def test_mahadashas_run_in_unbroken_sequence(report):
    timeline = report["dasha_timeline"]
    assert len(timeline) == 9
    for prev, nxt in zip(timeline, timeline[1:]):
        assert prev["end"] == nxt["start"], (
            f"gap between {prev['mahadasha']} and {nxt['mahadasha']} mahadasha"
        )


def test_active_mahadasha_actually_contains_today(report):
    """
    The old code picked the active period positionally (`i == 1`), so the
    "current" mahadasha was whatever sat second in the list. It must be the
    one today's date falls inside.
    """
    today = datetime.now(timezone.utc).replace(tzinfo=None)
    match = [
        md for md in report["dasha_timeline"]
        if _parse(md["start"]) <= today <= _parse(md["end"])
    ]
    if not match:
        pytest.skip("chart's dasha cycle does not cover today")
    assert report["active_md_lord"] == match[0]["mahadasha"]


def test_builder_delegates_dasha_to_the_canonical_engine():
    """Sourcing check — the builder must hold a DashaEngine, not its own maths."""
    from apps.api.services.dasha_engine import DashaEngine

    settings = get_settings()
    wrapper = EphemerisWrapper(
        ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri", node_type="mean"
    )
    builder = BirthChartReportBuilder(wrapper)
    assert isinstance(getattr(builder, "_dasha_engine", None), DashaEngine)
