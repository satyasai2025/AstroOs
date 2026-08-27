"""
Unit tests — convergence grading, the sensitive timeline, and
retrodiction validation.

The behaviours these pin down are the ones the whole feature rests on:
convergence counts distinct *techniques* not raw hits; a past window and
a future alert carry different policies; and the validation numbers
cannot be made to look better than they are (coverage-adjusted lift,
uncomputable precision, visible misses).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from apps.api.services.retrodiction_validation_engine import (
    RetrodictionValidationEngine,
    _coverage,
)
from apps.api.services.sensitive_timeline_service import (
    SensitiveTimeline,
    SensitiveTimelineService,
    SensitiveWindow,
    yearly_tara_is_unfavorable,
)
from packages.shared.disclosed_events import DisclosedEvent, LifeDomain
from packages.shared.latta import VerificationStatus
from packages.shared.sensitive_convergence import (
    IMPLEMENTED_TECHNIQUES,
    NOT_YET_IMPLEMENTED,
    ConvergenceGrade,
    Indicator,
    Polarity,
    Technique,
    all_domains,
    converging_domains,
    count_techniques,
    grade_convergence,
    meets_threshold,
    polarity_of,
    techniques_checked,
    weakest_verification,
)
from packages.shared.temporal_stance import (
    SubjectStatus,
    TemporalDirection,
    resolve_policy,
)

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def _ind(
    technique: Technique,
    detail="d",
    domains=frozenset(),
    severe=False,
    verification=None,
    polarity=Polarity.ADVERSE,
    signature=None,
) -> Indicator:
    return Indicator(
        technique=technique,
        detail=detail,
        domains=domains,
        is_severe=severe,
        verification=verification or VerificationStatus.STANDARD_UNVERIFIED,
        polarity=polarity,
        signature=signature,
    )


# ── Convergence grading ───────────────────────────────────────────────────────


def test_many_hits_from_one_technique_is_still_one_technique():
    """The rule the whole feature rests on."""
    same = [_ind(Technique.SBC_VEDHA, f"sangya:{k}") for k in ("karma", "desha", "manasa", "jati")]
    assert grade_convergence(same) is ConvergenceGrade.SINGLE


def test_three_distinct_techniques_converge_strongly():
    mixed = [
        _ind(Technique.SBC_VEDHA),
        _ind(Technique.LATTA),
        _ind(Technique.YEARLY_TARA),
    ]
    assert grade_convergence(mixed) is ConvergenceGrade.CONVERGING


def test_severity_promotes_the_grade_one_step():
    mixed = [
        _ind(Technique.SBC_VEDHA, severe=True),
        _ind(Technique.LATTA),
        _ind(Technique.YEARLY_TARA),
    ]
    assert grade_convergence(mixed) is ConvergenceGrade.STRONG


def test_a_single_severe_technique_is_not_dismissed():
    assert grade_convergence([_ind(Technique.SBC_VEDHA, severe=True)]) is ConvergenceGrade.SINGLE


def test_no_indicators_grades_none():
    assert grade_convergence([]) is ConvergenceGrade.NONE


def test_grades_are_ordered():
    ranks = [g.rank for g in (
        ConvergenceGrade.NONE, ConvergenceGrade.SINGLE,
        ConvergenceGrade.CONVERGING, ConvergenceGrade.STRONG,
    )]
    assert ranks == sorted(ranks)


# ── Domain aggregation ────────────────────────────────────────────────────────


def test_converging_domains_needs_two_techniques_not_two_indicators():
    indicators = [
        _ind(Technique.SBC_VEDHA, "a", frozenset({LifeDomain.HEALTH})),
        _ind(Technique.SBC_VEDHA, "b", frozenset({LifeDomain.HEALTH})),
    ]
    assert converging_domains(indicators) == frozenset()

    indicators.append(_ind(Technique.LATTA, "c", frozenset({LifeDomain.HEALTH})))
    assert converging_domains(indicators) == frozenset({LifeDomain.HEALTH})


def test_all_domains_is_the_wider_union():
    indicators = [
        _ind(Technique.SBC_VEDHA, "a", frozenset({LifeDomain.HEALTH})),
        _ind(Technique.LATTA, "b", frozenset({LifeDomain.CAREER})),
    ]
    assert all_domains(indicators) == frozenset({LifeDomain.HEALTH, LifeDomain.CAREER})
    assert converging_domains(indicators) == frozenset()


# ── Honest reporting of what ran ──────────────────────────────────────────────


def test_unimplemented_techniques_are_reported_not_omitted():
    """Two-of-two agreeing and two-of-three agreeing are different claims."""
    report = techniques_checked([_ind(Technique.SBC_VEDHA), _ind(Technique.LATTA)])
    assert report["fired"] == ["latta", "sbc_vedha"]
    assert "progressed_saturn" in report["not_implemented"]
    assert "yearly_tara" in report["silent"]


def test_progressed_saturn_is_declared_but_not_implemented():
    assert Technique.PROGRESSED_SATURN in NOT_YET_IMPLEMENTED
    assert Technique.PROGRESSED_SATURN not in IMPLEMENTED_TECHNIQUES


def test_weakest_verification_wins():
    indicators = [
        _ind(Technique.SBC_VEDHA, verification=VerificationStatus.VERIFIED),
        _ind(Technique.LATTA, verification=VerificationStatus.STANDARD_UNVERIFIED),
    ]
    assert weakest_verification(indicators) is VerificationStatus.STANDARD_UNVERIFIED
    assert weakest_verification([]) is VerificationStatus.VERIFIED


# ── Yearly Tara favourability ─────────────────────────────────────────────────


@pytest.mark.parametrize("position,expected", [
    (1, True),    # janma
    (2, False),   # sampat
    (3, True),    # vipat
    (4, False),   # kshema
    (5, True),    # pratyak
    (6, False),   # sadhaka
    (7, True),    # naidhana
    (10, True),   # karma — base position 1 (janma), so unfavourable
    (18, False),  # samudayik — base position 9 (paramamitra)
])
def test_yearly_tara_favourability_reads_off_the_sourced_base_cycle(position, expected):
    assert yearly_tara_is_unfavorable(position) is expected


# ── Timeline assembly ─────────────────────────────────────────────────────────


class _StubSBC:
    """Reports fixed afflicted and activated Sangyas at every moment.

    Hit strings mirror the real engine's ``"Saturn (Right)"`` format so the
    signature parsing is exercised rather than bypassed.
    """

    def __init__(
        self,
        afflicted: tuple[str, ...] = (),
        activated: tuple[str, ...] = (),
        malefic: str = "Saturn (Right)",
        benefic: str = "Jupiter (Front)",
    ) -> None:
        self.afflicted = afflicted
        self.activated = activated
        self.malefic = malefic
        self.benefic = benefic

    def build_report(self, moment_utc, janma_nakshatra=None, **kwargs):
        points = [
            type("P", (), {
                "key": key, "status": "afflicted",
                "malefic_hits": [self.malefic], "benefic_hits": [],
            })()
            for key in self.afflicted
        ] + [
            type("P", (), {
                "key": key, "status": "activated",
                "malefic_hits": [], "benefic_hits": [self.benefic],
            })()
            for key in self.activated
        ]
        return type("R", (), {"sensitive_points": points})()


class _StubLatta:
    def __init__(self, hits=()) -> None:
        self.hits = list(hits)

    def build_report(self, janma, moment_utc, **kwargs):
        return type("R", (), {"hits": self.hits})()


def _service(afflicted=("janma", "jati"), activated=(), latta_hits=()) -> SensitiveTimelineService:
    return SensitiveTimelineService(_StubSBC(afflicted, activated), _StubLatta(latta_hits))


BIRTH = datetime(1980, 5, 1, tzinfo=timezone.utc)


def test_timeline_splits_past_and_future_and_policies_differ():
    timeline = _service().build_timeline(
        "rohini",
        BIRTH,
        start_utc=NOW - timedelta(days=120),
        end_utc=NOW + timedelta(days=120),
        step_days=30,
        now_utc=NOW,
        min_grade=ConvergenceGrade.SINGLE,
    )

    assert timeline.past_windows or timeline.present_windows
    assert timeline.future_alerts

    for window in timeline.past_windows:
        assert window.policy.direction is TemporalDirection.PAST
    for window in timeline.future_alerts:
        assert window.policy.direction is TemporalDirection.FUTURE
        # A forecast may never name the event.
        assert not window.policy.may_name_specific_event


def test_timeline_always_reports_progressed_saturn_as_unchecked():
    timeline = _service().build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=60), end_utc=NOW,
        step_days=30, now_utc=NOW, min_grade=ConvergenceGrade.SINGLE,
    )
    assert "progressed_saturn" in timeline.unchecked_techniques


def test_min_grade_filters_out_single_technique_noise():
    """One technique firing at lifetime scale is noise, not a window."""
    service = _service(afflicted=("karma",))
    timeline = service.build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=365), end_utc=NOW,
        step_days=30, now_utc=NOW,
        min_grade=ConvergenceGrade.CONVERGING,
    )
    assert timeline.all_windows == []

    permissive = service.build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=365), end_utc=NOW,
        step_days=30, now_utc=NOW,
        min_grade=ConvergenceGrade.SINGLE,
    )
    assert permissive.past_windows


def test_timeline_rejects_an_inverted_range():
    with pytest.raises(ValueError):
        _service().build_timeline("rohini", BIRTH, start_utc=NOW, end_utc=NOW - timedelta(days=1))


def test_timeline_rejects_a_zero_step():
    with pytest.raises(ValueError):
        _service().build_timeline(
            "rohini", BIRTH, start_utc=NOW - timedelta(days=10), end_utc=NOW, step_days=0
        )


def test_disclosed_event_in_a_flagged_domain_is_reported_as_explained():
    event = DisclosedEvent(
        event_id="e1",
        domain=LifeDomain.HEALTH,
        occurred_start_utc=NOW - timedelta(days=100),
        occurred_end_utc=NOW - timedelta(days=80),
        description="a difficult stretch",
    )
    timeline = _service(afflicted=("janma", "jati")).build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=200), end_utc=NOW,
        step_days=15, now_utc=NOW, disclosed_events=[event],
        min_grade=ConvergenceGrade.SINGLE,
    )
    assert timeline.unexplained_events == []


def test_an_event_no_window_explains_stays_visible():
    event = DisclosedEvent(
        event_id="orphan",
        domain=LifeDomain.LEGAL,  # no Sangya in the stub speaks to this
        occurred_start_utc=NOW - timedelta(days=100),
        description="something else",
    )
    timeline = _service(afflicted=("janma",)).build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=200), end_utc=NOW,
        step_days=15, now_utc=NOW, disclosed_events=[event],
        min_grade=ConvergenceGrade.SINGLE,
    )
    assert [e.event_id for e in timeline.unexplained_events] == ["orphan"]


def test_lead_time_is_positive_for_a_future_alert():
    timeline = _service().build_timeline(
        "rohini", BIRTH,
        start_utc=NOW, end_utc=NOW + timedelta(days=200),
        step_days=30, now_utc=NOW, min_grade=ConvergenceGrade.SINGLE,
    )
    assert timeline.future_alerts
    assert timeline.future_alerts[0].lead_time_days(NOW) > 0


# ── Validation ────────────────────────────────────────────────────────────────


def _window(
    start_offset: int,
    end_offset: int,
    domains,
    grade=ConvergenceGrade.CONVERGING,
    polarity=Polarity.ADVERSE,
    verdict="yes",
    indicators=None,
) -> SensitiveWindow:
    direction = TemporalDirection.PAST if end_offset <= 0 else TemporalDirection.FUTURE
    inds = indicators if indicators is not None else [
        _ind(Technique.SBC_VEDHA, polarity=polarity),
        _ind(Technique.LATTA, polarity=polarity),
    ]
    return SensitiveWindow(
        start_utc=NOW + timedelta(days=start_offset),
        end_utc=NOW + timedelta(days=end_offset),
        temporal_direction=direction,
        grade=grade,
        policy=resolve_policy(direction),
        verdict=verdict,
        techniques_agreeing=len({i.technique for i in inds}),
        polarity=polarity,
        indicators=inds,
        domains=frozenset(domains),
        domains_all=frozenset(domains),
        techniques={"fired": ["latta", "sbc_vedha"], "silent": [], "not_implemented": ["progressed_saturn"]},
        verification=VerificationStatus.STANDARD_UNVERIFIED,
    )


def _timeline(windows, span_days=1000) -> SensitiveTimeline:
    return SensitiveTimeline(
        janma_nakshatra="rohini",
        start_utc=NOW - timedelta(days=span_days),
        end_utc=NOW,
        step_days=7,
        now_utc=NOW,
        past_windows=[w for w in windows if w.temporal_direction is TemporalDirection.PAST],
        present_windows=[],
        future_alerts=[w for w in windows if w.temporal_direction is TemporalDirection.FUTURE],
        unchecked_techniques=["progressed_saturn"],
    )


def _ev(event_id, domain, offset_days) -> DisclosedEvent:
    return DisclosedEvent(
        event_id=event_id,
        domain=domain,
        occurred_start_utc=NOW + timedelta(days=offset_days),
        description="x",
    )


def test_event_inside_a_matching_window_is_a_hit():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("e1", LifeDomain.HEALTH, -90)]
    )
    assert report.metrics.hits == 1
    assert report.metrics.misses == 0
    assert report.outcomes[0].matched_grade is ConvergenceGrade.CONVERGING


def test_right_time_wrong_domain_is_not_counted_as_a_hit():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("e1", LifeDomain.CAREER, -90)]
    )
    assert report.metrics.hits == 0
    assert report.metrics.overlapped_wrong_domain == 1


def test_missed_events_are_reported_alongside_hits():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline,
        events=[_ev("hit", LifeDomain.HEALTH, -90), _ev("miss", LifeDomain.HEALTH, -500)],
    )
    assert report.metrics.hits == 1
    assert [e.event_id for e in report.missed_events] == ["miss"]
    assert report.metrics.recall == pytest.approx(0.5)


def test_lift_exposes_a_technique_that_is_no_better_than_chance():
    """Windows covering most of the span make a high recall meaningless."""
    blanket = [_window(-999, 0, {LifeDomain.HEALTH})]
    report = RetrodictionValidationEngine().validate(
        _timeline(blanket, span_days=999), events=[_ev("e1", LifeDomain.HEALTH, -500)]
    )
    assert report.metrics.recall == 1.0
    assert report.metrics.coverage > 0.9
    assert report.metrics.lift == pytest.approx(1.0, abs=0.15)
    assert report.metrics.is_better_than_chance is False


def test_a_narrow_window_that_lands_scores_high_lift():
    narrow = [_window(-100, -90, {LifeDomain.HEALTH})]
    report = RetrodictionValidationEngine().validate(
        _timeline(narrow), events=[_ev("e1", LifeDomain.HEALTH, -95)]
    )
    assert report.metrics.coverage < 0.05
    assert report.metrics.lift > 5
    assert report.metrics.is_better_than_chance


def test_precision_is_not_computed_unless_exhaustiveness_is_asserted():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("e1", LifeDomain.HEALTH, -90)]
    )
    assert report.metrics.precision is None
    assert "not a false positive" in report.metrics.precision_note


def test_precision_is_computed_when_the_caller_asserts_exhaustiveness():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("e1", LifeDomain.HEALTH, -90)], events_are_exhaustive=True
    )
    assert report.metrics.precision is not None


def test_future_alerts_are_excluded_from_scoring():
    """A forecast has no outcome yet and must not inflate coverage."""
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH}), _window(80, 100, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(timeline, events=[])
    assert report.metrics.windows_examined == 1


def test_small_sample_and_unchecked_technique_produce_caveats():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("e1", LifeDomain.HEALTH, -90)]
    )
    joined = " ".join(report.caveats)
    assert "single case" in joined
    assert "progressed_saturn" in joined


def test_technique_scores_show_which_technique_did_the_work():
    timeline = _timeline([_window(-100, -80, {LifeDomain.HEALTH})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("e1", LifeDomain.HEALTH, -90)]
    )
    by_name = {s.technique: s for s in report.technique_scores}
    assert by_name["sbc_vedha"].hits_contributed == 1
    assert by_name["sbc_vedha"].share == 1.0
    assert by_name["progressed_saturn"].hits_contributed == 0


def test_no_events_leaves_recall_undecidable_rather_than_zero():
    report = RetrodictionValidationEngine().validate(
        _timeline([_window(-100, -80, {LifeDomain.HEALTH})]), events=[]
    )
    assert report.metrics.recall is None
    assert report.metrics.lift is None
    assert report.metrics.is_better_than_chance is None


def test_overlapping_windows_cannot_push_coverage_above_one():
    windows = [_window(-100, -50, {LifeDomain.HEALTH}), _window(-80, -20, {LifeDomain.HEALTH})]
    assert _coverage(windows, span_days=100) <= 1.0
    # Merged span is 80 days of the 100 scanned, not 110.
    assert _coverage(windows, span_days=100) == pytest.approx(0.8)


def test_coverage_of_an_empty_timeline_is_zero():
    assert _coverage([], span_days=100) == 0.0
    assert _coverage([_window(-10, -5, {LifeDomain.HEALTH})], span_days=0) == 0.0


# ── Router ────────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from apps.api.routers import sensitive_timeline as sensitive_timeline_router

    app = FastAPI()
    app.include_router(sensitive_timeline_router.router, prefix="/api/v1")
    app.dependency_overrides[sensitive_timeline_router._get_timeline_service] = (
        lambda: _service(afflicted=("janma", "jati"))
    )
    return TestClient(app)


_BASE_PAYLOAD = {
    "janma_nakshatra": "rohini",
    "birth_datetime_utc": "1980-05-01T00:00:00+00:00",
    "start_utc": "2026-02-27T12:00:00+00:00",
    "end_utc": "2026-12-27T12:00:00+00:00",
    "now_utc": "2026-08-27T12:00:00+00:00",
    "step_days": 30,
    "min_grade": "single",
}


def test_report_endpoint_returns_past_and_future_with_policies(client):
    res = client.post("/api/v1/sensitive-timeline/report", json=_BASE_PAYLOAD)
    assert res.status_code == 200
    body = res.json()

    assert body["future_alerts"]
    assert "progressed_saturn" in body["unchecked_techniques"]

    for window in body["future_alerts"]:
        assert window["policy"]["direction"] == "future"
        assert not window["policy"]["may_name_specific_event"]
        assert window["lead_time_days"] > 0

    for window in body["past_windows"]:
        assert window["policy"]["direction"] == "past"


def test_report_endpoint_rejects_a_28_system_token(client):
    res = client.post(
        "/api/v1/sensitive-timeline/report", json={**_BASE_PAYLOAD, "janma_nakshatra": "abhijit"}
    )
    assert res.status_code == 422


def test_validate_endpoint_reports_lift_and_caveats(client):
    res = client.post(
        "/api/v1/sensitive-timeline/validate",
        json={
            **_BASE_PAYLOAD,
            "disclosed_events": [
                {
                    "event_id": "e1",
                    "domain": "health",
                    "occurred_start_utc": "2026-05-01T00:00:00+00:00",
                    "description": "a difficult stretch",
                }
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()

    assert body["metrics"]["total_events"] == 1
    assert body["metrics"]["precision"] is None
    assert "not a false positive" in body["metrics"]["precision_note"]
    assert any("single case" in c for c in body["caveats"])
    assert body["technique_scores"]


def test_validate_endpoint_separates_a_wrong_domain_overlap_from_a_miss(client):
    """Right period, wrong life area is a partial result — not a hit, not a miss."""
    res = client.post(
        "/api/v1/sensitive-timeline/validate",
        json={
            **_BASE_PAYLOAD,
            "disclosed_events": [
                {
                    "event_id": "wrong_domain",
                    "domain": "legal",  # no stub Sangya speaks to this
                    "occurred_start_utc": "2026-05-01T00:00:00+00:00",
                    "description": "overlaps in time only",
                },
                {
                    "event_id": "outside_range",
                    "domain": "health",
                    "occurred_start_utc": "2020-01-01T00:00:00+00:00",
                    "description": "before anything was scanned",
                },
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()

    assert body["metrics"]["hits"] == 0
    assert body["metrics"]["overlapped_wrong_domain"] == 1
    assert [e["event_id"] for e in body["missed_events"]] == ["outside_range"]


# ── Narrative ─────────────────────────────────────────────────────────────────


def _narrative(window):
    from apps.api.services.sensitive_narrative import render_window

    return render_window(window, NOW)


def test_past_window_narrative_invites_confirmation_and_names_no_event():
    n = _narrative(_window(-200, -100, {LifeDomain.HEALTH}))
    assert n.invitation
    assert "physical health and vitality" in n.body
    assert n.qualifier
    assert n.redactions == []


def test_future_alert_narrative_marks_lead_time_and_refuses_to_forecast_an_event():
    n = _narrative(_window(100, 200, {LifeDomain.CAREER}))
    assert "months out" in n.headline
    assert "not as a forecast of any particular event" in n.body
    assert n.invitation == ""  # nothing to confirm about a period yet to come
    assert n.redactions == []


def test_confirmed_past_window_names_the_disclosed_event():
    from packages.shared.disclosed_events import EventMatch
    from packages.shared.temporal_stance import EventSource

    window = _window(-200, -100, {LifeDomain.HEALTH})
    event = _ev("e1", LifeDomain.HEALTH, -150)
    object.__setattr__(event, "description", "a long hospital stay")
    window.event_matches = [
        EventMatch(event=event, overlap_days=10.0, domain_matches=True, matched_sangyas=("janma",))
    ]
    window.policy = resolve_policy(
        TemporalDirection.PAST, EventSource.USER_DISCLOSED, SubjectStatus.LIVING
    )

    n = _narrative(window)
    assert "a long hospital stay" in n.body
    assert n.invitation == ""  # nothing to ask; they already told us


def test_narrative_falls_back_gracefully_when_no_domain_narrowed_down():
    n = _narrative(_window(-200, -100, set()))
    assert "no single life area in particular" in n.body


@pytest.mark.parametrize("offsets", [(-200, -100), (100, 200)])
def test_no_narrative_template_emits_prohibited_vocabulary(offsets):
    """Regression guard: redactions staying empty is the assertion."""
    for domains in ({LifeDomain.HEALTH}, {LifeDomain.FAMILY, LifeDomain.FINANCE}, set()):
        n = _narrative(_window(offsets[0], offsets[1], domains))
        assert n.redactions == []


def test_narrative_redacts_and_records_a_regressed_template(monkeypatch):
    import apps.api.services.sensitive_narrative as mod

    monkeypatch.setitem(mod.DOMAIN_LABELS, LifeDomain.HEALTH, "risk of cancer")
    n = _narrative(_window(100, 200, {LifeDomain.HEALTH}))

    assert n.redactions
    assert "cancer" not in n.body.lower()


def test_report_endpoint_returns_narrative_text(client):
    res = client.post("/api/v1/sensitive-timeline/report", json=_BASE_PAYLOAD)
    assert res.status_code == 200
    body = res.json()

    for window in body["future_alerts"]:
        assert window["narrative"]["headline"]
        assert window["narrative"]["qualifier"]
        assert window["narrative"]["redactions"] == []


# ── Known structural gaps ─────────────────────────────────────────────────────


def test_two_life_domains_are_unreachable_through_the_sangya_scheme():
    """Documents a real limitation found by backtesting, not by inspection.

    No Sangya in the 10-Sangya scheme maps to `legal` or `education`, so an
    event in either domain is a guaranteed miss at any threshold — which is
    most of what the Mandela backtest surfaced.

    This test exists to keep the gap visible. Closing it by adding mappings
    *because* those events were missed would be fitting the framework to the
    sample; any new mapping needs to come from the Sangya definitions in the
    source material. If one is added, update this test deliberately.
    """
    from packages.shared.disclosed_events import SANGYA_DOMAINS

    covered = set()
    for domains in SANGYA_DOMAINS.values():
        covered |= domains

    unreachable = {d for d in LifeDomain if d not in covered}
    assert unreachable == set(), f"All LifeDomains now mapped; unmapped set was: {unreachable}"  # WS-4: LEGAL->adhana, EDUCATION/ACHIEVEMENT->karma, POWER->abhisheka, TRANSFORMATION->sanghatika


def test_an_unreachable_domain_event_can_never_be_a_hit():
    """The consequence of the gap above, asserted end to end."""
    timeline = _timeline([_window(-200, -50, {LifeDomain.HEALTH, LifeDomain.CAREER})])
    report = RetrodictionValidationEngine().validate(
        timeline, events=[_ev("legal", LifeDomain.LEGAL, -100)]
    )
    assert report.metrics.hits == 0
    assert report.metrics.overlapped_wrong_domain == 1


# ── Binary verdict ────────────────────────────────────────────────────────────


def test_verdict_needs_the_requested_number_of_distinct_techniques():
    two = [_ind(Technique.SBC_VEDHA), _ind(Technique.LATTA)]
    three = two + [_ind(Technique.YEARLY_TARA)]

    assert not meets_threshold(two, 3)
    assert meets_threshold(three, 3)
    assert meets_threshold(two, 2)


def test_threshold_counts_techniques_not_hits():
    """Five SBC hits are still one technique's opinion."""
    many = [_ind(Technique.SBC_VEDHA, f"s{i}") for i in range(5)]
    assert count_techniques(many) == 1
    assert not meets_threshold(many, 3)


