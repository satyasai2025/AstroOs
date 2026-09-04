"""
AstroOS — Generic Technique Import Pipeline

    Source -> Extraction -> Normalization -> Rule creation -> Provenance
           -> Validation -> Technique Repository

Domain-agnostic: nothing here knows about eyes, marriage, or any technique.
Eye Health is merely the first fixture fed through it; Marriage Timing (or any
other) goes through the SAME pipeline with no change to this file, the
TechniqueEngine, or the RuleEngine.

How imported rules reach the existing deterministic engine (the core trick):
  build_technique() turns each proposed rule into a domain/rules.py
  RuleDefinition (via rule_serialization) and register_technique()/registration
  puts it in the existing rule_registry. The untouched RuleEngine then evaluates
  it by rule_id exactly like a hand-coded rule. No new engine, no per-technique
  Python module.

Extraction honesty:
  - RuleOrigin.EXPLICIT  -> ProvenanceStatus.SOURCE_DERIVED
  - RuleOrigin.DERIVED   -> ProvenanceStatus.DERIVED
  A derived rule is never relabelled as a source fact. Source inconsistencies
  are carried through untouched (unresolved_inconsistencies) — the pipeline
  never silently reconciles them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from apps.api.domain.rules import RuleDefinition
from apps.api.domain.technique import (
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
)
from apps.api.domain.technique_import import (
    RawRule,
    RawTechnique,
    RuleOrigin,
    SourceType,
    TechniqueSource,
)
from apps.api.services import rule_registry
from apps.api.services import technique_registry
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.rule_serialization import rule_from_dict, rule_to_dict
from apps.api.services.technique_engine import TechniqueEngine


# ── raw parsing (dict -> Raw*) ────────────────────────────────────────────────


def raw_technique_from_dict(d: dict[str, Any]) -> RawTechnique:
    """Parse a structured payload (from a STRUCTURED source or LLM JSON)."""
    rules = tuple(
        RawRule(
            rule_id=r["rule_id"],
            name=r.get("name", r["rule_id"]),
            conditions=tuple(r.get("conditions", ())),
            origin=RuleOrigin(r.get("origin", "explicit")),
            role=r.get("role", "primary"),
            priority=int(r.get("priority", 1)),
            category=r.get("category", "imported"),
            source_text=r.get("source_text", ""),
            explanation=r.get("explanation", ""),
            derived_facts=dict(r.get("derived_facts", {})),
            weight=float(r.get("weight", 1.0)),
            source_reference=r.get("source_reference", ""),
        )
        for r in d.get("rules", ())
    )
    return RawTechnique(
        technique_id=d["technique_id"],
        name=d.get("name", d["technique_id"]),
        version=int(d.get("version", 1)),
        description=d.get("description", ""),
        tradition=d.get("tradition", ""),
        objective=d.get("objective", ""),
        source_references=tuple(d.get("source_references", ())),
        dependencies=tuple(d.get("dependencies", ())),
        rules=rules,
        unresolved_inconsistencies=tuple(d.get("unresolved_inconsistencies", ())),
        required_inputs=tuple(d.get("required_inputs", ())),
    )


# ── Extraction stage ──────────────────────────────────────────────────────────


class TechniqueExtractor(Protocol):
    """Source -> RawTechnique. Implementations must set RuleOrigin honestly."""

    def extract(self, source: TechniqueSource) -> RawTechnique: ...


class StructuredTechniqueExtractor:
    """Deterministic extractor for already-structured sources.

    The primary, dependency-free path (no LLM): the source carries a ready
    RawTechnique payload. Used for programmatic imports, tests, and any source
    that has already been turned into structured JSON upstream.
    """

    def extract(self, source: TechniqueSource) -> RawTechnique:
        if source.payload is None:
            raise ValueError(
                "StructuredTechniqueExtractor requires source.payload "
                "(a RawTechnique dict)."
            )
        return raw_technique_from_dict(source.payload)


class LLMTechniqueExtractor:
    """LLM-backed extractor for free-text sources (PDF text, transcript, notes).

    Reuses the existing per-user AI provider (services/ai_provider.py) — it does
    NOT build its own HTTP client or read provider settings directly. The prompt
    forces strict JSON in the RawTechnique shape and requires an explicit
    origin ('explicit' | 'derived') per rule so the Provenance stage stays
    honest. The model proposes STRUCTURE from the source; it does not invent
    astrology beyond what the source contains (that discipline is enforced by
    the prompt + downstream validation, not by trusting the model).
    """

    _SYSTEM_PROMPT = (
        "You extract astrological techniques from a source into strict JSON. "
        "Return ONLY a JSON object matching this shape: {technique_id, name, "
        "version, description, tradition, objective, source_references[], "
        "dependencies[], unresolved_inconsistencies[], rules:[{rule_id, name, "
        "origin:'explicit'|'derived', role, priority, category, source_text, "
        "explanation, derived_facts:{}, conditions:[{type:'condition', fact_key, "
        "operator, value, description} | {type:'group', operator:'AND'|'OR', "
        "conditions:[...]}]}]}. Rules the source STATES are origin='explicit'; "
        "anything you infer is origin='derived' — never label an inference as "
        "explicit. Preserve, do not resolve, any contradictions or numbering "
        "gaps in the source by listing them in unresolved_inconsistencies. Do "
        "not invent rules that are not supported by the source."
    )

    def __init__(self, client: Any, resolved_provider: Any) -> None:
        self._client = client
        self._resolved = resolved_provider

    async def extract_async(self, source: TechniqueSource) -> RawTechnique:
        import json

        from apps.api.services.ai_provider import call_chat_completion

        user_prompt = (
            f"SOURCE TYPE: {source.source_type.value}\n"
            f"REFERENCE: {source.reference}\n\nCONTENT:\n{source.content}"
        )
        text = await call_chat_completion(
            self._client, self._resolved, self._SYSTEM_PROMPT, user_prompt,
            json_mode=True,
        )
        return raw_technique_from_dict(json.loads(text))

    def extract(self, source: TechniqueSource) -> RawTechnique:  # pragma: no cover
        raise RuntimeError("Use extract_async() for the LLM extractor.")


# ── Normalization stage ───────────────────────────────────────────────────────

_OPERATOR_ALIASES = {
    "==": "==", "eq": "==", "equals": "==", "=": "==", "is": "==",
    "!=": "!=", "ne": "!=", "neq": "!=", "is_not": "!=",
    ">": ">", "gt": ">", "greater_than": ">",
    "<": "<", "lt": "<", "less_than": "<",
    ">=": ">=", "gte": ">=", "ge": ">=", "at_least": ">=",
    "<=": "<=", "lte": "<=", "le": "<=", "at_most": "<=",
    "in": "in", "one_of": "in", "member_of": "in",
    "not_in": "not_in", "nin": "not_in", "none_of": "not_in",
}

# Sanskrit / alias -> canonical graha slug (subset mirroring
# knowledge_import_pipeline._GRAHA_ALIASES; kept local to avoid coupling).
_GRAHA_ALIASES = {
    "surya": "sun", "sun": "sun",
    "chandra": "moon", "moon": "moon",
    "mangala": "mars", "kuja": "mars", "mars": "mars",
    "budha": "mercury", "mercury": "mercury",
    "guru": "jupiter", "brihaspati": "jupiter", "jupiter": "jupiter",
    "shukra": "venus", "venus": "venus",
    "shani": "saturn", "saturn": "saturn",
    "rahu": "rahu", "ketu": "ketu",
}

_KNOWN_NAMESPACES = {"planet", "house", "dasha", "transit", "yoga", "nakshatra"}


def canonicalize_operator(op: str) -> str:
    key = str(op).strip().lower()
    if key not in _OPERATOR_ALIASES:
        raise ValueError(
            f"Unknown operator {op!r}; cannot normalize to a RuleEngine operator."
        )
    return _OPERATOR_ALIASES[key]


def canonicalize_fact_key(raw: str) -> str:
    """Best-effort canonicalization of a fact key to FactBuilder's vocabulary.

    Transparent and conservative: it lowercases, collapses whitespace, and
    canonicalizes graha names inside a `planet.<name>.` key. Keys already in a
    known namespace pass through; unrecognized keys are returned unchanged (the
    engine will then report INSUFFICIENT_DATA rather than a silent wrong match).
    """
    key = re.sub(r"\s+", "", str(raw).strip().lower())
    parts = key.split(".")
    if len(parts) >= 2 and parts[0] == "planet":
        parts[1] = _GRAHA_ALIASES.get(parts[1], parts[1])
        return ".".join(parts)
    return key


def _normalize_conditions(items: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    out: list[dict[str, Any]] = []
    for item in items:
        if item.get("type") == "group":
            out.append({
                "type": "group",
                "operator": str(item.get("operator", "AND")).strip().upper(),
                "conditions": list(_normalize_conditions(tuple(item.get("conditions", ())))),
            })
        else:
            out.append({
                "type": "condition",
                "fact_key": canonicalize_fact_key(item.get("fact_key", "")),
                "operator": canonicalize_operator(item.get("operator", "==")),
                "value": item.get("value"),
                "description": item.get("description", ""),
            })
    return tuple(out)


def _collect_fact_keys(items: tuple[dict[str, Any], ...], out: set[str]) -> None:
    for item in items:
        if item.get("type") == "group":
            _collect_fact_keys(tuple(item.get("conditions", ())), out)
        else:
            out.add(item["fact_key"])


def normalize_technique(raw: RawTechnique) -> RawTechnique:
    """Canonicalize fact keys + operators, and derive required_inputs."""
    norm_rules: list[RawRule] = []
    all_keys: set[str] = set()
    for r in raw.rules:
        conds = _normalize_conditions(r.conditions)
        _collect_fact_keys(conds, all_keys)
        norm_rules.append(
            RawRule(
                rule_id=r.rule_id, name=r.name, conditions=conds,
                origin=r.origin, role=r.role, priority=r.priority,
                category=r.category, source_text=r.source_text,
                explanation=r.explanation, derived_facts=r.derived_facts,
                weight=r.weight, source_reference=r.source_reference,
            )
        )
    required = raw.required_inputs or tuple(sorted(all_keys))
    return RawTechnique(
        technique_id=raw.technique_id, name=raw.name, version=raw.version,
        description=raw.description, tradition=raw.tradition,
        objective=raw.objective, source_references=raw.source_references,
        dependencies=raw.dependencies, rules=tuple(norm_rules),
        unresolved_inconsistencies=raw.unresolved_inconsistencies,
        required_inputs=required,
    )


# ── Rule creation + Provenance stage ──────────────────────────────────────────

_ORIGIN_TO_PROVENANCE = {
    RuleOrigin.EXPLICIT: ProvenanceStatus.SOURCE_DERIVED,
    RuleOrigin.DERIVED: ProvenanceStatus.DERIVED,
}


def _raw_rule_to_definition(r: RawRule) -> RuleDefinition:
    return rule_from_dict({
        "rule_id": r.rule_id,
        "rule_version": "1.0",
        "rule_name": r.name,
        "source_text": r.source_text,
        "priority": r.priority,
        "category": r.category,
        "conditions": list(r.conditions),
        "conclusion": {"derived_facts": r.derived_facts, "description": r.explanation},
        "explanation": r.explanation,
        "tags": (),
    })


def build_technique(raw: RawTechnique) -> tuple[list[RuleDefinition], TechniqueDefinition]:
    """Turn a normalized RawTechnique into evaluable RuleDefinitions + a
    TechniqueDefinition, applying provenance from each rule's origin."""
    rule_defs: list[RuleDefinition] = []
    refs: list[TechniqueRuleRef] = []
    for r in raw.rules:
        rule_defs.append(_raw_rule_to_definition(r))
        refs.append(TechniqueRuleRef(
            rule_id=r.rule_id,
            rule_version="1.0",
            role=RuleRole(r.role),
            provenance=_ORIGIN_TO_PROVENANCE[r.origin],
            weight=r.weight,
            source_reference=r.source_reference,
        ))
    technique = TechniqueDefinition(
        technique_id=raw.technique_id,
        name=raw.name,
        version=raw.version,
        description=raw.description,
        tradition=raw.tradition,
        objective=raw.objective,
        source_references=raw.source_references,
        required_inputs=raw.required_inputs,
        dependencies=raw.dependencies,
        rule_refs=tuple(refs),
        provenance=ProvenanceStatus.UNTESTED,  # validation is a separate, later step
        status="research",
        unresolved_inconsistencies=raw.unresolved_inconsistencies,
    )
    return rule_defs, technique


