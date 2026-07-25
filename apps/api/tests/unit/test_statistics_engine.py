"""
AstroOS — StatisticsEngine Unit Tests (Module 18, Phase 1)

Tests use synthetic AstrologicalSnapshot objects. No real engines, no DB.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from apps.api.domain.ashtakavarga import SarvashtakavargaResult
from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.research import AstrologicalSnapshot
from apps.api.domain.statistics import Distribution, NumericSummary
from apps.api.domain.verification import (
    Alignment,
    VerificationFindings,
    VerificationPair,
    VerificationStrength,
)
from apps.api.domain.yoga import YogaResult
from apps.api.services.statistics_engine import StatisticsEngine


def _make_planet(planet: str, house: int, rashi: str = "aries") -> SiderealPosition:
    return SiderealPosition(
        planet=planet, sidereal_longitude=float(house * 30), rashi=rashi,
        rashi_degree=10.0, house_number=house, nakshatra="pushya", pada=2,
        is_retrograde=False, is_combust=False, combustion_orb=None,
        dignity=DignityType.FRIENDLY,
    )


def _make_chart(planets: list[SiderealPosition]) -> D1Chart:
    return D1Chart(
        ephemeris=None, ascendant=None, houses=[], planets=planets,
        aspects=[], planet_strengths=[], panchanga=None,
        ayanamsa_system="lahiri", house_system="W",
    )


def _make_yoga(yoga_id: str, is_present: bool = True) -> YogaResult:
    return YogaResult(
        yoga_id=yoga_id, name=yoga_id, category="Test",
        source_text="", rule_version="1.0", is_present=is_present,
        strength="full" if is_present else None,
    )


def _make_snapshot(
    planets: list[SiderealPosition] | None = None,
    yogas: list[YogaResult] | None = None,
    verification: VerificationFindings | None = None,
) -> AstrologicalSnapshot:
    planets = planets or [_make_planet("sun", 1), _make_planet("moon", 2)]
    return AstrologicalSnapshot(
        id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
        label="test", captured_at=None,
        chart_ref=_make_chart(planets),
        yogas=tuple(yogas) if yogas else None,
        verification_ref=verification,
    )


class TestPlanetHouseDistribution:
    def test_single_planet(self):
        snap = _make_snapshot(planets=[_make_planet("jupiter", 5)])
        dist = StatisticsEngine.compute_planet_house_distribution((snap,), "jupiter")
        assert dist.total == 1
        assert dist.counts[4] == 1  # house 5 is index 4

    def test_multiple_snapshots_same_planet(self):
        s1 = _make_snapshot(planets=[_make_planet("jupiter", 5)])
        s2 = _make_snapshot(planets=[_make_planet("jupiter", 9)])
        dist = StatisticsEngine.compute_planet_house_distribution((s1, s2), "jupiter")
        assert dist.total == 2
        assert dist.counts[4] == 1  # house 5
        assert dist.counts[8] == 1  # house 9

    def test_empty_snapshots(self):
        dist = StatisticsEngine.compute_planet_house_distribution((), "jupiter")
        assert dist.total == 0
        assert all(c == 0 for c in dist.counts)

    def test_planet_not_found(self):
        snap = _make_snapshot(planets=[_make_planet("sun", 1)])
        dist = StatisticsEngine.compute_planet_house_distribution((snap,), "jupiter")
        assert dist.total == 0

    def test_12_bins(self):
        snap = _make_snapshot(planets=[_make_planet("jupiter", 1)])
        dist = StatisticsEngine.compute_planet_house_distribution((snap,), "jupiter")
        assert len(dist.bins) == 12
        assert dist.bins == tuple(str(i) for i in range(1, 13))


class TestPlanetRashiDistribution:
    def test_single_planet(self):
        snap = _make_snapshot(planets=[_make_planet("venus", 3, rashi="taurus")])
        dist = StatisticsEngine.compute_planet_rashi_distribution((snap,), "venus")
        assert dist.total == 1
        taurus_idx = 1  # aries=0, taurus=1
        assert dist.counts[taurus_idx] == 1

    def test_12_rashi_bins(self):
        snap = _make_snapshot()
        dist = StatisticsEngine.compute_planet_rashi_distribution((snap,), "sun")
        assert len(dist.bins) == 12


class TestYogaDistribution:
    def test_counts_present_yogas(self):
        snap = _make_snapshot(yogas=[
            _make_yoga("BPHS-PM-001", is_present=True),
            _make_yoga("BPHS-PM-002", is_present=False),
        ])
        dist = StatisticsEngine.compute_yoga_distribution((snap,))
        assert dist.counts[0] == 1  # BPHS-PM-001 present once

    def test_empty_snapshots(self):
        dist = StatisticsEngine.compute_yoga_distribution(())
        assert dist.total == 0


class TestVerificationStrengthDistribution:
    def test_counts_strengths(self):
        pair_high = VerificationPair(
            rule_id="R1", rule_name="R1", rule_category="g",
            rule_matched=True, event_id=uuid.uuid4(), event_date=date(2000, 1, 1),
            event_title="E", event_description=None, event_category="c",
            event_is_verified=True, derived_facts={}, inferred_domains=("c",),
            alignment=Alignment.CONFIRMED, strength=VerificationStrength.HIGH,
            explanation="",
        )
        pair_medium = VerificationPair(
            rule_id="R2", rule_name="R2", rule_category="g",
            rule_matched=True, event_id=uuid.uuid4(), event_date=date(2000, 1, 1),
            event_title="E", event_description=None, event_category="c",
            event_is_verified=False, derived_facts={}, inferred_domains=("c",),
            alignment=Alignment.CONFIRMED, strength=VerificationStrength.MEDIUM,
            explanation="",
        )
        findings = VerificationFindings(
            chart_id=uuid.uuid4(), period_covered=(date(2000,1,1), date(2000,1,1)),
            total_events=2, total_rules_evaluated=2, total_pairs=2,
            rule_summaries=(), verification_pairs=(pair_high, pair_medium),
        )
        snap = _make_snapshot(verification=findings)
        dist = StatisticsEngine.compute_verification_strength_distribution((snap,))
        assert dist.counts[0] == 1  # high count
        assert dist.counts[1] == 1  # medium count
        assert dist.total == 2

    def test_no_verification_data(self):
        snap = _make_snapshot()
        dist = StatisticsEngine.compute_verification_strength_distribution((snap,))
        assert dist.total == 0


class TestNumericSummary:
    def test_computes_mean_and_median(self):
        s1 = _make_snapshot(planets=[_make_planet("jupiter", 1)])
        s2 = _make_snapshot(planets=[_make_planet("jupiter", 5)])
        s3 = _make_snapshot(planets=[_make_planet("jupiter", 9)])
        summary = StatisticsEngine.compute_planet_house_summary((s1, s2, s3), "jupiter")
        assert summary.count == 3
        assert summary.mean == 5.0
        assert summary.median == 5.0
        assert summary.min == 1.0
        assert summary.max == 9.0

    def test_single_value(self):
        snap = _make_snapshot(planets=[_make_planet("jupiter", 7)])
        summary = StatisticsEngine.compute_planet_house_summary((snap,), "jupiter")
        assert summary.count == 1
        assert summary.mean == 7.0
        assert summary.std_dev == 0.0

    def test_empty_snapshots(self):
        summary = StatisticsEngine.compute_planet_house_summary((), "jupiter")
        assert summary.count == 0


class TestCrosstab:
    def test_crosstab_counts(self):
        def _labeled_snapshot(label: str) -> AstrologicalSnapshot:
            return AstrologicalSnapshot(
                id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
                label=label, captured_at=None, chart_ref=_make_chart([_make_planet("sun", 1)]),
            )
        s1 = _labeled_snapshot("A")
        s2 = _labeled_snapshot("B")
        s3 = _labeled_snapshot("A")
        ct = StatisticsEngine.compute_crosstab((s1, s2, s3), "label", "snapshot_version")
        assert ct.row_labels == ("A", "B")
        total = sum(sum(row) for row in ct.cells)
        assert total == 3

    def test_empty_snapshots(self):
        ct = StatisticsEngine.compute_crosstab((), "label", "snapshot_version")
        assert ct.row_labels == ()
        assert ct.column_labels == ()


class TestAggregateReport:
    def test_full_report_creation(self):
        snap = _make_snapshot(planets=[
            _make_planet("sun", 1), _make_planet("moon", 2),
        ])
        report = StatisticsEngine.compute_full_report((snap,), title="Test")
        assert report.title == "Test"
        assert report.metadata.sample_size == 1
        assert report.metadata.engine_version == "1.0"
        assert report.metadata.generated_at is not None
        assert len(report.distributions) >= 1
        assert len(report.numeric_summaries) >= 1

    def test_empty_report(self):
        report = StatisticsEngine.compute_full_report((), title="Empty")
        assert report.metadata.sample_size == 0
        assert report.metadata.filtered_sample_size is None

    def test_experiment_id_in_metadata(self):
        eid = uuid.uuid4()
        snap = _make_snapshot()
        report = StatisticsEngine.compute_full_report((snap,), experiment_id=eid)
        assert report.metadata.experiment_id == eid
