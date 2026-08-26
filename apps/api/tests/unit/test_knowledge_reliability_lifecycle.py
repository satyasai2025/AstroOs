"""
Unit tests for Knowledge Reliability Framework lifecycle state transitions,
governance gates, invariant enforcement, and zero AI promotion authority.
"""

import uuid
import pytest

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    EvidenceLevel,
    InvalidLifecycleTransitionError,
    ReviewStatus,
    RuleLifecycleState,
    RuleValidationSummary,
    ScholarlyEvaluation,
    SourceProvenance,
    SourceReliabilityTier,
    TechniqueFramework,
    UnauthorizedLifecycleTransitionError,
    ValidationPolicy,
    ValidationPolicyViolationError,
)
from apps.api.services.knowledge_reliability_engine import KnowledgeReliabilityEngine


@pytest.fixture
def engine():
    return KnowledgeReliabilityEngine()


@pytest.fixture
def sample_source(engine):
    src_id = uuid.uuid4()
    prov = SourceProvenance(
        edition_title="Brihat Parashara Hora Shastra (Santhanam Ed.)",
        publisher="Ranjan Publications",
        publication_year=1984,
        editor_or_translator="R. Santhanam",
        is_critical_edition=True,
    )
    scholarly = ScholarlyEvaluation(
        tradition="Parashari",
        methodology_clarity_notes="Foundational compendium with explicit verse definitions.",
    )
    return engine.register_source(
        source_id=src_id,
        source_name="Brihat Parashara Hora Shastra",
        tier=SourceReliabilityTier.AUTHENTICATED_CLASSICAL,
        provenance=prov,
        scholarly_eval=scholarly,
        review_status=ReviewStatus.PEER_REVIEWED,
    )


def test_source_reliability_does_not_promote_rule_evidence_level(engine, sample_source):
    """
    CRITICAL INVARIANT: A high-tier classical source does NOT automatically make its rules VALIDATED.
    All newly documented rules must default strictly to UNVALIDATED.
    """
    rule = engine.document_rule(
        rule_id="RULE-BPHS-GK-01",
        rule_name="Gajakesari Yoga (Lagna Kendra)",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="BPHS Chapter 35, Sloka 1-2",
        original_text_excerpt="kendrasthite devagurau mṛgāṅkāt kendre...",
        extracted_by_actor_id="ai-curator-v1",
        extracted_by_role=ActorRole.AI_AGENT,
        rule_definition_id="DEF-GK-01",
    )

    assert rule.lifecycle_state == RuleLifecycleState.DOCUMENTED
    assert rule.evidence_level == EvidenceLevel.UNVALIDATED
    assert rule.validation_summary is None


def test_ai_agent_cannot_promote_to_reviewed_validated_or_canonical(engine, sample_source):
    """
    GOVERNANCE INVARIANT: AI actors have ZERO authority to promote rules to REVIEWED, VALIDATED, or CANONICAL.
    """
    rule = engine.document_rule(
        rule_id="RULE-BPHS-HAMSA-01",
        rule_name="Hamsa Yoga (Exalted Jupiter Kendra)",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="BPHS Chapter 35, Sloka 10",
        original_text_excerpt="svoccha-svarkshe kendragate gurau...",
        extracted_by_actor_id="ai-agent-007",
        extracted_by_role=ActorRole.AI_AGENT,
        rule_definition_id="DEF-HAMSA-01",
    )

    # Attempt AI promotion to REVIEWED -> Must fail
    with pytest.raises(UnauthorizedLifecycleTransitionError) as exc_reviewed:
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.REVIEWED,
            actor_id="ai-agent-007",
            actor_role=ActorRole.AI_AGENT,
            notes="AI self-reviewed",
        )
    assert "AI agents cannot promote rule" in str(exc_reviewed.value)

    # Attempt AI promotion to VALIDATED -> Must fail
    with pytest.raises(UnauthorizedLifecycleTransitionError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.VALIDATED,
            actor_id="ai-agent-007",
            actor_role=ActorRole.AI_AGENT,
        )

    # Attempt AI promotion to CANONICAL -> Must fail
    with pytest.raises(UnauthorizedLifecycleTransitionError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.CANONICAL,
            actor_id="ai-agent-007",
            actor_role=ActorRole.AI_AGENT,
        )


