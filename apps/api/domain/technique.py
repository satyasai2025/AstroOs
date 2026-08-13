"""
AstroOS — Technique Intelligence: Domain Objects

A *generic, domain-agnostic* astrological technique framework. A Technique
is any named methodology (marriage timing, Raj Yoga, Neecha Bhanga, a Nadi
method, a medical-astrology reading, ...) expressed as a set of versioned,
provenance-tracked references to rules that the existing deterministic
RuleEngine (domain/rules.py + services/rule_engine.py) already evaluates.

Design constraints honoured here (see the framework spec):
  - The framework contains NO domain-specific assumptions (no "eye",
    "marriage", "career" fields). Those live only in registered Technique
    instances / fixtures.
  - Rules are NOT re-invented. A TechniqueRuleRef points at a rule_id in the
    existing rule_registry; the evaluable condition logic stays in
    domain/rules.py. This layer only adds technique-level metadata:
    provenance, role (primary/supporting/contradicting/exception/
    cancellation), confidence and versioning.
  - Provenance is a first-class, separate axis from lifecycle status. A rule
    can be SOURCE_DERIVED yet UNTESTED; VALIDATED is earned, never assumed.
  - Missing data is explicit (DataAvailability), never inferred.

Pure Python dataclasses only — no ORM / Pydantic dependency, matching the
convention in domain/rules.py, domain/prediction_evidence.py, domain/
event_timing.py. Persistence lives in models/technique.py; the evaluable
rules live in the rule_registry. This module is the shared vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Provenance (source-derivation axis) ───────────────────────────────────────


class ProvenanceStatus(str, Enum):
    """How a technique/rule relates to its source evidence.

    This is deliberately ORTHOGONAL to any lifecycle status. `SOURCE_DERIVED`
    means the source explicitly states it; `DERIVED` means the extraction
    system inferred it and it must NEVER be presented as a source fact. A
    later contradicting source produces `CONTRADICTED` (or a new version) —
    historical evidence is never silently overwritten.
    """

    SOURCE_DERIVED = "source_derived"
    DERIVED = "derived"
    VALIDATED = "validated"
    PARTIALLY_VALIDATED = "partially_validated"
    CONTRADICTED = "contradicted"
    UNTESTED = "untested"
    DEPRECATED = "deprecated"


# ── Missing-data states ───────────────────────────────────────────────────────


class DataAvailability(str, Enum):
    """Explicit availability of a required input. Never inferred: a missing
    required fact lowers confidence rather than being guessed."""

    AVAILABLE = "available"
    NOT_PRESENT = "not_present"
    NOT_APPLICABLE = "not_applicable"
    INSUFFICIENT_DATA = "insufficient_data"


# ── Rule role within a technique ──────────────────────────────────────────────


class RuleRole(str, Enum):
    """The part a referenced rule plays in the technique's synthesis."""

    PRIMARY = "primary"              # a core indication
    SUPPORTING = "supporting"        # strengthens a primary indication
    CONTRADICTING = "contradicting"  # weakens / opposes an indication
    EXCEPTION = "exception"          # a documented exception to a rule
    CANCELLATION = "cancellation"    # cancels an indication when triggered


# ── Rule trigger outcome ──────────────────────────────────────────────────────


class TriggerStatus(str, Enum):
    TRIGGERED = "triggered"
    NOT_TRIGGERED = "not_triggered"
    INSUFFICIENT_DATA = "insufficient_data"


# ── Event-timing metadata (optional; only meaningful for timing techniques) ───


class TimingResolution(str, Enum):
    """The granularity a technique's window claim may report. A technique must
    never claim finer precision than its methodology actually supports.

    Domain-agnostic vocabulary living here (not imported from a dedicated
    event-timing module) so TechniqueDefinition has no dependency on any one
    technique's domain — every other field on this dataclass follows the same
    rule (see module docstring)."""

    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    TIME = "time"
    EVENT_WINDOW = "event_window"


# ── Technique → rule reference ────────────────────────────────────────────────