# ── Validation stage ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ValidationSample:
    """One validation case: a set of facts + the expected primary outcome."""

    label: str
    facts: FactRegistry
    expect_triggered: Optional[bool] = None  # None => record observation only


@dataclass(frozen=True)
class ValidationCaseResult:
    label: str
    triggered_primary: bool
    match_status: str  # match | mismatch | untested
    confidence: int


def validate_technique(
    technique: TechniqueDefinition,
    samples: tuple[ValidationSample, ...],
    *,
    engine: TechniqueEngine | None = None,
) -> list[ValidationCaseResult]:
    """Run the technique against sample charts using the EXISTING TechniqueEngine.

    Never auto-promotes provenance to VALIDATED — it records match/mismatch so a
    human (or a research job) decides. Absence of samples => empty list (status
    stays UNTESTED), never fabricated metrics.
    """
    eng = engine or TechniqueEngine()
    out: list[ValidationCaseResult] = []
    for s in samples:
        result = eng.execute(technique, s.facts)
        triggered = len(result.primary) > 0
        if s.expect_triggered is None:
            status = "untested"
        else:
            status = "match" if triggered == s.expect_triggered else "mismatch"
        out.append(ValidationCaseResult(
            label=s.label, triggered_primary=triggered,
            match_status=status, confidence=result.confidence,
        ))
    return out


