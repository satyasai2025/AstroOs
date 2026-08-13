"""
AstroOS — Technique Repository

Persistence for the generic Technique framework (models/technique.py). Follows
the async-SQLAlchemy convention of research_repository.py: module-level
domain↔model mappers plus a repository class taking an AsyncSession.

Versioning is soft-append (migration 0021, mirroring 0008): `create_version`
always inserts a NEW row. `supersede` links an old row to its replacement.
Rows are never mutated in place, so any analysis that referenced version N can
still reconstruct exactly what it saw.

The evaluable rule logic is NOT stored here — `definition_json` serialises the
TechniqueDefinition's rule_refs (rule_id + version + role + provenance); the
conditions live in the code rule_registry.
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.technique import (
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
    TimingResolution,
)
from apps.api.domain.rules import RuleDefinition
from apps.api.models.technique import (
    TechniqueModel,
    TechniqueSourceModel,
    TechniqueValidationCaseModel,
)
from apps.api.services import rule_registry, technique_registry
from apps.api.services.rule_serialization import rule_from_dict, rule_to_dict


# ── serialisation ─────────────────────────────────────────────────────────────


def definition_to_json(
    t: TechniqueDefinition,
    rule_defs: list[RuleDefinition] | None = None,
) -> str:
    """Serialize a technique for storage.

    `rule_refs` carries the technique-layer metadata (role/provenance). When
    `rule_defs` is given (imported techniques that have no hand-coded Python
    module), the full evaluable rule BODIES are embedded under "rules" so they
    can be reconstructed into the rule_registry on load — this is what lets a
    persisted imported technique run without a per-technique source file. For
    fixtures whose rules live in code (e.g. services/techniques/eye_health.py),
    `rule_defs` is omitted and only the refs are stored.
    """
    payload = {
        "source_references": list(t.source_references),
        "required_inputs": list(t.required_inputs),
        "dependencies": list(t.dependencies),
        "unresolved_inconsistencies": list(t.unresolved_inconsistencies),
        "event_types": list(t.event_types),
        "timing_resolution": t.timing_resolution.value if t.timing_resolution else None,
        "rule_refs": [
            {
                "rule_id": r.rule_id,
                "rule_version": r.rule_version,
                "role": r.role.value,
                "provenance": r.provenance.value,
                "weight": r.weight,
                "source_reference": r.source_reference,
                "active": r.active,
            }
            for r in t.rule_refs
        ],
    }
    if rule_defs is not None:
        payload["rules"] = [rule_to_dict(r) for r in rule_defs]
    return json.dumps(payload)


def rules_from_model(m: TechniqueModel) -> list[RuleDefinition]:
    """Reconstruct embedded evaluable rule bodies (empty for code-backed
    fixtures that stored only refs)."""
    data = json.loads(m.definition_json or "{}")
    return [rule_from_dict(r) for r in data.get("rules", [])]


def register_from_model(m: TechniqueModel) -> TechniqueDefinition:
    """Load a persisted technique into the runtime registries so the untouched
    RuleEngine/TechniqueEngine can execute it — no Python module required.

    Registers any embedded rule bodies (idempotently) into rule_registry and
    the technique into technique_registry, then returns the domain object.
    """
    technique = model_to_domain(m)
    for rd in rules_from_model(m):
        rule_registry.ensure_rule(rd)
    if technique_registry.get_technique(technique.technique_id, technique.version) is None:
        technique_registry.register_technique(technique)
    return technique


def model_to_domain(m: TechniqueModel) -> TechniqueDefinition:
    data = json.loads(m.definition_json or "{}")
    refs = tuple(
        TechniqueRuleRef(
            rule_id=r["rule_id"],
            rule_version=r.get("rule_version", "1.0"),
            role=RuleRole(r.get("role", "primary")),
            provenance=ProvenanceStatus(r.get("provenance", "untested")),
            weight=r.get("weight", 1.0),
            source_reference=r.get("source_reference", ""),
            active=r.get("active", True),
        )
        for r in data.get("rule_refs", [])
    )
    return TechniqueDefinition(
        technique_id=m.technique_key,
        name=m.name,
        version=m.version,
        description=m.description,
        tradition=m.tradition,
        objective=m.objective,
        source_references=tuple(data.get("source_references", [])),
        required_inputs=tuple(data.get("required_inputs", [])),
        dependencies=tuple(data.get("dependencies", [])),
        rule_refs=refs,
        provenance=ProvenanceStatus(m.provenance),
        status=m.status,
        unresolved_inconsistencies=tuple(data.get("unresolved_inconsistencies", [])),
        event_types=tuple(data.get("event_types", [])),
        timing_resolution=(
            TimingResolution(data["timing_resolution"])
            if data.get("timing_resolution")
            else None
        ),
    )


# ── repository ────────────────────────────────────────────────────────────────


class TechniqueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_version(
        self,
        technique: TechniqueDefinition,
        version_comment: str | None = None,
        rule_defs: list[RuleDefinition] | None = None,
    ) -> TechniqueModel:
        """Insert a new immutable technique version row.

        Pass `rule_defs` (from the import pipeline) to embed the evaluable rule
        bodies so the technique can run after a fresh load with no Python
        module. Omit it for code-backed fixtures.
        """
        model = TechniqueModel(
            technique_key=technique.technique_id,
            name=technique.name,
            description=technique.description,
            tradition=technique.tradition,
            objective=technique.objective,
            provenance=technique.provenance.value,
            status=technique.status,
            version=technique.version,
            version_comment=version_comment,
            definition_json=definition_to_json(technique, rule_defs),
        )
        self._session.add(model)
        await self._session.flush()
        return model

    async def get_current(self, technique_key: str) -> Optional[TechniqueDefinition]:
        """Highest non-superseded version for a key."""
        stmt = (
            select(TechniqueModel)
            .where(
                TechniqueModel.technique_key == technique_key,
                TechniqueModel.superseded_by.is_(None),
                TechniqueModel.deleted_at.is_(None),
            )
            .order_by(TechniqueModel.version.desc())
            .limit(1)
        )
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return model_to_domain(m) if m else None

    async def get_current_model(self, technique_key: str) -> Optional[TechniqueModel]:
        """The highest non-superseded ORM row (for loading embedded rule bodies)."""
        stmt = (
            select(TechniqueModel)
            .where(
                TechniqueModel.technique_key == technique_key,
                TechniqueModel.superseded_by.is_(None),
                TechniqueModel.deleted_at.is_(None),
            )
            .order_by(TechniqueModel.version.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def load_and_register_current(
        self, technique_key: str
    ) -> Optional[TechniqueDefinition]:
        """Load a persisted technique from PostgreSQL and register it (plus its
        embedded rule bodies) into the runtime registries — the fresh-process
        entry point that makes a technique executable with no Python module."""
        m = await self.get_current_model(technique_key)
        return register_from_model(m) if m else None

    async def get_version(
        self, technique_key: str, version: int
    ) -> Optional[TechniqueDefinition]:
        stmt = select(TechniqueModel).where(
            TechniqueModel.technique_key == technique_key,
            TechniqueModel.version == version,
            TechniqueModel.deleted_at.is_(None),
        )
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return model_to_domain(m) if m else None

    async def list_current(self) -> list[TechniqueDefinition]:
        stmt = select(TechniqueModel).where(
            TechniqueModel.superseded_by.is_(None),
            TechniqueModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [model_to_domain(m) for m in rows]

    async def supersede(self, old_id: uuid.UUID, new_id: uuid.UUID) -> None:
        """Link an old version row to its replacement (never mutates content)."""
        await self._session.execute(
            update(TechniqueModel)
            .where(TechniqueModel.id == old_id)
            .values(superseded_by=new_id)
        )

    async def add_source(
        self,
        technique_id: uuid.UUID,
        *,
        source_type: str,
        reference: str,
        excerpt: str | None = None,
        notes: str | None = None,
    ) -> TechniqueSourceModel:
        model = TechniqueSourceModel(
            technique_id=technique_id,
            source_type=source_type,
            reference=reference,
            excerpt=excerpt,
            notes=notes,
        )
        self._session.add(model)
        await self._session.flush()
        return model

    async def add_validation_case(
        self,
        technique_id: uuid.UUID,
        *,
        rule_id: str,
        expected_result: str,
        observed_result: str,
        match_status: str,
        chart_ref: str | None = None,
        evidence_json: str = "{}",
        notes: str | None = None,
    ) -> TechniqueValidationCaseModel:
        model = TechniqueValidationCaseModel(
            technique_id=technique_id,
            rule_id=rule_id,
            chart_ref=chart_ref,
            expected_result=expected_result,
            observed_result=observed_result,
            match_status=match_status,
            evidence_json=evidence_json,
            notes=notes,
        )
        self._session.add(model)
        await self._session.flush()
        return model
