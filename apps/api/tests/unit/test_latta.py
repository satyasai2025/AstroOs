"""
Unit tests — Latta Dosha mechanism, sourcing tier, and policy wiring.

Two things these lock down beyond the arithmetic: that the unsourced
named-combination table stays empty rather than quietly acquiring
invented values, and that a Latta report always carries a temporal
stance policy — this technique's classical wording is the bluntest in
the area and the restriction has to be structural.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.services.latta_engine import LATTA_PLANETS, LattaEngine, match_events_by_domain
from packages.shared.disclosed_events import DisclosedEvent, LifeDomain
from packages.shared.enums import Nakshatra
from packages.shared.latta import (
    LATTA_RULES,
    NAMED_COMBINATIONS,
    NAMED_COMBINATIONS_STATUS,
    LattaDirection,
    VerificationStatus,
    afflicted_domains,
    check_latta,
    latta_target,
)
from packages.shared.temporal_stance import (
    EventSource,
    SubjectStatus,
    TemporalDirection,
    Voice,
)

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
ALL_27 = [n.value for n in Nakshatra]


# ── Offset arithmetic ─────────────────────────────────────────────────────────


def test_offsets_count_inclusively():
    """The Sun's 12th-star Latta lands eleven positions on, not twelve."""
    # ashwini is index 0; the 12th star counted inclusively is index 11.
    assert latta_target("sun", "ashwini") == ALL_27[11] == "uttara_phalguni"


def test_backward_latta_counts_against_the_zodiac():
    # Venus kicks the 5th backward: from index 10, inclusively, to index 6.
    assert latta_target("venus", "purva_phalguni") == ALL_27[6] == "punarvasu"


def test_forward_latta_wraps_around_the_end_of_the_circle():
    assert latta_target("saturn", "revati") == ALL_27[6]  # 26 + 7 = 33 -> 6


def test_backward_latta_wraps_around_the_start_of_the_circle():
    assert latta_target("rahu", "ashwini") == ALL_27[19]  # 0 - 8 -> 19


@pytest.mark.parametrize("planet", sorted(LATTA_RULES))
@pytest.mark.parametrize("nakshatra", ALL_27)
def test_every_target_is_a_valid_nakshatra(planet, nakshatra):
    assert latta_target(planet, nakshatra) in ALL_27


@pytest.mark.parametrize("planet", sorted(LATTA_RULES))
def test_each_planet_strikes_every_star_exactly_once_across_the_circle(planet):
    """A fixed offset is a bijection on the 27-star circle — a table typo
    (duplicate or out-of-range offset) would break this."""
    targets = {latta_target(planet, n) for n in ALL_27}
    assert len(targets) == 27


def test_unknown_planet_is_an_error_not_a_silent_miss():
    with pytest.raises(KeyError):
        latta_target("pluto", "ashwini")


def test_unknown_nakshatra_is_an_error():
    with pytest.raises(ValueError):
        latta_target("sun", "abhijit")  # 28-system token; Latta uses the 27-system


def test_planet_and_nakshatra_tokens_are_case_and_space_tolerant():
    assert latta_target(" Sun ", " Ashwini ") == latta_target("sun", "ashwini")


# ── Rule table integrity ──────────────────────────────────────────────────────


def test_ketu_carries_no_latta():
    """Its absence is the sourced position, not a gap."""
    assert "ketu" not in LATTA_RULES
    assert "ketu" not in LATTA_PLANETS


def test_all_eight_latta_grahas_are_present():
    assert set(LATTA_RULES) == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu",
    }


def test_malefics_are_flagged_as_such():
    malefics = {p for p, r in LATTA_RULES.items() if r.is_malefic}
    assert malefics == {"sun", "mars", "saturn", "rahu"}


def test_every_rule_declares_its_sourcing_tier_honestly():
    """No rule may claim verification the repo cannot back up."""
    for rule in LATTA_RULES.values():
        assert rule.verification is VerificationStatus.STANDARD_UNVERIFIED


def test_every_rule_carries_at_least_one_life_domain():
    for rule in LATTA_RULES.values():
        assert rule.domains


def test_rule_rejects_a_non_inclusive_offset():
    from packages.shared.latta import LattaRule

    with pytest.raises(ValueError):
        LattaRule(
            planet="test",
            offset=0,
            direction=LattaDirection.FORWARD,
            domains=frozenset({LifeDomain.OTHER}),
            is_malefic=False,
        )


def test_named_combinations_remain_unsourced_and_empty():
    """Guards the sourcing discipline itself.

    If someone later fills this table in, they must also move its status off
    NEEDS_SOURCE — which is exactly the review conversation that should happen.
    """
    assert NAMED_COMBINATIONS == {}
    assert NAMED_COMBINATIONS_STATUS["status"] is VerificationStatus.NEEDS_SOURCE
    assert len(NAMED_COMBINATIONS_STATUS["names"]) == 7
    assert "Phaladeepika" in NAMED_COMBINATIONS_STATUS["blocked_on"]


