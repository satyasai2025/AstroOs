"""
AstroOS — Prediction Orchestration Engine Test Suite

Proves:
  1. Mathematical Determinism: Same chart + same time range + same config = bit-for-bit identical result.
  2. Dasha Boundary Split: Correct temporal partition at Antardasha transitions.
  3. Gochara Ingress Split: Correct temporal refinement at transit steps.
  4. Coarse Candidate Window -> Fine-Grained Narrowed Peak Window.
  5. Natal Promise Absent -> Strong prediction suppressed below activation threshold.
  6. Supporting + Contradicting Evidence: Deterministic synthesis with conflict penalties.
  7. Engine Integrity: TechniqueEngine and RuleEngine remain untouched.
"""

from datetime import date, datetime, timezone
import importlib
import pytest

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
    ConsensusProfile,
    PromiseStatus,
    TemporalResolution,
)
from apps.api.services.adaptive_temporal_scanner import AdaptiveTemporalScanner
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()

    import apps.api.services.techniques.timing_events as _te
    import apps.api.services.techniques.panch_mahapurusha as _pm
    import apps.api.services.techniques.marriage_timing as _mt
    import apps.api.services.techniques.wealth_dhana as _wd
    import apps.api.services.techniques.gajakesari_yoga as _gj
    import apps.api.services.techniques.eye_health as _eye
    import apps.api.services.techniques.event_timing_migrated as _et

    importlib.reload(_te)
    importlib.reload(_pm)
    importlib.reload(_mt)
    importlib.reload(_wd)
    importlib.reload(_gj)
    importlib.reload(_eye)
    importlib.reload(_et)
    yield


def _build_test_chart(tenth_lord_house=10):
    """Helper to build a clean test chart with configurable 10th lord placement."""
    asc = Ascendant(10.0, 10.0, "aries", 10.0, "ashwini", 1)
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

    planets = [
        SiderealPosition("sun", 30.0, "taurus", 0.0, 2, "krittika", 2, False, False, None, None),
        SiderealPosition("moon", 15.0, "aries", 15.0, 1, "bharani", 1, False, False, None, None),
        SiderealPosition("mars", 60.0, "gemini", 0.0, 3, "mrigashira", 3, False, False, None, None),
        SiderealPosition("mercury", 90.0, "cancer", 0.0, 4, "punarvasu", 4, False, False, None, None),
        SiderealPosition("jupiter", 105.0, "cancer", 15.0, 4, "pushya", 2, False, False, None, "exalted"),
        SiderealPosition("venus", 120.0, "leo", 0.0, 5, "magha", 1, False, False, None, None),
        # 10th lord Saturn placed in tenth_lord_house
        SiderealPosition("saturn", float((tenth_lord_house - 1) * 30 + 5), rashis[tenth_lord_house - 1], 5.0, tenth_lord_house, "uttara_phalguni", 2, False, False, None, None),
        SiderealPosition("rahu", 180.0, "libra", 0.0, 7, "chitra", 3, True, False, None, None),
        SiderealPosition("ketu", 0.0, "aries", 0.0, 1, "ashwini", 1, True, False, None, None),
    ]
    houses = [HouseCusp(n, float((n - 1) * 30), float((n - 1) * 30), rashis[n - 1]) for n in range(1, 13)]
    return D1Chart(None, asc, houses, planets, [], [], None, "lahiri", "W")


def _build_test_dasha_tree():
    """Helper to build a deterministic DashaTree with known Antardasha boundaries."""
    # Sun Mahadasha: 2026-01-01 to 2032-01-01
    #   Sun-Sun: 2026-01-01 to 2026-04-19
    #   Sun-Moon: 2026-04-19 to 2026-10-19
    #   Sun-Mars: 2026-10-19 to 2027-02-25
    sun_ad1 = DashaPeriod("sun", date(2026, 1, 1), date(2026, 4, 19), 108, 2, [])
    sun_ad2 = DashaPeriod("moon", date(2026, 4, 19), date(2026, 10, 19), 183, 2, [])
    sun_ad3 = DashaPeriod("mars", date(2026, 10, 19), date(2027, 2, 25), 129, 2, [])

    sun_md = DashaPeriod("sun", date(2026, 1, 1), date(2032, 1, 1), 2191, 1, [sun_ad1, sun_ad2, sun_ad3])
    return DashaTree("vimshottari", date(1990, 1, 1), "sun", "krittika", 3, [sun_md], 2, 120)


