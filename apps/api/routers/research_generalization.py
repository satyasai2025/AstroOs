"""
AstroOS — Research External Validity, Generalization & Domain Transportability Router (Priority 35)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.research_generalization import (
    AssessGeneralizationRequest,
    DistributionShiftAnalysisSchema,
    DomainBoundarySchema,
    ExternalDomainSchema,
    FailureRegionSchema,
    GeneralizationAssessmentResponse,
    GeneralizationAuditEventResponse,
    GeneralizationMatrixCellSchema,
    GeneralizationSnapshotResponse,
    TransportabilityAssessmentSchema,
)
from apps.api.services.research_generalization_engine import ResearchGeneralizationEngine

router = APIRouter(
    prefix="/api/v1/research/generalization",
    tags=["Research External Validity & Domain Transportability"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_domain(d) -> ExternalDomainSchema:
    return ExternalDomainSchema(
        domain_id=d.domain_id,
        domain_name=d.domain_name,
        is_source=d.is_source,
        population_dimension=d.population_dimension,
        time_dimension=d.time_dimension,
        dataset_dimension=d.dataset_dimension,
        context_dimension=d.context_dimension,
        created_at=d.created_at.isoformat(),
    )


def _serialize_assessment(a) -> GeneralizationAssessmentResponse:
    s_dom = a.source_domain
    t_doms = a.target_domains
    trans = a.transportability

    return GeneralizationAssessmentResponse(
        assessment_id=a.assessment_id,
        target_objective=a.target_objective,
        source_domain=_serialize_domain(s_dom),
        target_domains=[_serialize_domain(td) for td in t_doms],
        source_replication_id=a.source_replication_id,
        methodology_version=a.methodology_version,
        shift_analyses=[
            DistributionShiftAnalysisSchema(
                source_domain_id=sa.source_domain_id,
                target_domain_id=sa.target_domain_id,
                shift_type=sa.shift_type.value,
                feature_drift_score=sa.feature_drift_score,
                outcome_drift_score=sa.outcome_drift_score,
                baseline_drift_score=sa.baseline_drift_score,
                is_significant_shift=sa.is_significant_shift,
                details=sa.details,
            )
            for sa in a.shift_analyses
        ],
        boundaries=[
            DomainBoundarySchema(
                boundary_id=b.boundary_id,
                dimension_name=b.dimension_name,
                valid_range=b.valid_range,
                failure_threshold=b.failure_threshold,
                degradation_rate=b.degradation_rate,
            )
            for b in a.boundaries
        ],
        failure_regions=[
            FailureRegionSchema(
                region_id=fr.region_id,
                region_type=fr.region_type.value,
                affected_dimension=fr.affected_dimension,
                trigger_condition=fr.trigger_condition,
                severity=fr.severity,
            )
            for fr in a.failure_regions
        ],
        matrix_cells=[
            GeneralizationMatrixCellSchema(
                source_domain_id=mc.source_domain_id,
                target_domain_id=mc.target_domain_id,
                target_domain_name=mc.target_domain_name,
                status=mc.status.value,
                target_metric=mc.target_metric,
                target_baseline=mc.target_baseline,
                baseline_lift=mc.baseline_lift,
                is_baseline_superior=mc.is_baseline_superior,
            )
            for mc in a.matrix_cells
        ],
        transportability=TransportabilityAssessmentSchema(
            source_domain_id=trans.source_domain_id,
            target_domain_id=trans.target_domain_id,
            status=trans.status.value,
            transfer_loss=trans.transfer_loss,
            reasons=list(trans.reasons),
        ),
        overall_verdict=a.overall_verdict.value,
        verdict_explanation=list(a.verdict_explanation),
        limitations=list(a.limitations),
        warnings=list(a.warnings),
        generalization_fingerprint=a.generalization_fingerprint,
        generalization_snapshot_id=a.generalization_snapshot_id,
        created_at=a.created_at.isoformat(),
        non_causal_disclosure=a.non_causal_disclosure,
    )


@router.post("/domains", response_model=ExternalDomainSchema)
def register_domain(
    domain_name: str = Query("Target Domain"),
    is_source: bool = Query(False),
    population_dimension: str = Query("EUROPEAN_SUBARRAY_25_60"),
    time_dimension: str = Query("2020_2025_RECENT"),
    dataset_dimension: str = Query("PROSPECTIVE_MOBILE_APP"),
    context_dimension: str = Query("WESTERN_EQUAL_HOUSES"),
):
    """Register Source or Target domain dimensions."""
    d = ResearchGeneralizationEngine.get_instance().register_domain(
        domain_name=domain_name,
        is_source=is_source,
        population_dimension=population_dimension,
        time_dimension=time_dimension,
        dataset_dimension=dataset_dimension,
        context_dimension=context_dimension,
    )
    return _serialize_domain(d)


@router.post("/assess", response_model=GeneralizationAssessmentResponse)
def assess_generalization(req: AssessGeneralizationRequest):
    """Execute an independent External Validity & Domain Transportability assessment."""
    assessment = ResearchGeneralizationEngine.get_instance().assess_generalization(
        target_objective=req.target_objective,
        source_replication_id=req.source_replication_id,
        override_inferior_target=req.override_inferior_target,
        override_direction_reversal=req.override_direction_reversal,
        override_performance_collapse=req.override_performance_collapse,
        override_severe_shift=req.override_severe_shift,
        override_insufficient_sample=req.override_insufficient_sample,
    )
    return _serialize_assessment(assessment)


@router.get("/latest", response_model=GeneralizationAssessmentResponse)
def get_latest_generalization():
    """Get latest generalization assessment."""
    assessment = ResearchGeneralizationEngine.get_instance().assess_generalization()
    return _serialize_assessment(assessment)


@router.get("/assess/{assessment_id}", response_model=GeneralizationAssessmentResponse)
def get_assessment_by_id(assessment_id: str):
    """Get assessment by ID."""
    assessment = ResearchGeneralizationEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchGeneralizationEngine.get_instance().assess_generalization()
    return _serialize_assessment(assessment)


@router.get("/assess/{assessment_id}/matrix", response_model=List[GeneralizationMatrixCellSchema])
def get_assessment_matrix(assessment_id: str):
    """Get generalization matrix cells."""
    assessment = ResearchGeneralizationEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchGeneralizationEngine.get_instance().assess_generalization()
    return [
        GeneralizationMatrixCellSchema(
            source_domain_id=mc.source_domain_id,
            target_domain_id=mc.target_domain_id,
            target_domain_name=mc.target_domain_name,
            status=mc.status.value,
            target_metric=mc.target_metric,
            target_baseline=mc.target_baseline,
            baseline_lift=mc.baseline_lift,
            is_baseline_superior=mc.is_baseline_superior,
        )
        for mc in assessment.matrix_cells
    ]


@router.get("/assess/{assessment_id}/shift", response_model=List[DistributionShiftAnalysisSchema])
def get_assessment_shift(assessment_id: str):
    """Get distribution shift analyses."""
    assessment = ResearchGeneralizationEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchGeneralizationEngine.get_instance().assess_generalization()
    return [
        DistributionShiftAnalysisSchema(
            source_domain_id=sa.source_domain_id,
            target_domain_id=sa.target_domain_id,
            shift_type=sa.shift_type.value,
            feature_drift_score=sa.feature_drift_score,
            outcome_drift_score=sa.outcome_drift_score,
            baseline_drift_score=sa.baseline_drift_score,
            is_significant_shift=sa.is_significant_shift,
            details=sa.details,
        )
        for sa in assessment.shift_analyses
    ]


@router.get("/assess/{assessment_id}/boundaries")
def get_assessment_boundaries(assessment_id: str):
    """Get domain boundaries and failure regions."""
    assessment = ResearchGeneralizationEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchGeneralizationEngine.get_instance().assess_generalization()
    return {
        "boundaries": [
            DomainBoundarySchema(
                boundary_id=b.boundary_id,
                dimension_name=b.dimension_name,
                valid_range=b.valid_range,
                failure_threshold=b.failure_threshold,
                degradation_rate=b.degradation_rate,
            )
            for b in assessment.boundaries
        ],
        "failure_regions": [
            FailureRegionSchema(
                region_id=fr.region_id,
                region_type=fr.region_type.value,
                affected_dimension=fr.affected_dimension,
                trigger_condition=fr.trigger_condition,
                severity=fr.severity,
            )
            for fr in assessment.failure_regions
        ],
    }


@router.get("/assess/{assessment_id}/snapshot", response_model=GeneralizationSnapshotResponse)
def get_assessment_snapshot(assessment_id: str):
    """Get generalization snapshot."""
    assessment = ResearchGeneralizationEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchGeneralizationEngine.get_instance().assess_generalization()
    snap = ResearchGeneralizationEngine.get_instance().get_snapshot(assessment.generalization_snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return GeneralizationSnapshotResponse(
        snapshot_id=snap.snapshot_id,
        assessment_id=snap.assessment_id,
        source_replication_id=snap.source_replication_id,
        methodology_version=snap.methodology_version,
        canonical_payload_hash=snap.canonical_payload_hash,
        created_at=snap.created_at.isoformat(),
        non_causal_disclosure=snap.non_causal_disclosure,
    )


@router.get("/assess/{assessment_id}/audit", response_model=List[GeneralizationAuditEventResponse])
def get_assessment_audit(assessment_id: str):
    """Get audit trail for an assessment."""
    trail = ResearchGeneralizationEngine.get_instance().get_audit_trail(assessment_id)
    return [
        GeneralizationAuditEventResponse(
            audit_event_id=e.audit_event_id,
            assessment_id=e.assessment_id,
            operation=e.operation.value,
            actor_type=e.actor_type,
            timestamp=e.timestamp.isoformat(),
            details_hash=e.details_hash,
            reason=e.reason,
        )
        for e in trail
    ]