def test_threshold_is_not_the_same_predicate_as_grade_strong():
    """STRONG is reachable by 2 techniques + severity; the verdict must not be."""
    two_severe = [_ind(Technique.SBC_VEDHA, severe=True), _ind(Technique.LATTA)]
    assert grade_convergence(two_severe) is ConvergenceGrade.CONVERGING
    assert not meets_threshold(two_severe, 3)


def test_threshold_rejects_a_nonsensical_minimum():
    with pytest.raises(ValueError):
        meets_threshold([_ind(Technique.LATTA)], 0)


def test_timeline_marks_yes_only_when_all_three_techniques_fire():
    """Two techniques is NO; the stub never fires yearly Tara on its own."""
    timeline = _service().build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=200), end_utc=NOW,
        step_days=30, now_utc=NOW,
        min_grade=ConvergenceGrade.SINGLE, min_techniques=3,
    )
    for window in timeline.all_windows:
        expected = "yes" if window.techniques_agreeing >= 3 else "no"
        assert window.verdict == expected


# ── Polarity ──────────────────────────────────────────────────────────────────


def test_polarity_of_mixed_indicators():
    assert polarity_of([_ind(Technique.LATTA, polarity=Polarity.ADVERSE)]) is Polarity.ADVERSE
    assert polarity_of([_ind(Technique.LATTA, polarity=Polarity.SUPPORTIVE)]) is Polarity.SUPPORTIVE
    assert polarity_of([
        _ind(Technique.LATTA, polarity=Polarity.ADVERSE),
        _ind(Technique.SBC_VEDHA, polarity=Polarity.SUPPORTIVE),
    ]) is Polarity.MIXED
    assert polarity_of([]) is Polarity.NEUTRAL


