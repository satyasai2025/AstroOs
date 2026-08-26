"""
AstroOS — Knowledge Reliability Repository

Asynchronous database persistence layer for:
- Source reliability records
- Rule reliability records
- Evidence families
- Empirical conflicts
- Validation policies

Maps between SQLAlchemy ORM models and pure Python domain objects.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    ConflictPreservationStatus,
    EmpiricalConflictRecord,
    EvidenceFamily,
    EvidenceLevel,
    ReviewStatus,
    RuleLifecycleState,
    RuleProvenanceChain,
    RuleReliabilityRecord,
    RuleValidationSummary,
    ScholarlyEvaluation,
    SourceProvenance,
    SourceReliabilityRecord,
    SourceReliabilityTier,
    TechniqueFramework,
    ValidationPolicy,
)
from apps.api.models.knowledge_reliability import (
    KnowledgeEmpiricalConflictModel,
    KnowledgeEvidenceFamilyModel,
    KnowledgeRuleReliabilityModel,
    KnowledgeSourceReliabilityModel,
    KnowledgeValidationPolicyModel,
)


# ── Private Domain Mappers ───────────────────────────────────────────────────

def _source_to_domain(m: KnowledgeSourceReliabilityModel) -> SourceReliabilityRecord:
    prov_data = m.provenance_json or {}
    scholarly_data = m.scholarly_eval_json or {}
    return SourceReliabilityRecord(
        source_id=m.source_id,
        source_name=m.source_name,
        tier=SourceReliabilityTier(m.tier),
        provenance=SourceProvenance(
            edition_title=prov_data.get("edition_title", ""),
            publisher=prov_data.get("publisher", ""),
            publication_year=prov_data.get("publication_year"),
            editor_or_translator=prov_data.get("editor_or_translator"),
            manuscript_lineage=prov_data.get("manuscript_lineage"),
            is_critical_edition=prov_data.get("is_critical_edition", False),
        ),
        scholarly_eval=ScholarlyEvaluation(
            tradition=scholarly_data.get("tradition", ""),
            methodology_clarity_notes=scholarly_data.get("methodology_clarity_notes", ""),
            primary_commentaries=tuple(scholarly_data.get("primary_commentaries", ())),
            known_disputed_passages=tuple(scholarly_data.get("known_disputed_passages", ())),
        ),
        review_status=ReviewStatus(m.review_status),
        empirical_citations=tuple(m.empirical_citations or ()),
        known_failures_or_contradictions=tuple(m.known_failures_or_contradictions or ()),
        audit_log=tuple(m.audit_log or ()),
    )


def _rule_to_domain(m: KnowledgeRuleReliabilityModel) -> RuleReliabilityRecord:
    prov_data = m.provenance_json or {}
    val_data = m.validation_summary_json

    validation_summary = None
    if val_data:
        validation_summary = RuleValidationSummary(
            rule_id=m.rule_id,
            policy_id=val_data.get("policy_id", ""),
            cases_tested=val_data.get("cases_tested", 0),
            applicable_cases=val_data.get("applicable_cases", 0),
            supported_outcomes=val_data.get("supported_outcomes", 0),
            unsupported_outcomes=val_data.get("unsupported_outcomes", 0),
            indeterminate_cases=val_data.get("indeterminate_cases", 0),
            counterexamples=tuple(val_data.get("counterexamples", ())),
            empirical_hit_rate=val_data.get("empirical_hit_rate", 0.0),
            brier_score=val_data.get("brier_score"),
            dataset_id=val_data.get("dataset_id", ""),
            dataset_version=val_data.get("dataset_version", "1.0.0"),
            benchmark_experiment_id=val_data.get("benchmark_experiment_id"),
            validated_at=datetime.fromisoformat(val_data["validated_at"]) if "validated_at" in val_data else datetime.now(timezone.utc),
            validated_by_actor_id=val_data.get("validated_by_actor_id", "SYSTEM"),
        )

    return RuleReliabilityRecord(
        rule_id=m.rule_id,
        rule_name=m.rule_name,
        technique_framework=TechniqueFramework(m.technique_framework),
        provenance=RuleProvenanceChain(
            source_id=uuid.UUID(prov_data["source_id"]) if "source_id" in prov_data else m.source_id,
            passage_reference=prov_data.get("passage_reference", ""),
            original_text_excerpt=prov_data.get("original_text_excerpt", ""),
            extraction_method=prov_data.get("extraction_method", ""),
            extracted_by_actor_id=prov_data.get("extracted_by_actor_id", ""),
            extracted_by_role=ActorRole(prov_data.get("extracted_by_role", ActorRole.HUMAN_CURATOR.value)),
            rule_definition_id=prov_data.get("rule_definition_id", ""),
            source_name=prov_data.get("source_name"),
            extracted_at=datetime.fromisoformat(prov_data["extracted_at"]) if "extracted_at" in prov_data else datetime.now(timezone.utc),
        ),
        evidence_family_id=m.evidence_family_id,
        lifecycle_state=RuleLifecycleState(m.lifecycle_state),
        evidence_level=EvidenceLevel(m.evidence_level),
        validation_summary=validation_summary,
        conflict_ids=tuple(m.conflict_ids or ()),
        review_history=tuple(m.review_history or ()),
        canonical_signoff_by=m.canonical_signoff_by,
        canonical_signoff_at=m.canonical_signoff_at,
    )


def _family_to_domain(m: KnowledgeEvidenceFamilyModel) -> EvidenceFamily:
    return EvidenceFamily(
        family_id=m.family_id,
        name=m.name,
        underlying_principle=m.underlying_principle,
        tradition=TechniqueFramework(m.tradition),
        member_rule_ids=tuple(m.member_rule_ids or ()),
        max_independent_dof=m.max_independent_dof,
    )


def _conflict_to_domain(m: KnowledgeEmpiricalConflictModel) -> EmpiricalConflictRecord:
    return EmpiricalConflictRecord(
        conflict_id=m.conflict_id,
        topic=m.topic,
        technique_framework=TechniqueFramework(m.technique_framework),
        supporting_sources=tuple(m.supporting_sources or ()),
        contradicting_sources=tuple(m.contradicting_sources or ()),
        empirical_findings=tuple(m.empirical_findings or ()),
        status=ConflictPreservationStatus(m.status),
        notes=m.notes or "",
    )


def _policy_to_domain(m: KnowledgeValidationPolicyModel) -> ValidationPolicy:
    return ValidationPolicy(
        policy_id=m.policy_id,
        name=m.name,
        min_applicable_cases=m.min_applicable_cases,
        min_holdout_cases=m.min_holdout_cases,
        min_hit_rate=m.min_hit_rate,
        max_brier_score=m.max_brier_score,
        max_counterexample_ratio=m.max_counterexample_ratio,
        require_independent_replication=m.require_independent_replication,
        require_holdout_split=m.require_holdout_split,
    )


# ── Repository Class ─────────────────────────────────────────────────────────

class KnowledgeReliabilityRepository:
    """Async SQLAlchemy persistence repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Source Reliability ───────────────────────────────────────────────────

    async def save_source_reliability(self, record: SourceReliabilityRecord) -> SourceReliabilityRecord:
        stmt = select(KnowledgeSourceReliabilityModel).where(
            KnowledgeSourceReliabilityModel.source_id == record.source_id,
            KnowledgeSourceReliabilityModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        prov_dict = {
            "edition_title": record.provenance.edition_title,
            "publisher": record.provenance.publisher,
            "publication_year": record.provenance.publication_year,
            "editor_or_translator": record.provenance.editor_or_translator,
            "manuscript_lineage": record.provenance.manuscript_lineage,
            "is_critical_edition": record.provenance.is_critical_edition,
        }
        scholarly_dict = {
            "tradition": record.scholarly_eval.tradition,
            "methodology_clarity_notes": record.scholarly_eval.methodology_clarity_notes,
            "primary_commentaries": list(record.scholarly_eval.primary_commentaries),
            "known_disputed_passages": list(record.scholarly_eval.known_disputed_passages),
        }

        if model is None:
            model = KnowledgeSourceReliabilityModel(
                source_id=record.source_id,
                source_name=record.source_name,
                tier=record.tier.value,
                provenance_json=prov_dict,
                scholarly_eval_json=scholarly_dict,
                review_status=record.review_status.value,
                empirical_citations=list(record.empirical_citations),
                known_failures_or_contradictions=list(record.known_failures_or_contradictions),
                audit_log=list(record.audit_log),
            )
            self._session.add(model)
        else:
            model.source_name = record.source_name
            model.tier = record.tier.value
            model.provenance_json = prov_dict
            model.scholarly_eval_json = scholarly_dict
            model.review_status = record.review_status.value
            model.empirical_citations = list(record.empirical_citations)
            model.known_failures_or_contradictions = list(record.known_failures_or_contradictions)
            model.audit_log = list(record.audit_log)

        await self._session.flush()
        return _source_to_domain(model)

    async def get_source_reliability(self, source_id: uuid.UUID) -> Optional[SourceReliabilityRecord]:
        stmt = select(KnowledgeSourceReliabilityModel).where(
            KnowledgeSourceReliabilityModel.source_id == source_id,
            KnowledgeSourceReliabilityModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return _source_to_domain(model) if model else None

    # ── Rule Reliability ─────────────────────────────────────────────────────

    async def save_rule_reliability(self, record: RuleReliabilityRecord) -> RuleReliabilityRecord:
        stmt = select(KnowledgeRuleReliabilityModel).where(
            KnowledgeRuleReliabilityModel.rule_id == record.rule_id,
            KnowledgeRuleReliabilityModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        prov_dict = {
            "source_id": str(record.provenance.source_id),
            "passage_reference": record.provenance.passage_reference,
            "original_text_excerpt": record.provenance.original_text_excerpt,
            "extraction_method": record.provenance.extraction_method,
            "extracted_by_actor_id": record.provenance.extracted_by_actor_id,
            "extracted_by_role": record.provenance.extracted_by_role.value,
            "rule_definition_id": record.provenance.rule_definition_id,
            "source_name": record.provenance.source_name,
            "extracted_at": record.provenance.extracted_at.isoformat(),
        }

        val_dict = None
        if record.validation_summary:
            v = record.validation_summary
            val_dict = {
                "policy_id": v.policy_id,
                "cases_tested": v.cases_tested,
                "applicable_cases": v.applicable_cases,
                "supported_outcomes": v.supported_outcomes,
                "unsupported_outcomes": v.unsupported_outcomes,
                "indeterminate_cases": v.indeterminate_cases,
                "counterexamples": list(v.counterexamples),
                "empirical_hit_rate": v.empirical_hit_rate,
                "brier_score": v.brier_score,
                "dataset_id": v.dataset_id,
                "dataset_version": v.dataset_version,
                "benchmark_experiment_id": v.benchmark_experiment_id,
                "validated_at": v.validated_at.isoformat(),
                "validated_by_actor_id": v.validated_by_actor_id,
            }

        if model is None:
            model = KnowledgeRuleReliabilityModel(
                rule_id=record.rule_id,
                rule_name=record.rule_name,
                technique_framework=record.technique_framework.value,
                source_id=record.provenance.source_id,
                evidence_family_id=record.evidence_family_id,
                lifecycle_state=record.lifecycle_state.value,
                evidence_level=record.evidence_level.value,
                provenance_json=prov_dict,
                validation_summary_json=val_dict,
                conflict_ids=list(record.conflict_ids),
                review_history=list(record.review_history),
                canonical_signoff_by=record.canonical_signoff_by,
                canonical_signoff_at=record.canonical_signoff_at,
            )
            self._session.add(model)
        else:
            model.rule_name = record.rule_name
            model.technique_framework = record.technique_framework.value
            model.source_id = record.provenance.source_id
            model.evidence_family_id = record.evidence_family_id
            model.lifecycle_state = record.lifecycle_state.value
            model.evidence_level = record.evidence_level.value
            model.provenance_json = prov_dict
            model.validation_summary_json = val_dict
            model.conflict_ids = list(record.conflict_ids)
            model.review_history = list(record.review_history)
            model.canonical_signoff_by = record.canonical_signoff_by
            model.canonical_signoff_at = record.canonical_signoff_at

        await self._session.flush()
        return _rule_to_domain(model)

    async def get_rule_reliability(self, rule_id: str) -> Optional[RuleReliabilityRecord]:
        stmt = select(KnowledgeRuleReliabilityModel).where(
            KnowledgeRuleReliabilityModel.rule_id == rule_id,
            KnowledgeRuleReliabilityModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return _rule_to_domain(model) if model else None

    # ── Evidence Family ──────────────────────────────────────────────────────

    async def save_evidence_family(self, family: EvidenceFamily) -> EvidenceFamily:
        stmt = select(KnowledgeEvidenceFamilyModel).where(
            KnowledgeEvidenceFamilyModel.family_id == family.family_id,
            KnowledgeEvidenceFamilyModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        if model is None:
            model = KnowledgeEvidenceFamilyModel(
                family_id=family.family_id,
                name=family.name,
                underlying_principle=family.underlying_principle,
                tradition=family.tradition.value,
                member_rule_ids=list(family.member_rule_ids),
                max_independent_dof=family.max_independent_dof,
            )
            self._session.add(model)
        else:
            model.name = family.name
            model.underlying_principle = family.underlying_principle
            model.tradition = family.tradition.value
            model.member_rule_ids = list(family.member_rule_ids)
            model.max_independent_dof = family.max_independent_dof

        await self._session.flush()
        return _family_to_domain(model)

    async def get_evidence_family(self, family_id: str) -> Optional[EvidenceFamily]:
        stmt = select(KnowledgeEvidenceFamilyModel).where(
            KnowledgeEvidenceFamilyModel.family_id == family_id,
            KnowledgeEvidenceFamilyModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return _family_to_domain(model) if model else None

    # ── Validation Policies ──────────────────────────────────────────────────

    async def save_validation_policy(self, policy: ValidationPolicy) -> ValidationPolicy:
        stmt = select(KnowledgeValidationPolicyModel).where(
            KnowledgeValidationPolicyModel.policy_id == policy.policy_id,
            KnowledgeValidationPolicyModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        if model is None:
            model = KnowledgeValidationPolicyModel(
                policy_id=policy.policy_id,
                name=policy.name,
                min_applicable_cases=policy.min_applicable_cases,
                min_holdout_cases=policy.min_holdout_cases,
                min_hit_rate=policy.min_hit_rate,
                max_brier_score=policy.max_brier_score,
                max_counterexample_ratio=policy.max_counterexample_ratio,
                require_independent_replication=policy.require_independent_replication,
                require_holdout_split=policy.require_holdout_split,
            )
            self._session.add(model)
        else:
            model.name = policy.name
            model.min_applicable_cases = policy.min_applicable_cases
            model.min_holdout_cases = policy.min_holdout_cases
            model.min_hit_rate = policy.min_hit_rate
            model.max_brier_score = policy.max_brier_score
            model.max_counterexample_ratio = policy.max_counterexample_ratio
            model.require_independent_replication = policy.require_independent_replication
            model.require_holdout_split = policy.require_holdout_split

        await self._session.flush()
        return _policy_to_domain(model)

    async def get_validation_policy(self, policy_id: str) -> Optional[ValidationPolicy]:
        stmt = select(KnowledgeValidationPolicyModel).where(
            KnowledgeValidationPolicyModel.policy_id == policy_id,
            KnowledgeValidationPolicyModel.deleted_at.is_(None),
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return _policy_to_domain(model) if model else None
