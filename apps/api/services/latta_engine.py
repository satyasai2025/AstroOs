"""
AstroOS — Latta Dosha engine

Computes, at a moment, which transiting grahas are kicking the native's
Janma Nakshatra (see :mod:`packages.shared.latta` for the mechanism and
— importantly — its sourcing tier).

Two things this engine does that the pure module deliberately does not:

1. **Resolves transiting positions** from the ephemeris, the same way
   ``tarabala_report_service`` does, so Latta converges with the Tara
   and SBC machinery on identical inputs rather than a second opinion
   about where the planets are.
2. **Attaches a temporal-stance policy.** Latta's classical predictive
   wording is the bluntest in this whole area of the tradition — the
   source text names specific deaths and specific losses. Nothing in
   this codebase reproduces that, and the policy object attached to
   every report is what makes the restriction structural rather than a
   matter of whoever writes the next template remembering it. The
   engine emits life *domains* and a severity grade; it emits no prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
)
from packages.shared.disclosed_events import DisclosedEvent, EventMatch, LifeDomain, match_events
from packages.shared.latta import (
    LATTA_RULES,
    LattaHit,
    NAMED_COMBINATIONS_STATUS,
    VerificationStatus,
    afflicted_domains,
    check_latta,
)
from packages.shared.temporal_stance import (
    DEFAULT_PRESENT_WINDOW_DAYS,
    EventSource,
    StancePolicy,
    SubjectStatus,
    classify_direction,
    resolve_policy,
)

#: Grahas carrying a Latta rule. Ketu is absent from the classical list, so it
#: is absent here — see packages/shared/latta.py.
LATTA_PLANETS: tuple[str, ...] = tuple(LATTA_RULES)


@dataclass
class LattaReport:
    janma_nakshatra: str
    moment_utc: datetime
    hits: list[LattaHit]
    #: Where each Latta-carrying graha currently stands.
    transit_nakshatras: dict[str, str]
    domains_struck: frozenset[LifeDomain]
    policy: StancePolicy
    event_matches: list[EventMatch] = field(default_factory=list)
    #: Surfaced so a caller can state the tier rather than imply verification.
    verification: VerificationStatus = VerificationStatus.STANDARD_UNVERIFIED
    named_combinations_status: dict = field(default_factory=lambda: dict(NAMED_COMBINATIONS_STATUS))

    @property
    def severe_hits(self) -> list[LattaHit]:
        """Malefic grahas kicking forward — the heavier reading."""
        return [h for h in self.hits if h.is_severe]

    @property
    def is_afflicted(self) -> bool:
        return bool(self.hits)

    @property
    def is_confirmed_by_disclosure(self) -> bool:
        return any(m.is_confirmation for m in self.event_matches)


class LattaEngine:
    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    def _nakshatra_of(self, planet: str, jd: float) -> str:
        tropical = self._wrapper.get_planet_position(planet, jd)
        ayanamsa_val = self._wrapper.get_ayanamsa(jd)
        sidereal_lon = self._wrapper.to_sidereal(tropical.longitude, ayanamsa_val)
        return longitude_to_nakshatra(sidereal_lon).nakshatra

    def build_report(
        self,
        janma_nakshatra: str,
        moment_utc: datetime,
        now_utc: Optional[datetime] = None,
        disclosed_events: Optional[list[DisclosedEvent]] = None,
        subject_status: SubjectStatus = SubjectStatus.LIVING,
        present_window_days: int = DEFAULT_PRESENT_WINDOW_DAYS,
    ) -> LattaReport:
        jd = datetime_to_jd(moment_utc)
        transit_nakshatras = {planet: self._nakshatra_of(planet, jd) for planet in LATTA_PLANETS}

        hits = check_latta(janma_nakshatra, transit_nakshatras)
        domains = afflicted_domains(hits)

        events = list(disclosed_events or ())
        matches = (
            match_events_by_domain(events, moment_utc, domains, tolerance_days=15.0)
            if events and domains
            else []
        )

        source = (
            EventSource.USER_DISCLOSED
            if any(m.is_confirmation for m in matches)
            else EventSource.SYSTEM_INFERRED
        )
        direction = classify_direction(moment_utc, now_utc or datetime.now(timezone.utc), present_window_days)

        return LattaReport(
            janma_nakshatra=janma_nakshatra.strip().lower(),
            moment_utc=moment_utc,
            hits=hits,
            transit_nakshatras=transit_nakshatras,
            domains_struck=domains,
            policy=resolve_policy(direction, source, subject_status),
            event_matches=matches,
        )


def match_events_by_domain(
    events: list[DisclosedEvent],
    moment_utc: datetime,
    domains: frozenset[LifeDomain],
    tolerance_days: float = 0.0,
) -> list[EventMatch]:
    """Match disclosed events to a Latta moment by life domain.

    ``disclosed_events.match_events`` keys domain alignment off Sangya keys,
    which Latta does not have — it produces domains directly. This wrapper
    performs the same overlap computation and then rewrites ``domain_matches``
    against the struck domains, so a career event cannot confirm a Latta that
    only strikes health.
    """
    raw = match_events(events, moment_utc, moment_utc, tolerance_days=tolerance_days)
    rescored = [
        EventMatch(
            event=m.event,
            overlap_days=m.overlap_days,
            domain_matches=m.event.domain in domains,
            matched_sangyas=(),
        )
        for m in raw
    ]
    rescored.sort(key=lambda m: (m.domain_matches, m.event.significance, m.overlap_days), reverse=True)
    return rescored