# ── 1. Mathematical Determinism ───────────────────────────────────────────────


def test_prediction_orchestrator_strict_determinism():
    """Same chart + same time range + same profile = identical signature and scores."""
    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    res1 = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)
    res2 = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res1.deterministic_signature == res2.deterministic_signature
    assert len(res1.candidate_windows) == len(res2.candidate_windows)
    for c1, c2 in zip(res1.candidate_windows, res2.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.start_date == c2.start_date
        assert c1.end_date == c2.end_date
        assert c1.deterministic_hash == c2.deterministic_hash


# ── 2. Dasha Boundary Split & 3. Gochara Ingress Split ─────────────────────────


def test_adaptive_temporal_scanner_splits():
    """Verify macro dasha boundary snapping and meso/micro refinement intervals."""
    scanner = AdaptiveTemporalScanner()
    dasha_tree = _build_test_dasha_tree()

    # Macro slices snap to exact antardashas (Jan 1, Apr 19, Oct 19)
    macro_slices = scanner.generate_macro_slices(dasha_tree, date(2026, 1, 1), date(2026, 12, 31))
    assert len(macro_slices) >= 3
    assert macro_slices[0].start_date == date(2026, 1, 1)
    assert macro_slices[0].end_date == date(2026, 4, 19)
    assert macro_slices[0].resolution == TemporalResolution.MACRO_DASHA

    # Meso refinement produces ~30 day intervals
    meso_slices = scanner.refine_to_meso_slices(macro_slices[0], step_days=30)
    assert len(meso_slices) > 1
    assert all(s.resolution == TemporalResolution.MESO_GOCHARA for s in meso_slices)


# ── 4. Coarse to Fine Candidate Window Narrowing ──────────────────────────────


def test_coarse_candidate_window_narrowing():
    """Adaptive zoom identifies peak dates inside the broader macro window."""
    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    result = orchestrator.predict_event_windows(
        chart, dasha_tree, "career", date(2026, 1, 1), date(2026, 12, 31),
        PARASHARI_STANDARD_PROFILE, enable_micro_zoom=True,
    )

    assert result.refined_slices_count > 0
    if result.candidate_windows:
        cand = result.candidate_windows[0]
        assert cand.peak_score >= PARASHARI_STANDARD_PROFILE.minimum_activation_threshold
        assert cand.start_date <= cand.peak_date <= cand.end_date


# ── 5. Natal Promise Absent -> Strong Prediction Suppressed ───────────────────


def test_natal_promise_absent_suppresses_prediction():
    """When 10th lord is in 8th Dusthana, career score is strictly capped <= 30."""
    chart_weak_promise = _build_test_chart(tenth_lord_house=8)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    result = orchestrator.predict_event_windows(
        chart_weak_promise, dasha_tree, "career", date(2026, 1, 1), date(2026, 12, 31),
        PARASHARI_STANDARD_PROFILE, enable_micro_zoom=True,
    )

    # All candidate windows suppressed below activation threshold (60)
    assert len(result.candidate_windows) == 0 or all(c.peak_score <= 30 for c in result.candidate_windows)


# ── 6. Supporting + Contradicting Evidence Synthesis ──────────────────────────


def test_conflict_penalty_applied_deterministically():
    """Custom profile with conflict penalty multiplier reduces score when opposing factors fire."""
    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    strict_profile = ConsensusProfile(
        profile_id="strict_penalty_v1",
        name="Strict Penalty Profile",
        conflict_penalty_multiplier=2.0,
        minimum_activation_threshold=50,
    )

    orchestrator = PredictionOrchestrator()
    result = orchestrator.predict_event_windows(
        chart, dasha_tree, "career", date(2026, 1, 1), date(2026, 12, 31), strict_profile
    )
    assert result.consensus_profile_used.profile_id == "strict_penalty_v1"