# ── Hit detection ─────────────────────────────────────────────────────────────


def test_check_latta_finds_the_kicking_planet():
    # Sun in ashwini strikes uttara_phalguni.
    hits = check_latta("uttara_phalguni", {"sun": "ashwini", "moon": "revati"})
    assert [h.planet for h in hits] == ["sun"]
    assert hits[0].from_nakshatra == "ashwini"
    assert hits[0].struck_nakshatra == "uttara_phalguni"


def test_check_latta_returns_nothing_when_no_planet_kicks_the_star():
    assert check_latta("ashwini", {"sun": "ashwini"}) == []


def test_planets_without_a_rule_are_skipped_not_rejected():
    """A caller passing a full graha set including Ketu is normal."""
    hits = check_latta("uttara_phalguni", {"sun": "ashwini", "ketu": "ashwini"})
    assert [h.planet for h in hits] == ["sun"]


def test_severe_hits_are_malefic_and_forward():
    hits = check_latta("uttara_phalguni", {"sun": "ashwini"})
    assert hits[0].is_severe

    # Venus is benefic and kicks backward — never severe.
    venus_hits = check_latta(latta_target("venus", "purva_phalguni"), {"venus": "purva_phalguni"})
    assert not venus_hits[0].is_severe


def test_hits_are_ordered_severe_first():
    star = latta_target("saturn", "ashwini")
    kickers = {"saturn": "ashwini"}
    for planet in ("jupiter", "venus", "mercury", "moon"):
        # Find a position from which this planet strikes the same star.
        for n in ALL_27:
            if latta_target(planet, n) == star:
                kickers[planet] = n
                break

    hits = check_latta(star, kickers)
    assert hits[0].planet == "saturn"
    assert hits[0].is_severe
    assert not hits[-1].is_severe


def test_check_latta_rejects_an_unknown_target():
    with pytest.raises(ValueError):
        check_latta("abhijit", {"sun": "ashwini"})


def test_afflicted_domains_unions_across_hits():
    star = latta_target("saturn", "ashwini")
    domains = afflicted_domains(check_latta(star, {"saturn": "ashwini"}))
    assert LifeDomain.HEALTH in domains
    assert LifeDomain.CAREER in domains
    assert afflicted_domains([]) == frozenset()


# ── Domain-aware event matching ───────────────────────────────────────────────


def _event(domain: LifeDomain, event_id: str = "e1") -> DisclosedEvent:
    return DisclosedEvent(
        event_id=event_id,
        domain=domain,
        occurred_start_utc=datetime(2003, 7, 1, tzinfo=timezone.utc),
        description="something that happened",
    )


def test_event_confirms_only_when_its_domain_was_struck():
    moment = datetime(2003, 7, 1, tzinfo=timezone.utc)
    struck = frozenset({LifeDomain.HEALTH})

    health = match_events_by_domain([_event(LifeDomain.HEALTH)], moment, struck)
    career = match_events_by_domain([_event(LifeDomain.CAREER)], moment, struck)

    assert health[0].is_confirmation
    assert not career[0].is_confirmation


def test_domain_matched_events_sort_ahead_of_merely_overlapping_ones():
    moment = datetime(2003, 7, 1, tzinfo=timezone.utc)
    matches = match_events_by_domain(
        [_event(LifeDomain.CAREER, "career"), _event(LifeDomain.HEALTH, "health")],
        moment,
        frozenset({LifeDomain.HEALTH}),
    )
    assert matches[0].event.event_id == "health"


# ── Engine wiring ─────────────────────────────────────────────────────────────


class _StubWrapper:
    """Places every graha at a chosen longitude; enough for policy wiring tests."""

    def __init__(self, longitude: float = 0.0) -> None:
        self.longitude = longitude

    def get_planet_position(self, planet, jd):
        return type("P", (), {"longitude": self.longitude})()

    def get_ayanamsa(self, jd):
        return 0.0

    def to_sidereal(self, longitude, ayanamsa):
        return longitude - ayanamsa


def test_report_carries_a_policy_matching_its_temporal_direction():
    engine = LattaEngine(_StubWrapper())
    report = engine.build_report("uttara_phalguni", NOW - timedelta(days=4000), now_utc=NOW)

    assert report.policy.direction is TemporalDirection.PAST
    assert report.policy.voice is Voice.RETRODICTIVE
    assert report.policy.requires_confidence_qualifier