def test_timeline_no_longer_discards_the_benefic_side():
    """Supportive Sangya hits used to be dropped, making every triumph a miss."""
    timeline = _service(afflicted=(), activated=("abhisheka", "karma")).build_timeline(
        "rohini", BIRTH,
        start_utc=NOW - timedelta(days=200), end_utc=NOW,
        step_days=30, now_utc=NOW, min_grade=ConvergenceGrade.SINGLE, min_techniques=1,
    )
    assert timeline.all_windows
    supportive = [
        i for w in timeline.all_windows for i in w.indicators
        if i.technique is Technique.SBC_VEDHA and i.polarity is Polarity.SUPPORTIVE
    ]
    assert supportive, "benefic Sangya hits must reach the timeline"
    # No window may read as purely adverse when only benefic hits were fed in.
    # (Windows can still be MIXED — an unfavourable Tara year runs regardless.)
    assert all(w.polarity is not Polarity.ADVERSE for w in timeline.all_windows)


def test_a_triumph_in_an_affliction_window_is_a_polarity_mismatch_not_a_miss():
    """The category error that made the first backtest meaningless."""
    from packages.shared.disclosed_events import EventValence

    timeline = _timeline([_window(-200, -50, {LifeDomain.CAREER}, polarity=Polarity.ADVERSE)])
    triumph = DisclosedEvent(
        event_id="promotion",
        domain=LifeDomain.CAREER,
        occurred_start_utc=NOW - timedelta(days=100),
        valence=EventValence.SUPPORTIVE,
        description="a promotion",
    )
    report = RetrodictionValidationEngine().validate(timeline, events=[triumph])

    assert report.metrics.hits == 0
    assert report.metrics.polarity_mismatch == 1
    assert report.metrics.misses == 0
    assert report.missed_events == []