def test_human_expert_review_transition(engine, sample_source):
    """
    Human expert verifies the rule translation and DSL syntax, transitioning to REVIEWED.
    """
    rule = engine.document_rule(
        rule_id="RULE-BPHS-001",
        rule_name="Dhana Yoga 2L in 11H",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="BPHS Chapter 41, Sloka 5",
        original_text_excerpt="dhaneshe labhagopete...",
        extracted_by_actor_id="ai-extractor",
        extracted_by_role=ActorRole.AI_AGENT,
        rule_definition_id="DEF-DY-01",
    )

    reviewed_rule = engine.transition_lifecycle(
        rule_id=rule.rule_id,
        target_state=RuleLifecycleState.REVIEWED,
        actor_id="scholar-acharya-108",
        actor_role=ActorRole.HUMAN_EXPERT,
        notes="Verified against original Sanskrit text. Condition DSL mapped correctly.",
    )

    assert reviewed_rule.lifecycle_state == RuleLifecycleState.REVIEWED
    assert reviewed_rule.evidence_level == EvidenceLevel.UNVALIDATED
    assert len(reviewed_rule.review_history) == 2


def test_validation_policy_enforcement_and_promotion_to_validated(engine, sample_source):
    """
    Rule validated against a configurable validation policy.
    """
    rule = engine.document_rule(
        rule_id="RULE-BPHS-002",
        rule_name="Dhana Yoga 11L in 2H",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="BPHS Chapter 41, Sloka 6",
        original_text_excerpt="labheshe dhanagopete...",
        extracted_by_actor_id="human-curator",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-DY-02",
    )

    # Move to REVIEWED first
    engine.transition_lifecycle(
        rule_id=rule.rule_id,
        target_state=RuleLifecycleState.REVIEWED,
        actor_id="scholar-acharya-108",
        actor_role=ActorRole.HUMAN_EXPERT,
    )

    # 1. Validation failure: insufficient cases
    insufficient_val = RuleValidationSummary(
        rule_id=rule.rule_id,
        policy_id="POLICY_STANDARD_EMPIRICAL",
        cases_tested=15,
        applicable_cases=10,  # min is 30
        supported_outcomes=8,
        unsupported_outcomes=2,
        indeterminate_cases=0,
        empirical_hit_rate=0.80,
    )
    with pytest.raises(ValidationPolicyViolationError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.VALIDATED,
            actor_id="research-runner",
            actor_role=ActorRole.RESEARCH_ENGINE,
            validation_summary=insufficient_val,
        )

    # 2. Validation failure: low hit rate
    low_hit_val = RuleValidationSummary(
        rule_id=rule.rule_id,
        policy_id="POLICY_STANDARD_EMPIRICAL",
        cases_tested=120,
        applicable_cases=80,
        supported_outcomes=32,
        unsupported_outcomes=48,
        indeterminate_cases=0,
        empirical_hit_rate=0.40,  # min is 0.60
    )
    with pytest.raises(ValidationPolicyViolationError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.VALIDATED,
            actor_id="research-runner",
            actor_role=ActorRole.RESEARCH_ENGINE,
            validation_summary=low_hit_val,
        )

    # 3. Successful validation satisfying policy
    successful_val = RuleValidationSummary(
        rule_id=rule.rule_id,
        policy_id="POLICY_STANDARD_EMPIRICAL",
        cases_tested=150,
        applicable_cases=100,
        supported_outcomes=78,
        unsupported_outcomes=22,
        indeterminate_cases=0,
        counterexamples=("RC-1984-042", "RC-1991-118"),
        empirical_hit_rate=0.78,
        brier_score=0.14,
        dataset_id="BENCH-FINANCE-001",
        benchmark_experiment_id="EXP-BENCH-FINANCE-001-42-hash123",
    )
    validated_rule = engine.transition_lifecycle(
        rule_id=rule.rule_id,
        target_state=RuleLifecycleState.VALIDATED,
        actor_id="research-runner",
        actor_role=ActorRole.RESEARCH_ENGINE,
        validation_summary=successful_val,
    )

    assert validated_rule.lifecycle_state == RuleLifecycleState.VALIDATED
    assert validated_rule.evidence_level == EvidenceLevel.HIGH
    assert validated_rule.validation_summary.empirical_hit_rate == 0.78


