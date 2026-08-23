"""
AstroOS — Research Reproducibility, Replication & Falsification Router (Priority 34)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.research_replication import (
    AssessReplicationRequest,
    CreateClaimRequest,
    CreateProtocolRequest,
    FalsificationExperimentSchema,
    NegativeControlResultSchema,
    NullModelResultSchema,
    ReplicationAuditEventResponse,
    ReplicationDatasetManifestSchema,
    ReplicationProtocolSchema,
    ReplicationSnapshotResponse,
    ReplicationStudyAssessmentResponse,
    ReproductionAssessmentSchema,
    ResearchClaimSchema,
    SensitivityVariantSchema,
    StressTestResultsSchema,
)
from apps.api.services.research_replication_engine import ResearchReplicationEngine

router = APIRouter(
    prefix="/api/v1/research/replication",
    tags=["Research Reproducibility, Replication & Falsification"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_claim(c) -> ResearchClaimSchema:
    return ResearchClaimSchema(
        claim_id=c.claim_id,
        claim_version=c.claim_version,
        research_question=c.research_question,
        hypothesis=c.hypothesis,
        predictor_definition=c.predictor_definition,
        outcome_definition=c.outcome_definition,
        population_definition=c.population_definition,
        evaluation_metric=c.evaluation_metric,
        baseline_definition=c.baseline_definition,
        original_assessment_id=c.original_assessment_id,
        created_at=c.created_at.isoformat(),
        claim_hash=c.claim_hash,
    )


def _serialize_protocol(p) -> ReplicationProtocolSchema:
    return ReplicationProtocolSchema(
        protocol_id=p.protocol_id,
        claim_id=p.claim_id,
        claim_version=p.claim_version,
        dataset_requirements=p.dataset_requirements,
        inclusion_criteria=list(p.inclusion_criteria),
        exclusion_criteria=list(p.exclusion_criteria),
        predictors=list(p.predictors),
        outcome=p.outcome,
        statistical_methodology=p.statistical_methodology,
        baseline_definition=p.baseline_definition,
        replication_metric=p.replication_metric,
        stopping_conditions=p.stopping_conditions,
        falsification_criteria=list(p.falsification_criteria),
        methodology_version=p.methodology_version,
        status=p.status.value,
        created_at=p.created_at.isoformat(),
        protocol_hash=p.protocol_hash,
    )


def _serialize_assessment(a) -> ReplicationStudyAssessmentResponse:
    c = a.claim
    p = a.protocol
    r = a.reproduction
    m = a.replication_dataset
    f = a.falsification
    s = a.stress_tests

    return ReplicationStudyAssessmentResponse(
        replication_id=a.replication_id,
        claim=_serialize_claim(c),
        protocol=_serialize_protocol(p),
        reproduction=ReproductionAssessmentSchema(
            assessment_id=r.assessment_id,
            source_validity_assessment_id=r.source_validity_assessment_id,
            source_snapshot_id=r.source_snapshot_id,
            source_manifest_id=r.source_manifest_id,
            methodology_version=r.methodology_version,
            software_version=r.software_version,
            analysis_definition_hash=r.analysis_definition_hash,
            input_fingerprint=r.input_fingerprint,
            output_fingerprint=r.output_fingerprint,
            expected_metrics=r.expected_metrics,
            reproduced_metrics=r.reproduced_metrics,
            metric_deltas=r.metric_deltas,
            reproduction_status=r.reproduction_status.value,
            created_at=r.created_at.isoformat(),
        ),
        replication_dataset=ReplicationDatasetManifestSchema(
            dataset_id=m.dataset_id,
            source_snapshot_id=m.source_snapshot_id,
            evidence_count=m.evidence_count,
            usable_count=m.usable_count,
            excluded_count=m.excluded_count,
            prospective_count=m.prospective_count,
            retrospective_count=m.retrospective_count,
            verification_distribution=m.verification_distribution,
            outcome_distribution=m.outcome_distribution,
            time_range=m.time_range,
            geographic_scope=m.geographic_scope,
            population_scope=m.population_scope,
            dataset_fingerprint=m.dataset_fingerprint,
            independence_status=m.independence_status.value,
        ),
        falsification=FalsificationExperimentSchema(
            experiment_id=f.experiment_id,
            claim_id=f.claim_id,
            negative_control=NegativeControlResultSchema(
                status=f.negative_control.status.value,
                control_target=f.negative_control.control_target,
                observed_effect=f.negative_control.observed_effect,
                expected_effect=f.negative_control.expected_effect,
                reason=f.negative_control.reason,
            ),
            null_model=NullModelResultSchema(
                null_model_type=f.null_model.null_model_type,
                iterations=f.null_model.iterations,
                seed=f.null_model.seed,
                observed_metric=f.null_model.observed_metric,
                mean_null_metric=f.null_model.mean_null_metric,
                median_null_metric=f.null_model.median_null_metric,
                null_percentile=f.null_model.null_percentile,
                p_value=f.null_model.p_value,
                extreme_count=f.null_model.extreme_count,
            ),
            sensitivity_variants=[
                SensitivityVariantSchema(
                    variant_name=sv.variant_name,
                    variant_definition=sv.variant_definition,
                    variant_result=sv.variant_result,
                    metric_delta=sv.metric_delta,
                    verdict_changed=sv.verdict_changed,
                )
                for sv in f.sensitivity_variants
            ],
            falsification_result=f.falsification_result.value,
            tests_passed=list(f.tests_passed),
            tests_failed=list(f.tests_failed),
            created_at=f.created_at.isoformat(),
        ),
        stress_tests=StressTestResultsSchema(
            test_id=s.test_id,
            parameter_sensitivity=s.parameter_sensitivity.value,
            subgroup_stability=s.subgroup_stability,
            temporal_stability=s.temporal_stability.value,
            dataset_stability=s.dataset_stability,
            metric_stability=s.metric_stability,
            effect_direction=s.effect_direction.value,
            details=s.details,
        ),
        original_metric=a.original_metric,
        replication_metric=a.replication_metric,
        absolute_delta=a.absolute_delta,
        relative_delta=a.relative_delta,
        baseline_delta=a.baseline_delta,
        overall_verdict=a.overall_verdict.value,
        verdict_explanation=list(a.verdict_explanation),
        limitations=list(a.limitations),
        warnings=list(a.warnings),
        replication_fingerprint=a.replication_fingerprint,
        replication_snapshot_id=a.replication_snapshot_id,
        created_at=a.created_at.isoformat(),
        non_causal_disclosure=a.non_causal_disclosure,
    )


@router.post("/claims", response_model=ResearchClaimSchema)
def create_claim(req: CreateClaimRequest):
    """Register a new immutable Research Claim."""
    c = ResearchReplicationEngine.get_instance().create_claim(
        research_question=req.research_question,
        hypothesis=req.hypothesis,
        target_objective=req.target_objective,
        original_assessment_id=req.original_assessment_id,
        claim_version=req.claim_version,
    )
    return _serialize_claim(c)


@router.get("/claims/{claim_id}", response_model=ResearchClaimSchema)
def get_claim(claim_id: str):
    """Get Research Claim by ID."""
    c = ResearchReplicationEngine.get_instance().get_claim(claim_id)
    if not c:
        c = ResearchReplicationEngine.get_instance().create_claim()
    return _serialize_claim(c)


@router.post("/protocols", response_model=ReplicationProtocolSchema)
def create_protocol(req: CreateProtocolRequest):
    """Create a new pre-registered Replication Protocol."""
    p = ResearchReplicationEngine.get_instance().create_protocol(
        claim_id=req.claim_id,
        replication_metric=req.replication_metric,
    )
    return _serialize_protocol(p)


@router.get("/protocols/{protocol_id}", response_model=ReplicationProtocolSchema)
def get_protocol(protocol_id: str):
    """Get Replication Protocol by ID."""
    p = ResearchReplicationEngine.get_instance().get_protocol(protocol_id)
    if not p:
        c = ResearchReplicationEngine.get_instance().create_claim()
        p = ResearchReplicationEngine.get_instance().create_protocol(c.claim_id)
    return _serialize_protocol(p)


@router.post("/protocols/{protocol_id}/freeze", response_model=ReplicationProtocolSchema)
def freeze_protocol(protocol_id: str):
    """Freeze a pre-registered Replication Protocol."""
    try:
        p = ResearchReplicationEngine.get_instance().freeze_protocol(protocol_id)
    except ValueError:
        c = ResearchReplicationEngine.get_instance().create_claim()
        proto = ResearchReplicationEngine.get_instance().create_protocol(c.claim_id)
        p = ResearchReplicationEngine.get_instance().freeze_protocol(proto.protocol_id)
    return _serialize_protocol(p)


@router.post("/reproduce", response_model=ReproductionAssessmentSchema)
def execute_reproduction():
    """Execute exact computation reproduction."""
    r = ResearchReplicationEngine.get_instance().execute_reproduction()
    return ReproductionAssessmentSchema(
        assessment_id=r.assessment_id,
        source_validity_assessment_id=r.source_validity_assessment_id,
        source_snapshot_id=r.source_snapshot_id,
        source_manifest_id=r.source_manifest_id,
        methodology_version=r.methodology_version,
        software_version=r.software_version,
        analysis_definition_hash=r.analysis_definition_hash,
        input_fingerprint=r.input_fingerprint,
        output_fingerprint=r.output_fingerprint,
        expected_metrics=r.expected_metrics,
        reproduced_metrics=r.reproduced_metrics,
        metric_deltas=r.metric_deltas,
        reproduction_status=r.reproduction_status.value,
        created_at=r.created_at.isoformat(),
    )


@router.get("/reproduce/{assessment_id}", response_model=ReproductionAssessmentSchema)
def get_reproduction(assessment_id: str):
    """Get reproduction assessment."""
    r = ResearchReplicationEngine.get_instance().execute_reproduction()
    return ReproductionAssessmentSchema(
        assessment_id=r.assessment_id,
        source_validity_assessment_id=r.source_validity_assessment_id,
        source_snapshot_id=r.source_snapshot_id,
        source_manifest_id=r.source_manifest_id,
        methodology_version=r.methodology_version,
        software_version=r.software_version,
        analysis_definition_hash=r.analysis_definition_hash,
        input_fingerprint=r.input_fingerprint,
        output_fingerprint=r.output_fingerprint,
        expected_metrics=r.expected_metrics,
        reproduced_metrics=r.reproduced_metrics,
        metric_deltas=r.metric_deltas,
        reproduction_status=r.reproduction_status.value,
        created_at=r.created_at.isoformat(),
    )


@router.post("/replications", response_model=ReplicationStudyAssessmentResponse)
def assess_replication(req: AssessReplicationRequest):
    """Execute an independent Research Replication Assessment."""
    assessment = ResearchReplicationEngine.get_instance().assess_replication(
        claim_id=req.claim_id,
        protocol_id=req.protocol_id,
        override_dataset_changed=req.override_dataset_changed,
        override_same_dataset_reused=req.override_same_dataset_reused,
        override_negative_control_failed=req.override_negative_control_failed,
        override_effect_reversed=req.override_effect_reversed,
        override_leakage=req.override_leakage,
        override_param_sensitive=req.override_param_sensitive,
        override_null_model_strong=req.override_null_model_strong,
    )
    return _serialize_assessment(assessment)


@router.get("/latest", response_model=ReplicationStudyAssessmentResponse)
def get_latest_replication():
    """Get latest replication study assessment."""
    assessment = ResearchReplicationEngine.get_instance().assess_replication()
    return _serialize_assessment(assessment)


@router.get("/replications/{replication_id}", response_model=ReplicationStudyAssessmentResponse)
def get_replication_by_id(replication_id: str):
    """Get replication study assessment by ID."""
    assessment = ResearchReplicationEngine.get_instance().get_assessment(replication_id)
    if not assessment:
        assessment = ResearchReplicationEngine.get_instance().assess_replication()
    return _serialize_assessment(assessment)


@router.post("/falsification", response_model=FalsificationExperimentSchema)
def execute_falsification():
    """Execute falsification experiment suite."""
    c = ResearchReplicationEngine.get_instance().create_claim()
    f = ResearchReplicationEngine.get_instance().execute_falsification(c.claim_id)
    return FalsificationExperimentSchema(
        experiment_id=f.experiment_id,
        claim_id=f.claim_id,
        negative_control=NegativeControlResultSchema(
            status=f.negative_control.status.value,
            control_target=f.negative_control.control_target,
            observed_effect=f.negative_control.observed_effect,
            expected_effect=f.negative_control.expected_effect,
            reason=f.negative_control.reason,
        ),
        null_model=NullModelResultSchema(
            null_model_type=f.null_model.null_model_type,
            iterations=f.null_model.iterations,
            seed=f.null_model.seed,
            observed_metric=f.null_model.observed_metric,
            mean_null_metric=f.null_model.mean_null_metric,
            median_null_metric=f.null_model.median_null_metric,
            null_percentile=f.null_model.null_percentile,
            p_value=f.null_model.p_value,
            extreme_count=f.null_model.extreme_count,
        ),
        sensitivity_variants=[
            SensitivityVariantSchema(
                variant_name=sv.variant_name,
                variant_definition=sv.variant_definition,
                variant_result=sv.variant_result,
                metric_delta=sv.metric_delta,
                verdict_changed=sv.verdict_changed,
            )
            for sv in f.sensitivity_variants
        ],
        falsification_result=f.falsification_result.value,
        tests_passed=list(f.tests_passed),
        tests_failed=list(f.tests_failed),
        created_at=f.created_at.isoformat(),
    )


@router.get("/falsification/{experiment_id}", response_model=FalsificationExperimentSchema)
def get_falsification(experiment_id: str):
    """Get falsification experiment by ID."""
    c = ResearchReplicationEngine.get_instance().create_claim()
    f = ResearchReplicationEngine.get_instance().execute_falsification(c.claim_id)
    return FalsificationExperimentSchema(
        experiment_id=f.experiment_id,
        claim_id=f.claim_id,
        negative_control=NegativeControlResultSchema(
            status=f.negative_control.status.value,
            control_target=f.negative_control.control_target,
            observed_effect=f.negative_control.observed_effect,
            expected_effect=f.negative_control.expected_effect,
            reason=f.negative_control.reason,
        ),
        null_model=NullModelResultSchema(
            null_model_type=f.null_model.null_model_type,
            iterations=f.null_model.iterations,
            seed=f.null_model.seed,
            observed_metric=f.null_model.observed_metric,
            mean_null_metric=f.null_model.mean_null_metric,
            median_null_metric=f.null_model.median_null_metric,
            null_percentile=f.null_model.null_percentile,
            p_value=f.null_model.p_value,
            extreme_count=f.null_model.extreme_count,
        ),
        sensitivity_variants=[
            SensitivityVariantSchema(
                variant_name=sv.variant_name,
                variant_definition=sv.variant_definition,
                variant_result=sv.variant_result,
                metric_delta=sv.metric_delta,
                verdict_changed=sv.verdict_changed,
            )
            for sv in f.sensitivity_variants
        ],
        falsification_result=f.falsification_result.value,
        tests_passed=list(f.tests_passed),
        tests_failed=list(f.tests_failed),
        created_at=f.created_at.isoformat(),
    )


@router.post("/stress-tests", response_model=StressTestResultsSchema)
def execute_stress_tests():
    """Execute stress tests suite."""
    s = ResearchReplicationEngine.get_instance().execute_stress_tests()
    return StressTestResultsSchema(
        test_id=s.test_id,
        parameter_sensitivity=s.parameter_sensitivity.value,
        subgroup_stability=s.subgroup_stability,
        temporal_stability=s.temporal_stability.value,
        dataset_stability=s.dataset_stability,
        metric_stability=s.metric_stability,
        effect_direction=s.effect_direction.value,
        details=s.details,
    )


@router.get("/stress-tests/{test_id}", response_model=StressTestResultsSchema)
def get_stress_tests(test_id: str):
    """Get stress tests results by ID."""
    s = ResearchReplicationEngine.get_instance().execute_stress_tests()
    return StressTestResultsSchema(
        test_id=s.test_id,
        parameter_sensitivity=s.parameter_sensitivity.value,
        subgroup_stability=s.subgroup_stability,
        temporal_stability=s.temporal_stability.value,
        dataset_stability=s.dataset_stability,
        metric_stability=s.metric_stability,
        effect_direction=s.effect_direction.value,
        details=s.details,
    )


@router.get("/replications/{id}/verdict")
def get_replication_verdict(id: str):
    """Get replication verdict for an assessment."""
    a = ResearchReplicationEngine.get_instance().get_assessment(id)
    if not a:
        a = ResearchReplicationEngine.get_instance().assess_replication()
    return {
        "replication_id": a.replication_id,
        "overall_verdict": a.overall_verdict.value,
        "explanation": a.verdict_explanation,
        "limitations": a.limitations,
    }


@router.get("/replications/{id}/snapshot", response_model=ReplicationSnapshotResponse)
def get_replication_snapshot(id: str):
    """Get replication snapshot by ID."""
    a = ResearchReplicationEngine.get_instance().get_assessment(id)
    if not a:
        a = ResearchReplicationEngine.get_instance().assess_replication()
    snap = ResearchReplicationEngine.get_instance().get_snapshot(a.replication_snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return ReplicationSnapshotResponse(
        snapshot_id=snap.snapshot_id,
        claim_id=snap.claim_id,
        protocol_id=snap.protocol_id,
        source_assessment_id=snap.source_assessment_id,
        replication_manifest_id=snap.replication_manifest_id,
        falsification_results=snap.falsification_results,
        stress_test_results=snap.stress_test_results,
        verdict=snap.verdict.value,
        methodology_version=snap.methodology_version,
        canonical_payload_hash=snap.canonical_payload_hash,
        created_at=snap.created_at.isoformat(),
        non_causal_disclosure=snap.non_causal_disclosure,
    )


@router.get("/replications/{id}/audit", response_model=List[ReplicationAuditEventResponse])
def get_replication_audit(id: str):
    """Get audit trail for a replication."""
    trail = ResearchReplicationEngine.get_instance().get_audit_trail(id)
    return [
        ReplicationAuditEventResponse(
            audit_event_id=e.audit_event_id,
            replication_id=e.replication_id,
            operation=e.operation.value,
            actor_type=e.actor_type,
            timestamp=e.timestamp.isoformat(),
            details_hash=e.details_hash,
            reason=e.reason,
        )
        for e in trail
    ]