@dataclass(frozen=True)
class TechniqueRuleRef:
    """A technique's typed reference to one rule in the rule_registry.

    The evaluable conditions live in the referenced RuleDefinition (rule_id +
    rule_version). This ref carries only the technique-layer metadata the
    RuleDefinition intentionally does not: what ROLE the rule plays here, its
    PROVENANCE against the source, a per-rule confidence weight, and whether
    it is active in this technique version.
    """

    rule_id: str
    rule_version: str
    role: RuleRole = RuleRole.PRIMARY
    provenance: ProvenanceStatus = ProvenanceStatus.UNTESTED
    weight: float = 1.0
    source_reference: str = ""
    active: bool = True


# ── Technique definition ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class TechniqueDefinition:
    """A registered, versioned astrological technique — pure data.

    `required_inputs` are Fact-key prefixes the technique needs (e.g.
    "planet.sun.house", "house.2.lord", "dasha.current_lord"); the engine
    checks their availability to compute missing-data states. `dependencies`
    is a free-form set of higher-level chart dependencies (charts/vargas/
    dasha/transit) for documentation and the knowledge graph.

    `provenance` and `status` are separate axes (see ProvenanceStatus). A
    freshly-imported technique is UNTESTED even if every rule is
    SOURCE_DERIVED. `unresolved_inconsistencies` preserves source conflicts
    that were intentionally NOT auto-resolved (e.g. conflicting rule
    numbering between two sections of a source).
    """

    technique_id: str            # stable slug, e.g. "eye_health", "marriage_timing"
    name: str
    version: int
    description: str = ""
    tradition: str = ""          # e.g. "Parashari", "Jaimini", "Nadi", "KP"
    objective: str = ""          # intent key a resolver can match, e.g. "ocular_health"
    source_references: tuple[str, ...] = field(default_factory=tuple)
    required_inputs: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    rule_refs: tuple[TechniqueRuleRef, ...] = field(default_factory=tuple)
    provenance: ProvenanceStatus = ProvenanceStatus.UNTESTED
    status: str = "research"     # reuses the RESEARCH-first lifecycle vocabulary
    unresolved_inconsistencies: tuple[str, ...] = field(default_factory=tuple)
    # Event-timing metadata — empty/None for techniques that aren't about
    # timing an event (e.g. eye_health). Never inferred from rule_refs.
    event_types: tuple[str, ...] = field(default_factory=tuple)
    timing_resolution: Optional[TimingResolution] = None


# ── Execution result ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RuleTrigger:
    """The evaluated outcome of one TechniqueRuleRef against a FactRegistry."""

    rule_id: str
    rule_name: str
    role: RuleRole
    status: TriggerStatus
    provenance: ProvenanceStatus
    matched_conditions: tuple[str, ...]
    failed_conditions: tuple[str, ...]
    missing_facts: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class InputAvailability:
    """Availability of one required input for a technique execution."""

    fact_key: str
    availability: DataAvailability


@dataclass(frozen=True)
class TechniqueExecutionResult:
    """The full, neutral, structured result of running a technique.

    Deliberately NOT hard-coded around any domain (no medical/eye fields).
    Callers (and the AI Explain layer) read the buckets and the transparent
    `confidence`; they never receive free-floating prose that isn't backed by
    a RuleTrigger. `confidence` is 0-100, reconstructible from the primary
    triggers and reduced by insufficient data — never asserted independently.
    """

    technique_id: str
    technique_version: int
    triggers: tuple[RuleTrigger, ...]
    inputs: tuple[InputAvailability, ...]
    confidence: int
    confidence_basis: str
    evidence: tuple[str, ...]
    unresolved_inconsistencies: tuple[str, ...] = field(default_factory=tuple)

    def _by_role(self, role: RuleRole) -> tuple[RuleTrigger, ...]:
        return tuple(
            t for t in self.triggers
            if t.role is role and t.status is TriggerStatus.TRIGGERED
        )

    @property
    def primary(self) -> tuple[RuleTrigger, ...]:
        return self._by_role(RuleRole.PRIMARY)

    @property
    def supporting(self) -> tuple[RuleTrigger, ...]:
        return self._by_role(RuleRole.SUPPORTING)

    @property
    def contradicting(self) -> tuple[RuleTrigger, ...]:
        return self._by_role(RuleRole.CONTRADICTING)

    @property
    def exceptions(self) -> tuple[RuleTrigger, ...]:
        return self._by_role(RuleRole.EXCEPTION)

    @property
    def cancellations(self) -> tuple[RuleTrigger, ...]:
        return self._by_role(RuleRole.CANCELLATION)