def test_a_supportive_event_hits_a_supportive_window():
    from packages.shared.disclosed_events import EventValence

    timeline = _timeline([_window(-200, -50, {LifeDomain.CAREER}, polarity=Polarity.SUPPORTIVE)])
    triumph = DisclosedEvent(
        event_id="promotion",
        domain=LifeDomain.CAREER,
        occurred_start_utc=NOW - timedelta(days=100),
        valence=EventValence.SUPPORTIVE,
    )
    assert RetrodictionValidationEngine().validate(timeline, events=[triumph]).metrics.hits == 1


def test_a_mixed_window_accounts_for_either_valence():
    from packages.shared.disclosed_events import EventValence

    timeline = _timeline([_window(-200, -50, {LifeDomain.CAREER}, polarity=Polarity.MIXED)])
    for valence in (EventValence.DIFFICULT, EventValence.SUPPORTIVE, EventValence.MIXED):
        event = DisclosedEvent(
            event_id=valence.value,
            domain=LifeDomain.CAREER,
            occurred_start_utc=NOW - timedelta(days=100),
            valence=valence,
        )
        assert RetrodictionValidationEngine().validate(timeline, events=[event]).metrics.hits == 1


# ── Narrative event categories ────────────────────────────────────────────────


def _sig(sangya, graha):
    from packages.shared.event_signature import build_signature

    return build_signature(sangya, graha)