def test_canonical_promotion_and_governance_gate(engine, sample_source):
    """
    Only GOVERNANCE_ADMIN can promote a VALIDATED rule with benchmark proof to CANONICAL.
    """
    rule = engine.document_rule(
        rule_id="RULE-BPHS-003",
        rule_name="Ruchaka Yoga (Exalted Mars in Kendra)",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="BPHS Chapter 35, Sloka 8",
        original_text_excerpt="svocche kshetre...",
        extracted_by_actor_id="curator",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-RUCHAKA-01",
    )

    engine.transition_lifecycle(
        rule_id=rule.rule_id,
        target_state=RuleLifecycleState.REVIEWED,
        actor_id="scholar",
        actor_role=ActorRole.HUMAN_EXPERT,
    )

    val_summary = RuleValidationSummary(
        rule_id=rule.rule_id,
        policy_id="POLICY_STANDARD_EMPIRICAL",
        cases_tested=200,
        applicable_cases=140,
        supported_outcomes=115,
        unsupported_outcomes=25,
        indeterminate_cases=0,
        empirical_hit_rate=0.82,
        brier_score=0.12,
        dataset_id="BENCH-LEADERSHIP-001",
        benchmark_experiment_id="EXP-BENCH-LEADERSHIP-001-777",
    )
    engine.transition_lifecycle(
        rule_id=rule.rule_id,
        target_state=RuleLifecycleState.VALIDATED,
        actor_id="research-runner",
        actor_role=ActorRole.RESEARCH_ENGINE,
        validation_summary=val_summary,
    )

    # Promotion by research engine or human expert must fail
    with pytest.raises(UnauthorizedLifecycleTransitionError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.CANONICAL,
            actor_id="scholar",
            actor_role=ActorRole.HUMAN_EXPERT,
        )

    # Promotion by Governance Admin succeeds
    canonical_rule = engine.transition_lifecycle(
        rule_id=rule.rule_id,
        target_state=RuleLifecycleState.CANONICAL,
        actor_id="admin-board",
        actor_role=ActorRole.GOVERNANCE_ADMIN,
        notes="Approved for canonical baseline consensus profile.",
    )

    assert canonical_rule.lifecycle_state == RuleLifecycleState.CANONICAL
    assert canonical_rule.evidence_level == EvidenceLevel.HIGH
    assert canonical_rule.canonical_signoff_by == "admin-board"
    assert canonical_rule.canonical_signoff_at is not None


def test_illegal_state_jumps_rejected(engine, sample_source):
    """
    Illegal lifecycle jumps (e.g. DOCUMENTED directly to CANONICAL) are rejected.
    """
    rule = engine.document_rule(
        rule_id="RULE-JUMP-001",
        rule_name="Unreviewed Rule",
        technique_framework=TechniqueFramework.PARASHARI,
        source_id=sample_source.source_id,
        passage_reference="BPHS Ch 12",
        original_text_excerpt="some text",
        extracted_by_actor_id="curator",
        extracted_by_role=ActorRole.HUMAN_CURATOR,
        rule_definition_id="DEF-JUMP-01",
    )

    # Direct jump to CANONICAL
    with pytest.raises(InvalidLifecycleTransitionError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.CANONICAL,
            actor_id="admin",
            actor_role=ActorRole.GOVERNANCE_ADMIN,
        )

    # Direct jump to VALIDATED without REVIEWED
    with pytest.raises(InvalidLifecycleTransitionError):
        engine.transition_lifecycle(
            rule_id=rule.rule_id,
            target_state=RuleLifecycleState.VALIDATED,
            actor_id="admin",
            actor_role=ActorRole.GOVERNANCE_ADMIN,
        )
