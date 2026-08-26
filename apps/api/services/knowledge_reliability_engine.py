"""
AstroOS — Knowledge Reliability Engine

Core service engine governing:
1. Multidimensional source reliability tracking (no single truth score)
2. Strict rule lifecycle state transitions and invariant guardrails
3. Zero AI promotion authority to VALIDATED or CANONICAL
4. Traceable provenance chains
5. Configurable validation policy enforcement
6. Evidence family aggregation (anti-double counting)
7. Preserving conflicting evidence without majority voting
8. Technique framework isolation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

if TYPE_CHECKING:  # import only for typing — avoids a runtime import cycle
    from apps.api.domain.benchmark_experiment import BenchmarkExperiment

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    ConflictPreservationStatus,
    EmpiricalConflictRecord,
    EvidenceFamily,
    EvidenceLevel,
    InvalidLifecycleTransitionError,
    KnowledgeReliabilityError,
    ProvenanceIntegrityError,
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
    TechniqueIsolationError,
    UnauthorizedLifecycleTransitionError,
    ValidationPolicy,
    ValidationPolicyViolationError,
)


class KnowledgeReliabilityEngine:
    """
    Stateless or in-memory registry capable service for the Knowledge Reliability Framework.
    Can operate in-memory for unit testing and domain execution or delegate to repository.
    """

    def __init__(self) -> None:
        self._sources: Dict[uuid.UUID, SourceReliabilityRecord] = {}
        self._rules: Dict[str, RuleReliabilityRecord] = {}
        self._policies: Dict[str, ValidationPolicy] = {}
        self._families: Dict[str, EvidenceFamily] = {}
        self._conflicts: Dict[str, EmpiricalConflictRecord] = {}

        # Seed standard default validation policies
        self._seed_default_policies()

    def _seed_default_policies(self) -> None:
        default_policy = ValidationPolicy(
            policy_id="POLICY_STANDARD_EMPIRICAL",
            name="Standard Empirical Validation Policy",
            min_applicable_cases=30,
            min_holdout_cases=100,
            min_hit_rate=0.60,
            max_brier_score=0.25,
            max_counterexample_ratio=0.15,
            require_independent_replication=True,
            require_holdout_split=True,
        )
        strict_policy = ValidationPolicy(
            policy_id="POLICY_STRICT_CRITICAL",
            name="Strict Critical Evidence Policy",
            min_applicable_cases=50,
            min_holdout_cases=200,
            min_hit_rate=0.75,
            max_brier_score=0.18,
            max_counterexample_ratio=0.08,
            require_independent_replication=True,
            require_holdout_split=True,
        )
        self._policies[default_policy.policy_id] = default_policy
        self._policies[strict_policy.policy_id] = strict_policy

    # ── Source Reliability (Issue 1: Multidimensional, No Truth Score) ────────

    def register_source(
        self,
        source_id: uuid.UUID,
        source_name: str,
        tier: SourceReliabilityTier,
        provenance: SourceProvenance,
        scholarly_eval: ScholarlyEvaluation,
        review_status: ReviewStatus = ReviewStatus.UNREVIEWED,
        empirical_citations: Sequence[str] = (),
        known_failures_or_contradictions: Sequence[str] = (),
    ) -> SourceReliabilityRecord:
        """Register a multidimensional source reliability assessment."""
        record = SourceReliabilityRecord(
            source_id=source_id,
            source_name=source_name,
            tier=tier,
            provenance=provenance,
            scholarly_eval=scholarly_eval,
            review_status=review_status,
            empirical_citations=tuple(empirical_citations),
            known_failures_or_contradictions=tuple(known_failures_or_contradictions),
            audit_log=(f"Source registered under tier {tier.value} at {datetime.now(timezone.utc).isoformat()}",),
        )
        self._sources[source_id] = record
        return record

    def get_source(self, source_id: uuid.UUID) -> Optional[SourceReliabilityRecord]:
        return self._sources.get(source_id)

    # ── Rule Documentation & Provenance ───────────────────────────────────────

    def document_rule(
        self,
        rule_id: str,
        rule_name: str,
        technique_framework: TechniqueFramework,
        source_id: uuid.UUID,
        passage_reference: str,
        original_text_excerpt: str,
        extracted_by_actor_id: str,
        extracted_by_role: ActorRole,
        rule_definition_id: str,
        extraction_method: str = "MANUAL_SCHOLARLY_TRANSCRIPTION",
        evidence_family_id: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> RuleReliabilityRecord:
        """
        Extract and document a rule from a source.
        INVARIANT: Rule evidence level is ALWAYS UNVALIDATED initially, regardless of source tier.
        """
        if not passage_reference or not passage_reference.strip():
            raise ProvenanceIntegrityError("Cannot document rule without non-empty passage reference.")

        if not original_text_excerpt or not original_text_excerpt.strip():
            raise ProvenanceIntegrityError("Cannot document rule without original text excerpt.")

        if not rule_definition_id or not rule_definition_id.strip():
            raise ProvenanceIntegrityError("Cannot document rule without valid rule_definition_id.")

        provenance = RuleProvenanceChain(
            source_id=source_id,
            passage_reference=passage_reference.strip(),
            original_text_excerpt=original_text_excerpt.strip(),
            extraction_method=extraction_method,
            extracted_by_actor_id=extracted_by_actor_id,
            extracted_by_role=extracted_by_role,
            rule_definition_id=rule_definition_id.strip(),
            source_name=source_name,
        )

        record = RuleReliabilityRecord(
            rule_id=rule_id,
            rule_name=rule_name,
            technique_framework=technique_framework,
            provenance=provenance,
            evidence_family_id=evidence_family_id,
            lifecycle_state=RuleLifecycleState.DOCUMENTED,
            evidence_level=EvidenceLevel.UNVALIDATED,  # Invariant: always unvalidated on creation
            validation_summary=None,
            review_history=(
                f"Documented by {extracted_by_actor_id} ({extracted_by_role.value}) via {extraction_method} at {datetime.now(timezone.utc).isoformat()}",
            ),
        )
        self._rules[rule_id] = record
        return record

    def get_rule(self, rule_id: str) -> Optional[RuleReliabilityRecord]:
        return self._rules.get(rule_id)

    # ── Lifecycle State Machine & Invariants (Issues 2 & 3) ───────────────────

    def transition_lifecycle(
        self,
        rule_id: str,
        target_state: RuleLifecycleState,
        actor_id: str,
        actor_role: ActorRole,
        notes: str = "",
        validation_summary: Optional[RuleValidationSummary] = None,
        policy_id: Optional[str] = None,
    ) -> RuleReliabilityRecord:
        """
        Executes a controlled state transition with governance and invariant checks.
        """
        current_record = self._rules.get(rule_id)
        if not current_record:
            raise KnowledgeReliabilityError(f"Rule {rule_id} not found in reliability registry.")

        current_state = current_record.lifecycle_state

        # ── Invariant: AI actors have ZERO authority for REVIEWED / VALIDATED / CANONICAL
        if actor_role == ActorRole.AI_AGENT:
            if target_state in (RuleLifecycleState.REVIEWED, RuleLifecycleState.VALIDATED, RuleLifecycleState.CANONICAL):
                raise UnauthorizedLifecycleTransitionError(
                    f"AI agents cannot promote rule {rule_id} to {target_state.value}. "
                    "Promotion requires human expert or benchmark governance sign-off."
                )

        # ── State Machine Transitions
        new_evidence_level = current_record.evidence_level
        new_validation_summary = current_record.validation_summary
        canonical_signoff_by = current_record.canonical_signoff_by
        canonical_signoff_at = current_record.canonical_signoff_at

        if target_state == RuleLifecycleState.REVIEWED:
            if current_state not in (RuleLifecycleState.DOCUMENTED, RuleLifecycleState.CANONICAL):
                raise InvalidLifecycleTransitionError(
                    f"Cannot transition from {current_state.value} to REVIEWED."
                )
            if actor_role not in (ActorRole.HUMAN_EXPERT, ActorRole.GOVERNANCE_ADMIN):
                raise UnauthorizedLifecycleTransitionError(
                    "Only HUMAN_EXPERT or GOVERNANCE_ADMIN can mark rules as REVIEWED."
                )
            # Retains UNVALIDATED until empirical benchmark passes
            new_evidence_level = EvidenceLevel.UNVALIDATED

        elif target_state == RuleLifecycleState.VALIDATED:
            if current_state != RuleLifecycleState.REVIEWED:
                raise InvalidLifecycleTransitionError(
                    f"Rule must be in REVIEWED state before VALIDATED (currently {current_state.value})."
                )
            if actor_role not in (ActorRole.RESEARCH_ENGINE, ActorRole.GOVERNANCE_ADMIN):
                raise UnauthorizedLifecycleTransitionError(
                    "Only RESEARCH_ENGINE or GOVERNANCE_ADMIN can mark rules as VALIDATED."
                )
            if not validation_summary:
                raise ValidationPolicyViolationError("ValidationSummary is required to transition to VALIDATED.")

            active_policy = self.get_policy(policy_id or validation_summary.policy_id)
            if not active_policy:
                raise ValidationPolicyViolationError(f"Validation policy '{policy_id or validation_summary.policy_id}' not found.")

            computed_level, is_passed = self.evaluate_validation_against_policy(validation_summary, active_policy)
            if not is_passed:
                raise ValidationPolicyViolationError(
                    f"Validation results failed policy '{active_policy.name}': "
                    f"Hit rate={validation_summary.empirical_hit_rate:.2f} (min {active_policy.min_hit_rate:.2f}), "
                    f"Applicable cases={validation_summary.applicable_cases} (min {active_policy.min_applicable_cases})."
                )

            new_evidence_level = computed_level
            new_validation_summary = validation_summary

        elif target_state == RuleLifecycleState.CONTRADICTED:
            if actor_role not in (ActorRole.RESEARCH_ENGINE, ActorRole.HUMAN_EXPERT, ActorRole.GOVERNANCE_ADMIN):
                raise UnauthorizedLifecycleTransitionError("Unauthorized to mark rule as CONTRADICTED.")
            new_evidence_level = EvidenceLevel.CONTRADICTED
            if validation_summary:
                new_validation_summary = validation_summary

        elif target_state == RuleLifecycleState.CANONICAL:
            if current_state != RuleLifecycleState.VALIDATED:
                raise InvalidLifecycleTransitionError(
                    f"Rule must be in VALIDATED state before promotion to CANONICAL (currently {current_state.value})."
                )
            if actor_role != ActorRole.GOVERNANCE_ADMIN:
                raise UnauthorizedLifecycleTransitionError(
                    "Only GOVERNANCE_ADMIN can promote rules to CANONICAL."
                )
            if not current_record.validation_summary or not current_record.validation_summary.benchmark_experiment_id:
                raise ValidationPolicyViolationError("Cannot promote to CANONICAL without benchmark_experiment_id.")

            new_evidence_level = EvidenceLevel.HIGH
            canonical_signoff_by = actor_id
            canonical_signoff_at = datetime.now(timezone.utc)

        else:
            raise InvalidLifecycleTransitionError(f"Unhandled transition to {target_state.value}")

        review_entry = f"Transitioned to {target_state.value} by {actor_id} ({actor_role.value}) at {datetime.now(timezone.utc).isoformat()}. Notes: {notes}"
        updated_record = RuleReliabilityRecord(
            rule_id=current_record.rule_id,
            rule_name=current_record.rule_name,
            technique_framework=current_record.technique_framework,
            provenance=current_record.provenance,
            evidence_family_id=current_record.evidence_family_id,
            lifecycle_state=target_state,
            evidence_level=new_evidence_level,
            validation_summary=new_validation_summary,
            conflict_ids=current_record.conflict_ids,
            review_history=current_record.review_history + (review_entry,),
            canonical_signoff_by=canonical_signoff_by,
            canonical_signoff_at=canonical_signoff_at,
        )
        self._rules[rule_id] = updated_record
        return updated_record

    # ── Validation Policies (Issue 2: Configurable, No Magic Numbers) ────────

    def register_policy(self, policy: ValidationPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[ValidationPolicy]:
        return self._policies.get(policy_id)

    def build_validation_summary_from_experiment(
        self,
        rule_id: str,
        experiment: "BenchmarkExperiment",
        policy_id: str,
        profile_id: Optional[str] = None,
    ) -> RuleValidationSummary:
        """
        Derive a RuleValidationSummary for `rule_id` from a REAL
        BenchmarkExperiment, using apps/api/domain/benchmark_validation_bridge.

        This is the wiring between the benchmark system and the knowledge
        governance system. Before it existed, every RuleValidationSummary in
        the codebase was hand-constructed with manually supplied numbers, so a
        governance record could not be traced back to an actual benchmark run.

        The returned summary carries the experiment's real experiment_id and
        corpus id/version, so `transition_lifecycle`'s existing
        benchmark_experiment_id invariant is satisfiable from genuine data.

        This method does NOT transition the rule. Pass the result to
        `transition_lifecycle(...)` — which keeps every existing governance
        guard (actor authority, state machine, policy check) in force. In
        particular an AI actor still cannot reach VALIDATED/REVIEWED/CANONICAL.
        """
        from apps.api.domain.benchmark_validation_bridge import (
            build_validation_summary_from_benchmark,
        )

        policy = self.get_policy(policy_id)
        if not policy:
            raise ValidationPolicyViolationError(
                f"Validation policy '{policy_id}' not found."
            )
        return build_validation_summary_from_benchmark(
            experiment=experiment,
            rule_id=rule_id,
            policy=policy,
            profile_id=profile_id,
        )

    def evaluate_validation_against_policy(
        self,
        summary: RuleValidationSummary,
        policy: ValidationPolicy,
    ) -> Tuple[EvidenceLevel, bool]:
        """
        Evaluates a validation summary against a configurable policy.
        Returns (computed_evidence_level, is_passed).
        """
        if summary.applicable_cases < policy.min_applicable_cases:
            return EvidenceLevel.INSUFFICIENT_DATA, False

        counterexample_ratio = len(summary.counterexamples) / max(summary.applicable_cases, 1)
        if counterexample_ratio > policy.max_counterexample_ratio:
            return EvidenceLevel.CONTRADICTED, False

        if summary.empirical_hit_rate < policy.min_hit_rate:
            return EvidenceLevel.LOW, False

        if summary.brier_score is not None and summary.brier_score > policy.max_brier_score:
            return EvidenceLevel.LOW, False

        if policy.require_holdout_split and summary.cases_tested < policy.min_holdout_cases:
            return EvidenceLevel.MODERATE, True

        return EvidenceLevel.HIGH, True

    # ── Evidence Families (Issue 7: Anti-Double Counting) ─────────────────────

    def register_evidence_family(
        self,
        family_id: str,
        name: str,
        underlying_principle: str,
        tradition: TechniqueFramework,
        member_rule_ids: Sequence[str] = (),
        max_independent_dof: int = 1,
    ) -> EvidenceFamily:
        """Register an evidence family to group derivative rules."""
        family = EvidenceFamily(
            family_id=family_id,
            name=name,
            underlying_principle=underlying_principle,
            tradition=tradition,
            member_rule_ids=tuple(member_rule_ids),
            max_independent_dof=max_independent_dof,
        )
        self._families[family_id] = family
        return family

    def get_evidence_family(self, family_id: str) -> Optional[EvidenceFamily]:
        return self._families.get(family_id)

    def calculate_independent_confirmations(
        self,
        rule_ids: Sequence[str],
    ) -> Dict[str, Any]:
        """
        Calculates true independent confirmations across matched rules.
        Collapses derivative rules in the same EvidenceFamily into family.max_independent_dof.
        """
        matched_families: Dict[str, List[str]] = {}
        standalone_rules: List[str] = []

        # Index member_rule_ids across registered families for lookup
        family_by_member_id: Dict[str, str] = {}
        for fam_id, fam_obj in self._families.items():
            for member_id in fam_obj.member_rule_ids:
                family_by_member_id[member_id] = fam_id

        for r_id in rule_ids:
            rule_rec = self._rules.get(r_id)
            fam_id = None
            if rule_rec and rule_rec.evidence_family_id:
                fam_id = rule_rec.evidence_family_id
            elif r_id in family_by_member_id:
                fam_id = family_by_member_id[r_id]

            if fam_id:
                matched_families.setdefault(fam_id, []).append(r_id)
            else:
                standalone_rules.append(r_id)

        independent_dof = len(standalone_rules)
        family_breakdown: Dict[str, Dict[str, Any]] = {}

        for fam_id, members in matched_families.items():
            fam_obj = self._families.get(fam_id)
            allowed_dof = fam_obj.max_independent_dof if fam_obj else 1
            contributed_dof = min(len(members), allowed_dof)
            independent_dof += contributed_dof
            family_breakdown[fam_id] = {
                "family_name": fam_obj.name if fam_obj else fam_id,
                "matched_rules_count": len(members),
                "member_rule_ids": members,
                "contributed_independent_dof": contributed_dof,
                "underlying_principle": fam_obj.underlying_principle if fam_obj else "",
            }

        return {
            "total_rules_matched": len(rule_ids),
            "independent_confirmations_dof": independent_dof,
            "standalone_rules_count": len(standalone_rules),
            "standalone_rule_ids": standalone_rules,
            "family_breakdown": family_breakdown,
        }

    # ── Conflict Preservation (Issue 8: No Majority Voting) ───────────────────

    def register_conflict(
        self,
        conflict_id: str,
        topic: str,
        technique_framework: TechniqueFramework,
        supporting_sources: Sequence[str],
        contradicting_sources: Sequence[str],
        empirical_findings: Sequence[str] = (),
        status: ConflictPreservationStatus = ConflictPreservationStatus.ACTIVE_DISPUTE,
        notes: str = "",
    ) -> EmpiricalConflictRecord:
        """Preserve an active doctrinal or empirical conflict without resolving by majority vote."""
        conflict = EmpiricalConflictRecord(
            conflict_id=conflict_id,
            topic=topic,
            technique_framework=technique_framework,
            supporting_sources=tuple(supporting_sources),
            contradicting_sources=tuple(contradicting_sources),
            empirical_findings=tuple(empirical_findings),
            status=status,
            notes=notes,
        )
        self._conflicts[conflict_id] = conflict
        return conflict

    def get_conflict(self, conflict_id: str) -> Optional[EmpiricalConflictRecord]:
        return self._conflicts.get(conflict_id)

    # ── Technique Boundary Isolation (Issue 9) ────────────────────────────────

    def validate_technique_compatibility(
        self,
        rule_ids: Sequence[str],
        target_framework: TechniqueFramework,
    ) -> bool:
        """
        Ensures that rules evaluated together belong to the same framework.
        Raises TechniqueIsolationError if cross-framework mixing is detected.
        """
        for r_id in rule_ids:
            rule_rec = self._rules.get(r_id)
            if rule_rec and rule_rec.technique_framework != target_framework:
                raise TechniqueIsolationError(
                    f"Rule '{r_id}' belongs to technique framework '{rule_rec.technique_framework.value}', "
                    f"which cannot be evaluated under target framework '{target_framework.value}' without an explicit adapter."
                )
        return True

    # ── Traceability & Querying ───────────────────────────────────────────────

    def get_rule_provenance_trace(self, rule_id: str) -> Dict[str, Any]:
        """Answers: 'Where did this rule come from?'"""
        record = self._rules.get(rule_id)
        if not record:
            raise KnowledgeReliabilityError(f"Rule '{rule_id}' not found.")

        src = self._sources.get(record.provenance.source_id)
        return {
            "rule_id": record.rule_id,
            "rule_name": record.rule_name,
            "technique_framework": record.technique_framework.value,
            "lifecycle_state": record.lifecycle_state.value,
            "evidence_level": record.evidence_level.value,
            "source_id": str(record.provenance.source_id),
            "source_name": record.provenance.source_name or (src.source_name if src else "Unknown"),
            "passage_reference": record.provenance.passage_reference,
            "original_text_excerpt": record.provenance.original_text_excerpt,
            "extraction_method": record.provenance.extraction_method,
            "extracted_by_actor_id": record.provenance.extracted_by_actor_id,
            "extracted_by_role": record.provenance.extracted_by_role.value,
            "rule_definition_id": record.provenance.rule_definition_id,
            "extracted_at": record.provenance.extracted_at.isoformat(),
        }

    def get_rule_validation_status(self, rule_id: str) -> Dict[str, Any]:
        """Answers: 'Why does AstroOS believe this rule exists and how has it performed?'"""
        record = self._rules.get(rule_id)
        if not record:
            raise KnowledgeReliabilityError(f"Rule '{rule_id}' not found.")

        val = record.validation_summary
        return {
            "rule_id": record.rule_id,
            "lifecycle_state": record.lifecycle_state.value,
            "evidence_level": record.evidence_level.value,
            "is_unvalidated": record.evidence_level == EvidenceLevel.UNVALIDATED,
            "has_empirical_validation": val is not None,
            "validation_summary": {
                "policy_id": val.policy_id,
                "cases_tested": val.cases_tested,
                "applicable_cases": val.applicable_cases,
                "supported_outcomes": val.supported_outcomes,
                "unsupported_outcomes": val.unsupported_outcomes,
                "indeterminate_cases": val.indeterminate_cases,
                "counterexamples_count": len(val.counterexamples),
                "empirical_hit_rate": val.empirical_hit_rate,
                "brier_score": val.brier_score,
                "dataset_id": val.dataset_id,
                "benchmark_experiment_id": val.benchmark_experiment_id,
                "validated_at": val.validated_at.isoformat(),
            } if val else None,
            "canonical_signoff": {
                "signoff_by": record.canonical_signoff_by,
                "signoff_at": record.canonical_signoff_at.isoformat() if record.canonical_signoff_at else None,
            } if record.canonical_signoff_by else None,
        }