# ── Orchestrator ──────────────────────────────────────────────────────────────


@dataclass
class ImportResult:
    technique: TechniqueDefinition
    rule_definitions: list[RuleDefinition]
    sources: list[TechniqueSource] = field(default_factory=list)
    validation: list[ValidationCaseResult] = field(default_factory=list)

    def serialized_rules(self) -> list[dict[str, Any]]:
        return [rule_to_dict(r) for r in self.rule_definitions]


class TechniqueImportPipeline:
    """Ties the stages together. Pure in-memory (extract -> ... -> register);
    persistence is a separate, explicit step (repository) so importing is
    testable without a database."""

    def __init__(self, extractor: TechniqueExtractor | None = None) -> None:
        self._extractor = extractor or StructuredTechniqueExtractor()

    def run(
        self,
        source: TechniqueSource,
        *,
        samples: tuple[ValidationSample, ...] = (),
        register: bool = True,
    ) -> ImportResult:
        raw = self._extractor.extract(source)                 # Extraction
        raw = normalize_technique(raw)                         # Normalization
        rule_defs, technique = build_technique(raw)           # Rule creation + Provenance
        if register:
            register_import(rule_defs, technique)
        validation = (                                        # Validation
            validate_technique(technique, samples) if samples else []
        )
        return ImportResult(
            technique=technique, rule_definitions=rule_defs,
            sources=[source], validation=validation,
        )


