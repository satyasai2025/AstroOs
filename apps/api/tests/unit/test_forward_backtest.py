"""
Unit tests for ForwardBacktestRunner (Phase 3 Validation).
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_validation import (
    OutcomeRecord,
    OutcomeStatus,
    PredictionCategory,
)
from apps.api.services.forward_backtest_runner import (
    ForwardBacktestReport,
    ForwardBacktestRunner,
    HistoricalCohortMember,
)


@pytest.fixture
def sample_chart():
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
              "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    asc = Ascendant(0.0, 0.0, "aries", 0.0, "ashwini", 1)
    planets = [
        SiderealPosition("sun", 0.0, "aries", 0.0, 1, "ashwini", 1, False, False, None, "exalted"),
        SiderealPosition("moon", 30.0, "taurus", 0.0, 2, "krittika", 1, False, False, None, "exalted"),
        SiderealPosition("mars", 60.0, "gemini", 0.0, 3, "mrigashira", 3, False, False, None, None),
        SiderealPosition("mercury", 90.0, "cancer", 0.0, 4, "punarvasu", 4, False, False, None, None),
        SiderealPosition("jupiter", 105.0, "cancer", 15.0, 4, "pushya", 2, False, False, None, "exalted"),
        SiderealPosition("venus", 120.0, "leo", 0.0, 5, "magha", 1, False, False, None, None),
        SiderealPosition("saturn", 275.0, "capricorn", 5.0, 10, "uttara_ashadha", 2, False, False, None, "own_sign"),
        SiderealPosition("rahu", 180.0, "libra", 0.0, 7, "chitra", 3, True, False, None, None),
        SiderealPosition("ketu", 0.0, "aries", 0.0, 1, "ashwini", 1, True, False, None, None),
    ]
    houses = [HouseCusp(n, float((n - 1) * 30), float((n - 1) * 30), rashis[n - 1]) for n in range(1, 13)]
    return D1Chart(None, asc, houses, planets, [], [], None, "lahiri", "W")


@pytest.fixture
def sample_dasha_tree():
    sun_ad1 = DashaPeriod("sun", date(2026, 1, 1), date(2026, 4, 19), 108, 2, [])
    sun_ad2 = DashaPeriod("moon", date(2026, 4, 19), date(2026, 10, 19), 183, 2, [])
    sun_ad3 = DashaPeriod("mars", date(2026, 10, 19), date(2027, 2, 25), 129, 2, [])

    sun_md = DashaPeriod("sun", date(2026, 1, 1), date(2032, 1, 1), 2191, 1, [sun_ad1, sun_ad2, sun_ad3])
    return DashaTree("vimshottari", date(1990, 1, 1), "sun", "krittika", 3, [sun_md], 2, 120)


def test_forward_backtest_runner_smoke(sample_chart, sample_dasha_tree):
    runner = ForwardBacktestRunner()

    outcome = OutcomeRecord(
        outcome_id="out_001",
        chart_id="chart_backtest_001",
        subject_name="Native 1",
        category=PredictionCategory.CAREER,
        observed_date=datetime(2026, 6, 15, tzinfo=timezone.utc),
        actual_outcome_description="Promoted to Director",
        observed_direction="POSITIVE_FRUCTIFICATION",
        verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
        source_reference="Company records",
    )

    member = HistoricalCohortMember(
        chart=sample_chart,
        dasha_tree=sample_dasha_tree,
        subject_name="Native 1",
        outcomes=(outcome,),
    )

    report = runner.run_backtest(
        cohort=[member],
        dataset_name="smoke_cohort",
        target_start=date(2026, 1, 1),
        target_end=date(2027, 1, 1),
        event_types=["job_change"],
        min_confidence=0.0,
    )

    assert isinstance(report, ForwardBacktestReport)
    assert report.total_subjects == 1
    assert report.dataset_name == "smoke_cohort"
    assert report.uncertainty_disclosure is not None
    assert report.cohort_run.temporal_leakage_detected is False
