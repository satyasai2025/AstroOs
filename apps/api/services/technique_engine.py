"""
AstroOS — Technique Engine

The bridge between the Calculation layer (Facts) and the Prediction layer.
It executes a TechniqueDefinition by delegating EVERY condition evaluation to
the existing deterministic RuleEngine (services/rule_engine.py). It invents no
astrology and no rules: it only

  1. resolves each TechniqueRuleRef to its registered RuleDefinition,
  2. detects explicit missing-data states (a rule whose conditions reference a
     Fact the registry does not have is INSUFFICIENT_DATA, never guessed),
  3. runs RuleEngine on the rest to get TRIGGERED / NOT_TRIGGERED,
  4. buckets the outcomes by role and produces a transparent confidence,
  5. carries the technique's unresolved source inconsistencies through
     untouched.

The output is a neutral, structured TechniqueExecutionResult — the factual
"rule-trigger / evidence" layer the AI Explain Engine later narrates. This
engine never produces user-facing prose or domain-specific (medical/marriage/
career) claims.
"""

from __future__ import annotations

from apps.api.domain.prediction_evidence import (
    PredictionConfidence,
    PredictionEvidence,
    PredictionReason,
    PredictionRule,
)
from apps.api.domain.rules import Condition, ConditionGroup, RuleDefinition
from apps.api.domain.technique import (
    DataAvailability,
    InputAvailability,
    ProvenanceStatus,
    RuleTrigger,
    TechniqueDefinition,
    TechniqueExecutionResult,
    TechniqueRuleRef,
    TriggerStatus,
)
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.rule_engine import RuleEngine
from apps.api.services.rule_registry import get_rule


def _collect_fact_keys(items: tuple, out: set[str]) -> None:
    """Recursively collect every Fact key a rule's conditions reference."""
    for item in items:
        if isinstance(item, ConditionGroup):
            _collect_fact_keys(item.conditions, out)
        elif isinstance(item, Condition):
            out.add(item.fact_key)