def register_import(
    rule_defs: list[RuleDefinition],
    technique: TechniqueDefinition,
) -> None:
    """Make an imported technique executable by the untouched engines: register
    its reconstructed rules (idempotently) into the existing rule_registry and
    the technique into the technique_registry."""
    for rd in rule_defs:
        rule_registry.ensure_rule(rd)
    if technique_registry.get_technique(technique.technique_id, technique.version) is None:
        technique_registry.register_technique(technique)


# ── Persistence (async, end-to-end) ───────────────────────────────────────────


async def persist_import(session: Any, result: ImportResult) -> Any:
    """Persist a completed import to PostgreSQL: the technique version (with the
    evaluable rule BODIES embedded so a fresh process needs no Python module),
    its provenance sources, and any validation cases.

    Uses the existing TechniqueRepository / models — no new persistence engine.
    Returns the created TechniqueModel row (already flushed; the caller's
    session governs commit).
    """
    # Imported lazily to keep the pipeline importable without the ORM/DB layer.
    from apps.api.repositories.technique_repository import TechniqueRepository

    repo = TechniqueRepository(session)
    model = await repo.create_version(
        result.technique, rule_defs=result.rule_definitions
    )

    for src in result.sources:
        await repo.add_source(
            model.id,
            source_type=src.source_type.value,
            reference=src.reference,
            excerpt=src.excerpt,
            notes=src.notes,
        )

    for case in result.validation:
        await repo.add_validation_case(
            model.id,
            rule_id=result.technique.technique_id,
            expected_result="triggered" if case.match_status != "untested" else "n/a",
            observed_result="triggered" if case.triggered_primary else "not_triggered",
            match_status=case.match_status,
            chart_ref=case.label,
        )

    return model