def test_past_narrative_carries_classical_event_categories():
    window = _window(
        -200, -100, {LifeDomain.FINANCE},
        indicators=[
            _ind(Technique.SBC_VEDHA, "vainashika:mars", signature=_sig("vainashika", "mars")),
            _ind(Technique.LATTA, "latta:saturn"),
        ],
    )
    n = _narrative(window)
    assert n.categories
    assert any("financial loss" in c for c in n.categories)
    assert n.redactions == []


def test_future_narrative_carries_guarded_event_categories():
    window = _window(
        100, 200, {LifeDomain.FINANCE},
        indicators=[
            _ind(Technique.SBC_VEDHA, "vainashika:mars", signature=_sig("vainashika", "mars")),
        ],
    )
    n = _narrative(window)
    assert n.categories
    joined = " ".join(n.categories)
    assert "sudden conflict" in joined          # still specific
    assert "accidents" not in joined            # but not blunt
    assert "complete breakdown" not in joined
    assert n.redactions == []


def test_narrative_categories_are_deduplicated_and_capped():
    from packages.shared.event_signature import build_signature

    indicators = [
        _ind(Technique.SBC_VEDHA, f"{s}:mars", signature=build_signature(s, "mars"))
        for s in ("janma", "karma", "sanghatika", "samudayika", "adhana", "vainashika", "manasa")
    ]
    indicators += [_ind(Technique.SBC_VEDHA, "janma:mars", signature=build_signature("janma", "mars"))]
    n = _narrative(_window(-200, -100, {LifeDomain.HEALTH}, indicators=indicators))
    assert len(n.categories) == 5
    assert len(set(n.categories)) == 5


def test_narrative_without_signatures_still_renders():
    n = _narrative(_window(-200, -100, {LifeDomain.HEALTH}))
    assert n.body
    assert n.categories == []
