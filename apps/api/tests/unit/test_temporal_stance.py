"""
Unit tests — temporal stance policy, disclosed events, and the SBC
analyzer's retrodiction path.

The point of these is that the *distinction* holds: a past window and a
future window must not be allowed to say the same things, and a template
edit that reintroduces disease/mortality vocabulary into a forecast must
fail here rather than reach a native.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from apps.api.schemas.ai import AISBCAnalysisRequest, DisclosedEventInput
from apps.api.services.sbc_ai_analyzer import SBCAIAnalyzer
from apps.api.services.sbc_scan_engine import (
    SBCScanHit,
    SeverityTier,
    group_into_windows,
    severity_tier,
)
from packages.shared.disclosed_events import (
    DisclosedEvent,
    EventValence,
    LifeDomain,
    domains_for_sangyas,
    match_events,
)
from packages.shared.temporal_stance import (
    EventSource,
    LanguageCategory,
    StancePolicyViolation,
    SubjectStatus,
    TemporalDirection,
    Voice,
    assert_compliant,
    classify_direction,
    policy_for_moment,
    redact,
    resolve_policy,
    scan_text,
)

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


# ── Direction classification ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "offset_days,expected",
    [
        (-3650, TemporalDirection.PAST),
        (-8, TemporalDirection.PAST),
        (-7, TemporalDirection.PRESENT),
        (0, TemporalDirection.PRESENT),
        (7, TemporalDirection.PRESENT),
        (8, TemporalDirection.FUTURE),
        (3650, TemporalDirection.FUTURE),
    ],
)
def test_classify_direction_boundaries(offset_days, expected):
    moment = NOW + timedelta(days=offset_days)
    assert classify_direction(moment, NOW) == expected


def test_classify_direction_assumes_utc_for_naive_input():
    naive = (NOW - timedelta(days=100)).replace(tzinfo=None)
    assert classify_direction(naive, NOW) == TemporalDirection.PAST


def test_classify_direction_rejects_negative_window():
    with pytest.raises(ValueError):
        classify_direction(NOW, NOW, present_window_days=-1)


# ── Policy matrix ─────────────────────────────────────────────────────────────


def test_future_window_may_not_name_an_event():
    policy = resolve_policy(TemporalDirection.FUTURE)
    assert policy.voice is Voice.PROSPECTIVE
    assert not policy.may_name_specific_event
    assert not policy.longevity_formula_allowed
    assert policy.prohibited_categories == frozenset(
        {LanguageCategory.MORTALITY, LanguageCategory.DISEASE, LanguageCategory.CATASTROPHE}
    )


def test_inferred_past_window_hedges_and_invites_confirmation():
    policy = resolve_policy(TemporalDirection.PAST, EventSource.SYSTEM_INFERRED)
    assert policy.voice is Voice.RETRODICTIVE
    assert not policy.may_name_specific_event
    assert policy.requires_invitation_to_confirm


def test_disclosed_past_event_may_be_named_plainly():
    policy = resolve_policy(TemporalDirection.PAST, EventSource.USER_DISCLOSED)
    assert policy.may_name_specific_event
    assert not policy.requires_invitation_to_confirm
    assert policy.prohibited_categories == frozenset()
    # Still never a longevity calculation, even about the past, for the living.
    assert not policy.longevity_formula_allowed


def test_present_window_is_advisory_but_never_names_disease():
    policy = resolve_policy(TemporalDirection.PRESENT)
    assert policy.voice is Voice.ADVISORY
    assert not policy.permits(LanguageCategory.DISEASE)
    assert not policy.permits(LanguageCategory.MORTALITY)


@pytest.mark.parametrize("direction", list(TemporalDirection))
def test_longevity_formula_never_runs_for_the_living(direction):
    policy = resolve_policy(direction, subject_status=SubjectStatus.LIVING)
    assert not policy.longevity_formula_allowed


@pytest.mark.parametrize("direction", list(TemporalDirection))
def test_historical_backtesting_mode_is_unrestricted(direction):
    policy = resolve_policy(direction, subject_status=SubjectStatus.DECEASED_HISTORICAL)
    assert policy.longevity_formula_allowed
    assert policy.may_name_specific_event
    assert policy.prohibited_categories == frozenset()


def test_confidence_qualifier_is_required_in_every_configuration():
    for direction in TemporalDirection:
        for source in EventSource:
            for status in SubjectStatus:
                assert resolve_policy(direction, source, status).requires_confidence_qualifier


def test_policy_for_moment_composes_classification_and_resolution():
    policy = policy_for_moment(NOW - timedelta(days=400), NOW)
    assert policy.direction is TemporalDirection.PAST
    assert policy.voice is Voice.RETRODICTIVE


# ── Vocabulary scanner ────────────────────────────────────────────────────────


def test_scanner_flags_prohibited_terms_in_a_forecast():
    policy = resolve_policy(TemporalDirection.FUTURE)
    violations = scan_text("This period brings a risk of a heart attack.", policy, field_name="story")
    assert [v.category for v in violations] == [LanguageCategory.DISEASE]
    assert violations[0].term.lower() == "heart attack"
    assert violations[0].field_name == "story"


def test_scanner_permits_domain_level_language():
    policy = resolve_policy(TemporalDirection.FUTURE)
    text = "Indicators converge on health and family matters; treat this as a period to be careful in."
    assert scan_text(text, policy) == []


def test_scanner_is_silent_where_the_policy_permits():
    policy = resolve_policy(TemporalDirection.PAST, EventSource.USER_DISCLOSED)
    assert scan_text("the bereavement you described in 2003", policy) == []


def test_scanner_does_not_match_substrings():
    policy = resolve_policy(TemporalDirection.FUTURE)
    # "diesel" contains "dies"; word boundaries must prevent a false positive.
    assert scan_text("Fuel and diesel costs may rise.", policy) == []


def test_assert_compliant_raises_with_all_offending_fields():
    policy = resolve_policy(TemporalDirection.FUTURE)
    with pytest.raises(StancePolicyViolation) as excinfo:
        assert_compliant({"a": "risk of stroke", "b": "an accident is likely"}, policy)
    assert len(excinfo.value.violations) == 2


def test_redact_replaces_terms_with_domain_level_standins():
    policy = resolve_policy(TemporalDirection.FUTURE)
    out = redact("Risk of cancer this year.", policy)
    assert "cancer" not in out.lower()
    assert "a health matter" in out


# ── Disclosed events ──────────────────────────────────────────────────────────


def _event(**overrides) -> DisclosedEvent:
    defaults = dict(
        event_id="e1",
        domain=LifeDomain.HEALTH,
        occurred_start_utc=datetime(2003, 6, 1, tzinfo=timezone.utc),
        occurred_end_utc=datetime(2003, 8, 31, tzinfo=timezone.utc),
        description="a long hospital stay",
    )
    defaults.update(overrides)
    return DisclosedEvent(**defaults)


def test_event_rejects_inverted_range():
    with pytest.raises(ValueError):
        _event(occurred_end_utc=datetime(2002, 1, 1, tzinfo=timezone.utc))


def test_event_rejects_out_of_range_significance():
    with pytest.raises(ValueError):
        _event(significance=9)


def test_point_in_time_event_is_detected():
    assert _event(occurred_end_utc=None).is_point_in_time


def test_match_requires_domain_alignment_for_confirmation():
    event = _event()
    # 'janma' covers health; 'karma' does not.
    health = match_events([event], datetime(2003, 7, 1, tzinfo=timezone.utc),
                          datetime(2003, 7, 10, tzinfo=timezone.utc), sangya_keys=["janma"])
    career = match_events([event], datetime(2003, 7, 1, tzinfo=timezone.utc),
                          datetime(2003, 7, 10, tzinfo=timezone.utc), sangya_keys=["karma"])

    assert health[0].is_confirmation
    assert health[0].matched_sangyas == ("janma",)
    # Overlapping in time is not enough — the window must point at the same area.
    assert not career[0].is_confirmation


def test_point_event_inside_window_reports_a_full_day_of_overlap():
    event = _event(occurred_end_utc=None, occurred_start_utc=datetime(2003, 7, 5, tzinfo=timezone.utc))
    matches = match_events([event], datetime(2003, 7, 5, tzinfo=timezone.utc),
                           datetime(2003, 7, 5, tzinfo=timezone.utc), sangya_keys=["janma"])
    assert matches[0].overlap_days == 1.0


def test_non_overlapping_event_is_not_matched():
    assert match_events([_event()], datetime(2010, 1, 1, tzinfo=timezone.utc),
                        datetime(2010, 2, 1, tzinfo=timezone.utc), sangya_keys=["janma"]) == []


def test_matches_are_returned_strongest_first():
    weak = _event(event_id="weak", domain=LifeDomain.CAREER, significance=1)
    strong = _event(event_id="strong", domain=LifeDomain.HEALTH, significance=5)
    matches = match_events([weak, strong], datetime(2003, 7, 1, tzinfo=timezone.utc),
                           datetime(2003, 7, 10, tzinfo=timezone.utc), sangya_keys=["janma"])
    assert matches[0].event.event_id == "strong"


def test_domains_for_sangyas_unions_and_ignores_unknown_keys():
    domains = domains_for_sangyas(["janma", "karma", "not_a_sangya"])
    assert LifeDomain.HEALTH in domains
    assert LifeDomain.CAREER in domains


# ── Severity tiers ────────────────────────────────────────────────────────────


def test_severity_tier_grades_by_convergence():
    assert severity_tier([]) is SeverityTier.NONE
    assert severity_tier(["karma"]) is SeverityTier.SINGLE
    assert severity_tier(["karma", "desha"]) is SeverityTier.CONVERGING
    assert severity_tier(["karma", "desha", "manasa", "jati"]) is SeverityTier.STRONG_CONVERGENCE


def test_janma_affliction_is_weighted_above_other_points():
    # Janma alone outranks any other single point, per the classical note that
    # damage to Karma is read as less severe than damage to Janma itself.
    assert severity_tier(["janma"]) is SeverityTier.CONVERGING
    assert severity_tier(["karma"]) is SeverityTier.SINGLE


def test_severity_tier_deduplicates_and_normalises_keys():
    assert severity_tier([" Karma ", "karma"]) is SeverityTier.SINGLE


# ── Window grouping ───────────────────────────────────────────────────────────


def _hit(offset_days: float, afflicted: tuple[str, ...] = ("karma",), matches=()) -> SBCScanHit:
    moment = NOW + timedelta(days=offset_days)
    direction = classify_direction(moment, NOW)
    return SBCScanHit(
        moment_utc=moment,
        report=None,  # grouping never touches the report
        temporal_direction=direction,
        policy=resolve_policy(direction),
        tier=severity_tier(afflicted),
        afflicted_sangyas=afflicted,
        event_matches=list(matches),
    )


def test_grouping_splits_on_gaps_larger_than_the_threshold():
    hits = [_hit(-100), _hit(-99), _hit(-98), _hit(-50), _hit(-49)]
    windows = group_into_windows(hits, max_gap_days=3.0)
    assert [len(w.hits) for w in windows] == [3, 2]
    assert windows[0].duration_days == pytest.approx(2.0)


def test_empty_scan_produces_no_windows():
    assert group_into_windows([]) == []


def test_window_carries_the_strongest_tier_it_contains():
    hits = [_hit(-100, ("karma",)), _hit(-99, ("karma", "desha", "manasa", "jati"))]
    window = group_into_windows(hits)[0]
    assert window.tier is SeverityTier.STRONG_CONVERGENCE


def test_window_unions_afflicted_points_preserving_order():
    hits = [_hit(-100, ("karma",)), _hit(-99, ("desha", "karma"))]
    assert group_into_windows(hits)[0].afflicted_sangyas == ("karma", "desha")


def test_window_spanning_past_into_present_takes_the_stricter_stance():
    """A stretch still running is not licensed to speak in past-tense certainties."""
    window = group_into_windows([_hit(-9), _hit(-6)], max_gap_days=5.0)[0]
    assert window.temporal_direction is TemporalDirection.PRESENT
    assert window.policy.voice is Voice.ADVISORY


def test_window_wholly_in_the_past_is_retrodictive():
    window = group_into_windows([_hit(-100), _hit(-99)])[0]
    assert window.temporal_direction is TemporalDirection.PAST
    assert window.policy.voice is Voice.RETRODICTIVE


def test_window_deduplicates_repeated_event_matches():
    match = match_events(
        [_event()],
        datetime(2003, 7, 1, tzinfo=timezone.utc),
        datetime(2003, 7, 1, tzinfo=timezone.utc),
        sangya_keys=["janma"],
    )
    hits = [_hit(-100, ("janma",), match), _hit(-99, ("janma",), match)]
    window = group_into_windows(hits)[0]
    assert len(window.event_matches) == 1
    assert window.is_confirmed_by_disclosure
    # A confirmed window may name the event it lines up with.
    assert window.policy.may_name_specific_event


def test_grouping_rejects_a_negative_gap():
    with pytest.raises(ValueError):
        group_into_windows([_hit(-1)], max_gap_days=-1.0)


# ── Analyzer integration ──────────────────────────────────────────────────────


def _sangyas(afflicted: list[str]) -> list[dict]:
    return [
        {
            "key": key,
            "status": "afflicted",
            "nakshatra_name": "Rohini",
            "vedhas_received": ["Saturn (Right)"],
            "benefic_hits": [],
            "malefic_hits": ["Saturn"],
        }
        for key in afflicted
    ]


def test_past_window_uses_retrodictive_voice_and_invites_confirmation():
    resp = SBCAIAnalyzer.analyze(
        AISBCAnalysisRequest(
            reference_nakshatra="rohini",
            transit_date=datetime(2003, 7, 1, tzinfo=timezone.utc),
            now_utc=NOW,
            event_type="life_events",
            active_sangyas=_sangyas(["janma", "jati"]),
        )
    )
    assert resp.temporal_direction == "past"
    assert resp.voice == "retrodictive"
    assert resp.event_type == "retrodiction"
    assert not resp.confirmed_by_disclosure
    assert resp.confirmation_invitation
    # An inferred retrodiction must not hand the native a guessed event.
    assert resp.policy_redactions == []


def test_disclosed_event_unlocks_naming_and_drops_the_invitation():
    resp = SBCAIAnalyzer.analyze(
        AISBCAnalysisRequest(
            reference_nakshatra="rohini",
            transit_date=datetime(2003, 7, 1, tzinfo=timezone.utc),
            now_utc=NOW,
            event_type="life_events",
            active_sangyas=_sangyas(["janma"]),
            disclosed_events=[
                DisclosedEventInput(
                    event_id="e1",
                    domain="health",
                    occurred_start_utc=datetime(2003, 6, 1, tzinfo=timezone.utc),
                    occurred_end_utc=datetime(2003, 8, 31, tzinfo=timezone.utc),
                    description="a long hospital stay",
                )
            ],
        )
    )
    assert resp.confirmed_by_disclosure
    assert resp.confirmation_invitation == ""
    assert "a long hospital stay" in resp.the_story


def test_disclosed_event_in_an_unrelated_domain_does_not_unlock_naming():
    resp = SBCAIAnalyzer.analyze(
        AISBCAnalysisRequest(
            reference_nakshatra="rohini",
            transit_date=datetime(2003, 7, 1, tzinfo=timezone.utc),
            now_utc=NOW,
            event_type="life_events",
            active_sangyas=_sangyas(["janma"]),  # health/mental — not career
            disclosed_events=[
                DisclosedEventInput(
                    event_id="e1",
                    domain="career",
                    occurred_start_utc=datetime(2003, 6, 1, tzinfo=timezone.utc),
                    occurred_end_utc=datetime(2003, 8, 31, tzinfo=timezone.utc),
                    description="a promotion",
                )
            ],
        )
    )
    assert not resp.confirmed_by_disclosure
    assert resp.confirmation_invitation


def test_future_window_keeps_advisory_templates_and_marks_direction():
    resp = SBCAIAnalyzer.analyze(
        AISBCAnalysisRequest(
            reference_nakshatra="rohini",
            transit_date=NOW + timedelta(days=200),
            now_utc=NOW,
            event_type="market",
            active_sangyas=_sangyas(["sanghatika", "vainashika"]),
        )
    )
    assert resp.temporal_direction == "future"
    assert resp.voice == "prospective"
    assert resp.event_type == "market"


@pytest.mark.parametrize(
    "event_type,keys",
    [
        ("market", ["sanghatika", "vainashika"]),
        ("life_events", ["janma", "jati", "manasa"]),
        ("muhurta", ["karma", "abhisheka"]),
        ("general", ["janma", "karma", "desha"]),
    ],
)
@pytest.mark.parametrize("offset_days", [-4000, 0, 4000])
def test_no_template_emits_prohibited_vocabulary_in_any_direction(event_type, keys, offset_days):
    """Regression guard over the authored templates themselves.

    Every branch of the analyzer, in every temporal direction, must already
    comply with its own policy — ``policy_redactions`` is a bug signal, so it
    staying empty is the assertion.
    """
    resp = SBCAIAnalyzer.analyze(
        AISBCAnalysisRequest(
            reference_nakshatra="rohini",
            transit_date=NOW + timedelta(days=offset_days),
            now_utc=NOW,
            event_type=event_type,
            active_sangyas=_sangyas(keys),
        )
    )
    assert resp.policy_redactions == []


def test_runtime_redaction_records_the_violation_rather_than_hiding_it():
    policy = resolve_policy(TemporalDirection.FUTURE)
    resp = SBCAIAnalyzer.analyze(
        AISBCAnalysisRequest(
            reference_nakshatra="rohini",
            transit_date=NOW + timedelta(days=200),
            now_utc=NOW,
            event_type="general",
            active_sangyas=_sangyas(["janma"]),
        )
    )
    resp.the_story = "There is a risk of cancer here."
    patched = SBCAIAnalyzer._apply_policy(resp, policy, [])
    assert patched.policy_redactions
    assert "cancer" not in patched.the_story.lower()