class TechniqueEngine:
    """Stateless — one FactRegistry (and one technique) per call."""

    def __init__(self, rule_engine: RuleEngine | None = None) -> None:
        self._rules = rule_engine or RuleEngine()

    def execute(
        self,
        technique: TechniqueDefinition,
        facts: FactRegistry,
    ) -> TechniqueExecutionResult:
        triggers: list[RuleTrigger] = []
        evidence: list[str] = []

        for ref in technique.rule_refs:
            if not ref.active:
                continue
            triggers.append(self._evaluate_ref(ref, facts, evidence))

        inputs = self._input_availability(technique, facts)
        confidence, basis = self._confidence(triggers, inputs)

        return TechniqueExecutionResult(
            technique_id=technique.technique_id,
            technique_version=technique.version,
            triggers=tuple(triggers),
            inputs=tuple(inputs),
            confidence=confidence,
            confidence_basis=basis,
            evidence=tuple(evidence),
            unresolved_inconsistencies=technique.unresolved_inconsistencies,
        )

    # ── per-rule evaluation ──────────────────────────────────────────────────

    def _evaluate_ref(
        self,
        ref: TechniqueRuleRef,
        facts: FactRegistry,
        evidence: list[str],
    ) -> RuleTrigger:
        rule = get_rule(ref.rule_id)
        if rule is None:
            # A technique may only reference rules that exist in the registry.
            return RuleTrigger(
                rule_id=ref.rule_id,
                rule_name=ref.rule_id,
                role=ref.role,
                status=TriggerStatus.INSUFFICIENT_DATA,
                provenance=ref.provenance,
                matched_conditions=(),
                failed_conditions=(),
                missing_facts=(),
                explanation=f"Rule {ref.rule_id!r} is not registered.",
            )

        missing = self._missing_facts(rule, facts)
        if missing:
            return RuleTrigger(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                role=ref.role,
                status=TriggerStatus.INSUFFICIENT_DATA,
                provenance=ref.provenance,
                matched_conditions=(),
                failed_conditions=(),
                missing_facts=tuple(sorted(missing)),
                explanation=(
                    f"Insufficient data for {rule.rule_id}: missing "
                    f"{', '.join(sorted(missing))}."
                ),
            )

        result = self._rules.evaluate(rule.rule_id, facts)
        status = TriggerStatus.TRIGGERED if result.matched else TriggerStatus.NOT_TRIGGERED
        if result.matched:
            evidence.append(f"[{ref.role.value}] {rule.rule_id}: {result.explanation}")

        return RuleTrigger(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            role=ref.role,
            status=status,
            provenance=ref.provenance,
            matched_conditions=result.matched_conditions,
            failed_conditions=result.failed_conditions,
            missing_facts=(),
            explanation=result.explanation or rule.explanation,
        )

    @staticmethod
    def _missing_facts(rule: RuleDefinition, facts: FactRegistry) -> set[str]:
        keys: set[str] = set()
        _collect_fact_keys(rule.conditions, keys)
        return {k for k in keys if not facts.has_fact(k)}

    # ── inputs & confidence ──────────────────────────────────────────────────

    @staticmethod
    def _input_availability(
        technique: TechniqueDefinition,
        facts: FactRegistry,
    ) -> list[InputAvailability]:
        out: list[InputAvailability] = []
        for key in technique.required_inputs:
            availability = (
                DataAvailability.AVAILABLE
                if facts.has_fact(key)
                else DataAvailability.INSUFFICIENT_DATA
            )
            out.append(InputAvailability(fact_key=key, availability=availability))
        return out

    @staticmethod
    def _confidence(
        triggers: list[RuleTrigger],
        inputs: list[InputAvailability],
    ) -> tuple[int, str]:
        """Transparent, deterministic confidence.

        Base = fraction of PRIMARY rules that TRIGGERED (of those that had
        sufficient data). Contradictions/cancellations subtract; supporting
        rules add a small bounded bonus. Missing required inputs scale the
        whole score down. Never a bare number — the basis string is the
        reconstruction.
        """
        primary = [t for t in triggers if t.role.value == "primary"]
        evaluable = [t for t in primary if t.status is not TriggerStatus.INSUFFICIENT_DATA]
        fired = [t for t in evaluable if t.status is TriggerStatus.TRIGGERED]

        if not evaluable:
            return 0, "No primary rule had sufficient data — confidence 0."

        base = len(fired) / len(evaluable)

        supporting = sum(
            1 for t in triggers
            if t.role.value == "supporting" and t.status is TriggerStatus.TRIGGERED
        )
        opposing = sum(
            1 for t in triggers
            if t.role.value in ("contradicting", "cancellation")
            and t.status is TriggerStatus.TRIGGERED
        )

        score = base + 0.05 * supporting - 0.15 * opposing
        score = max(0.0, min(1.0, score))

        # Scale down by missing required inputs.
        if inputs:
            available = sum(
                1 for i in inputs if i.availability is DataAvailability.AVAILABLE
            )
            input_factor = available / len(inputs)
        else:
            input_factor = 1.0

        final = round(score * input_factor * 100)
        basis = (
            f"{len(fired)}/{len(evaluable)} primary rules triggered; "
            f"+{supporting} supporting, -{opposing} opposing; "
            f"input availability {round(input_factor * 100)}%."
        )
        return final, basis


def to_prediction_evidence(
    technique: TechniqueDefinition,
    result: TechniqueExecutionResult,
) -> PredictionEvidence:
    """Adapt a TechniqueExecutionResult onto the generic, already-proven
    PredictionEvidence contract (domain/prediction_evidence.py) — the same
    shape the Jaimini yoga engine returns — so the Technique framework and
    Jaimini yogas expose one prediction/evidence output, not two.

    One PredictionReason per RuleTrigger (regardless of role): this keeps the
    `len(reasons) == confidence.total_conditions` invariant trivially true
    and preserves every rule's individual outcome, not just the primaries
    `TechniqueExecutionResult.primary` filters down to. `is_matched` mirrors
    whether the technique produced at least one triggered primary indication
    — the same bar TechniqueEngine's own confidence calculation uses.
    """
    reasons = tuple(
        PredictionReason(
            description=trigger.explanation,
            matched_objects=(trigger.rule_id,),
            is_satisfied=trigger.status is TriggerStatus.TRIGGERED,
        )
        for trigger in result.triggers
    )
    satisfied = sum(1 for r in reasons if r.is_satisfied)

    return PredictionEvidence(
        rule=PredictionRule(
            rule_id=technique.technique_id,
            name=technique.name,
            sutra_reference=technique.source_references[0] if technique.source_references else "",
            rule_version=str(technique.version),
            requires=technique.required_inputs,
        ),
        is_matched=len(result.primary) > 0,
        triggering_conditions=tuple(t.rule_id for t in result.triggers if t.status is TriggerStatus.TRIGGERED),
        reasons=reasons,
        confidence=PredictionConfidence(
            score=result.confidence,
            satisfied_conditions=satisfied,
            total_conditions=len(reasons),
            basis=result.confidence_basis,
        ),
        explanation="; ".join(result.evidence) if result.evidence else result.confidence_basis,
    )
