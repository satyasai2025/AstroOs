"""
AstroOS — Event Engine (Module 14, Phase 1 + Phase 2)

An assembly and correlation layer, not a calculation engine in the
sense Yoga/Shadbala/Ashtakavarga/Transit are — closer in spirit to
FactBuilder (Module 13). EventEngine calls existing engines and one
new pure lookup (dasha_lookup.find_active_dasha_chain) and never
duplicates any astrology calculation itself.

Per the approved Module 14 Design Audit:
  - Yoga, Shadbala, and Ashtakavarga are natal-chart-level and
    date-invariant. They are never recomputed here — EventEngine takes
    an already-built NatalSnapshot (one per chart, shared across every
    event for that chart) rather than calling YogaEngine/
    ShadbalaEngine/AshtakavargaEngine itself. This is what structurally
    prevents the single most likely accidental-duplication bug this
    design guards against.
  - Dasha and Transit ARE date-dependent. Active Dasha periods are
    resolved via the new dasha_lookup primitive over already-computed
    DashaTrees (never recomputed); Transit is delegated to
    TransitEngine.compute_transit(), which already accepts an
    arbitrary moment — no change needed there either.
  - If a RuleEngine is available, its RuleResults are consumed as-is
    and simply attached to EventAnalysis — EventEngine never
    re-implements rule-matching logic.

Phase 2 adds `analyze_batch()` — analyzing many EventRecords for one
chart efficiently, reusing one NatalSnapshot across all of them. No new
domain model was needed for this (per the Phase 2 Design Audit): a
`BatchAnalysisResult` operation-result container lives in this service
module, not domain/events.py, since it describes a batch call's
outcome, not a first-class Event Engine concept. FactRegistry (Module
13, complete) is left unmodified, same as Phase 1's own `dasha.*` fork
decision.

Not wired into any router or persistence layer — same scope discipline
as every engine before it (Yoga, Shadbala, Ashtakavarga, Transit, Rule
Engine, each at their own Phase 1).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from typing import Optional, Protocol

from apps.api.domain.dasha import DashaTree
from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord, NatalSnapshot
from apps.api.domain.facts import Fact
from apps.api.domain.rules import RuleResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.fact_registry import FactRegistry


@dataclass(frozen=True)
class BatchAnalysisResult:
    """
    Lightweight outcome of EventEngine.analyze_batch() (Phase 2). Not a
    domain model — an operation-result container, same spirit as a
    function returning a small summary tuple, just named and typed.

    `analyses` holds only the EventAnalysis objects produced for events
    that succeeded, in input order (skipping failures, not padding them
    with None) — a plain `tuple[EventAnalysis, ...]`, consistent with
    how YogaEngine.evaluate_all() returns a plain list rather than a
    wrapper type for its own per-item results.

    `successful` and `failed` are counts (int), not lists of ids — kept
    deliberately lightweight per the approved Phase 2 scope. A caller
    needing to know WHICH specific events failed is a slightly larger
    ask than what was specified here; flagged in the Phase 2 docs as a
    follow-up if that turns out to be needed.
    """

    analyses: tuple[EventAnalysis, ...]
    total_events: int
    successful: int
    failed: int


class _TransitEngineProtocol(Protocol):
    """
    Structural shape EventEngine needs from a TransitEngine — avoids a
    hard import dependency on the concrete TransitEngine class (which
    itself needs an EphemerisWrapper) purely for type-checking
    purposes. Any object with this method (the real TransitEngine, or a
    test double) works.
    """

    def compute_transit(
        self, natal_chart, transit_datetime_utc: datetime
    ) -> list[TransitPlanetResult]: ...


class _RuleEngineProtocol(Protocol):
    """Structural shape EventEngine needs from a RuleEngine."""

    def evaluate_all(self, facts: FactRegistry) -> list[RuleResult]: ...


class EventEngine:
    """
    Constructed with an optional TransitEngine (context/facts degrade
    gracefully if absent — same optional-dependency pattern as
    FactBuilder, ShadbalaEngine, etc.) and an optional RuleEngine
    (rule_results is None, not an empty tuple, if absent).

    Deliberately does NOT take a DashaEngine/YogaEngine/ShadbalaEngine/
    AshtakavargaEngine directly — see module docstring and the Design
    Audit §5 for why: those engines' OUTPUTS (already-computed
    DashaTrees, and a NatalSnapshot) are passed into this engine's
    methods instead, so the "compute once per chart, reuse across
    every event" rule is a structural guarantee, not caller discipline.
    """

    _CONTEXT_VERSION = "1.0"
    _ANALYSIS_VERSION = "1.0"

    def __init__(
        self,
        transit_engine: Optional[_TransitEngineProtocol] = None,
        rule_engine: Optional[_RuleEngineProtocol] = None,
    ) -> None:
        self._transit_engine = transit_engine
        self._rule_engine = rule_engine

    def build_context(
        self,
        event: EventRecord,
        dasha_trees: dict[str, DashaTree],
        natal_snapshot: NatalSnapshot,
    ) -> EventAstrologicalContext:
        """
        Assembles one EventAstrologicalContext for `event`.

        `dasha_trees` must be already-computed DashaTree objects (any
        subset of the six systems DashaEngine supports — a caller may
        not always have computed all six); each is looked up by
        `event.event_date` via the pure dasha_lookup primitive, never
        recomputed here.

        Raises ValueError if `natal_snapshot.chart_id != event.chart_id`
        — a defensive guard against assembling a context from the
        wrong chart's natal data, since NatalSnapshot is normally
        reused across many events and a caller mismatch here would
        otherwise silently produce a wrong-chart context.
        """
        if natal_snapshot.chart_id != event.chart_id:
            raise ValueError(
                f"NatalSnapshot chart_id ({natal_snapshot.chart_id!r}) does not "
                f"match EventRecord chart_id ({event.chart_id!r})."
            )

        active_dashas = {
            system: find_active_dasha_chain(tree, event.event_date)
            for system, tree in dasha_trees.items()
        }

        transits: tuple[TransitPlanetResult, ...] = ()
        if self._transit_engine is not None:
            # events.event_date is a date (no time-of-day is recorded by
            # the schema); approximated as midnight UTC on that date for
            # the transit moment. This is a documented approximation, not
            # a hidden one — see Design Audit follow-ups.
            event_datetime_utc = datetime.combine(event.event_date, time.min, tzinfo=timezone.utc)
            transits = tuple(
                self._transit_engine.compute_transit(natal_snapshot.chart, event_datetime_utc)
            )

        return EventAstrologicalContext(
            event_id=event.id,
            chart_id=event.chart_id,
            active_dashas=active_dashas,
            transits=transits,
            natal_snapshot=natal_snapshot,
            context_version=self._CONTEXT_VERSION,
        )

    def build_event_facts(
        self,
        event: EventRecord,
        context: EventAstrologicalContext,
        rule_results: Optional[tuple[RuleResult, ...]] = None,
    ) -> tuple[Fact, ...]:
        """
        Standardized `event.{event_id}.*` Facts for downstream modules
        (Research/Statistics/Knowledge/AI — none built yet), using the
        existing Fact(key, value, source) dataclass unchanged. See
        Design Audit §6 for the key-namespace rationale.
        """
        facts: list[Fact] = [
            Fact(f"event.{event.id}.category", event.category, "event_engine"),
            Fact(f"event.{event.id}.is_verified", event.is_verified, "event_engine"),
        ]

        for system, chain in context.active_dashas.items():
            for period in chain:
                facts.append(
                    Fact(
                        f"event.{event.id}.dasha.{system}.level{period.level}.lord",
                        period.lord,
                        "event_engine",
                    )
                )

        if rule_results:
            for result in rule_results:
                facts.append(
                    Fact(
                        f"event.{event.id}.rule.{result.rule_id}.matched",
                        result.matched,
                        "event_engine",
                    )
                )

        return tuple(facts)

    def _dasha_rule_facts(self, context: EventAstrologicalContext) -> list[Fact]:
        """
        Chart/rule-facing `dasha.*` facts (no event id in the key) for
        merging into the FactRegistry passed to RuleEngine — same
        lookup result as build_event_facts()'s dasha entries, emitted
        under a different key prefix for a different consumer. One
        lookup (already done in build_context), two fact emissions —
        no duplicate computation. See Design Audit §6.
        """
        facts: list[Fact] = []
        for system, chain in context.active_dashas.items():
            for period in chain:
                facts.append(
                    Fact(
                        f"dasha.{system}.level{period.level}.lord",
                        period.lord,
                        "event_engine",
                    )
                )
        return facts

    def analyze(
        self,
        event: EventRecord,
        dasha_trees: dict[str, DashaTree],
        natal_snapshot: NatalSnapshot,
        fact_registry: Optional[FactRegistry] = None,
    ) -> EventAnalysis:
        """
        Top-level orchestration: builds the context, optionally runs
        RuleEngine against a merged FactRegistry (the caller's own
        `fact_registry` — typically FactBuilder's output for this
        chart/event-date — plus this event's dasha.* facts), builds the
        standardized event.* Facts, and returns one EventAnalysis.

        `fact_registry` is never mutated — if RuleEngine evaluation is
        requested, a new FactRegistry is built from its contents plus
        the dasha facts, so the caller's own registry is unaffected.

        rule_results is None (not evaluated) unless BOTH a RuleEngine
        was supplied at construction AND a `fact_registry` is passed
        here — matching FactBuilder's own graceful-degradation pattern
        for optional dependencies.
        """
        context = self.build_context(event, dasha_trees, natal_snapshot)

        rule_results: Optional[tuple[RuleResult, ...]] = None
        if self._rule_engine is not None and fact_registry is not None:
            merged_registry = FactRegistry()
            for fact in fact_registry.all_facts():
                merged_registry.add_fact(fact)
            for fact in self._dasha_rule_facts(context):
                merged_registry.add_fact(fact)
            rule_results = tuple(self._rule_engine.evaluate_all(merged_registry))

        event_facts = self.build_event_facts(event, context, rule_results)

        return EventAnalysis(
            event=event,
            context=context,
            rule_results=rule_results,
            event_facts=event_facts,
            analysis_version=self._ANALYSIS_VERSION,
        )

    def analyze_batch(
        self,
        events: list[EventRecord],
        dasha_trees: dict[str, DashaTree],
        natal_snapshot: NatalSnapshot,
        fact_registries: Optional[dict[uuid.UUID, FactRegistry]] = None,
    ) -> BatchAnalysisResult:
        """
        Analyzes many EventRecords for ONE chart, reusing the SAME
        `dasha_trees` and `natal_snapshot` across every event — the
        efficient-batch counterpart to calling `analyze()` in a
        hand-written loop. Nothing natal or Dasha-tree-shaped is
        recomputed per event; only the genuinely per-event work
        (Dasha-by-date lookup, Transit, and — if used — a merged
        FactRegistry) happens once per event, same as a single
        `analyze()` call.

        `fact_registries`, if given, maps `event.id -> FactRegistry`
        (typically each built via `FactBuilder.build_facts(chart,
        transit_datetime_utc=event.event_date)` for that specific
        event's date) — a per-event registry is looked up by id and
        passed through to that event's own `analyze()` call. An event
        with no entry in `fact_registries` simply gets `fact_registry=None`
        for that call (same graceful-degradation behavior as calling
        `analyze()` directly without one).

        Validates chart-id consistency for the WHOLE batch up front —
        raises ValueError naming every offending event id at once (not
        just the first one hit) if any event's `chart_id` doesn't match
        `natal_snapshot.chart_id`. This is a batch-scoped version of the
        same guard `build_context()` already applies per event; catching
        it up front avoids partially analyzing a batch before failing
        partway through on a mismatched chart.

        Any OTHER exception raised while analyzing an individual event
        (e.g. from a supplied TransitEngine or RuleEngine) is caught and
        counted as a failure for that event only — one bad event does
        not abort the rest of the batch. Returns a BatchAnalysisResult
        with `analyses` holding only the successful EventAnalysis
        objects, in input order.
        """
        mismatched = [e.id for e in events if e.chart_id != natal_snapshot.chart_id]
        if mismatched:
            raise ValueError(
                f"NatalSnapshot chart_id ({natal_snapshot.chart_id!r}) does not "
                f"match {len(mismatched)} event(s)' chart_id: {mismatched!r}."
            )

        fact_registries = fact_registries or {}
        analyses: list[EventAnalysis] = []
        successful = 0
        failed = 0

        for event in events:
            try:
                analysis = self.analyze(
                    event,
                    dasha_trees,
                    natal_snapshot,
                    fact_registry=fact_registries.get(event.id),
                )
            except Exception:
                failed += 1
                continue
            analyses.append(analysis)
            successful += 1

        return BatchAnalysisResult(
            analyses=tuple(analyses),
            total_events=len(events),
            successful=successful,
            failed=failed,
        )