def test_future_report_may_not_name_a_specific_event():
    engine = LattaEngine(_StubWrapper())
    report = engine.build_report("uttara_phalguni", NOW + timedelta(days=400), now_utc=NOW)

    assert report.policy.direction is TemporalDirection.FUTURE
    assert not report.policy.may_name_specific_event


def test_report_surfaces_its_sourcing_tier():
    engine = LattaEngine(_StubWrapper())
    report = engine.build_report("ashwini", NOW, now_utc=NOW)

    assert report.verification is VerificationStatus.STANDARD_UNVERIFIED
    assert report.named_combinations_status["status"] is VerificationStatus.NEEDS_SOURCE


def test_all_grahas_at_ashwini_strike_ashwini_s_latta_targets():
    """Every Latta graha sitting at 0° places them all in ashwini, so the
    star each one kicks from there must show up as a hit for that star."""
    engine = LattaEngine(_StubWrapper(longitude=0.0))
    report = engine.build_report(latta_target("sun", "ashwini"), NOW, now_utc=NOW)

    assert set(report.transit_nakshatras.values()) == {"ashwini"}
    assert "sun" in {h.planet for h in report.hits}
    assert report.is_afflicted


def test_disclosed_event_in_a_struck_domain_flips_the_source_to_user_disclosed():
    engine = LattaEngine(_StubWrapper(longitude=0.0))
    moment = datetime(2003, 7, 1, tzinfo=timezone.utc)
    struck_star = latta_target("sun", "ashwini")

    report = engine.build_report(
        struck_star,
        moment,
        now_utc=NOW,
        disclosed_events=[_event(LifeDomain.HEALTH)],
    )

    assert LifeDomain.HEALTH in report.domains_struck
    assert report.is_confirmed_by_disclosure
    assert report.policy.event_source is EventSource.USER_DISCLOSED
    assert report.policy.may_name_specific_event


def test_longevity_formula_stays_blocked_for_a_living_subject():
    engine = LattaEngine(_StubWrapper())
    report = engine.build_report(
        "ashwini", NOW - timedelta(days=4000), now_utc=NOW, subject_status=SubjectStatus.LIVING
    )
    assert not report.policy.longevity_formula_allowed


# ── Router ────────────────────────────────────────────────────────────────────


@pytest.fixture
def client() -> TestClient:
    from apps.api.dependencies import get_ephemeris_wrapper
    from apps.api.routers import latta as latta_router

    app = FastAPI()
    app.include_router(latta_router.router, prefix="/api/v1")
    app.dependency_overrides[get_ephemeris_wrapper] = lambda: _StubWrapper(longitude=0.0)
    return TestClient(app)


def test_report_endpoint_returns_domains_and_policy(client: TestClient):
    res = client.post(
        "/api/v1/latta/report",
        json={
            "janma_nakshatra": latta_target("sun", "ashwini"),
            "moment_utc": "2026-01-15T12:00:00+00:00",
            "now_utc": "2026-08-27T12:00:00+00:00",
        },
    )
    assert res.status_code == 200
    body = res.json()

    assert body["is_afflicted"]
    assert "sun" in {h["planet"] for h in body["hits"]}
    assert body["domains_struck"]
    assert body["policy"]["direction"] == "past"
    assert body["policy"]["requires_confidence_qualifier"]


def test_report_endpoint_surfaces_the_unsourced_table_rather_than_hiding_it(client: TestClient):
    res = client.post("/api/v1/latta/report", json={"janma_nakshatra": "ashwini"})
    assert res.status_code == 200
    body = res.json()

    assert body["verification"] == "standard_unverified"
    assert body["named_combinations_status"]["status"] == "needs_source"
    assert len(body["named_combinations_status"]["names"]) == 7


def test_report_endpoint_rejects_an_unknown_nakshatra(client: TestClient):
    res = client.post("/api/v1/latta/report", json={"janma_nakshatra": "abhijit"})
    # Latta is reckoned on the 27-star circle, so a 28-system token is a
    # category error the schema rejects rather than an engine crash.
    assert res.status_code == 422


def test_report_endpoint_accepts_disclosed_events(client: TestClient):
    res = client.post(
        "/api/v1/latta/report",
        json={
            "janma_nakshatra": latta_target("sun", "ashwini"),
            "moment_utc": "2003-07-01T12:00:00+00:00",
            "now_utc": "2026-08-27T12:00:00+00:00",
            "disclosed_events": [
                {
                    "event_id": "e1",
                    "domain": "health",
                    "occurred_start_utc": "2003-06-01T00:00:00+00:00",
                    "occurred_end_utc": "2003-08-31T00:00:00+00:00",
                    "description": "a long hospital stay",
                }
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()

    assert body["confirmed_by_disclosure"]
    assert body["policy"]["may_name_specific_event"]
