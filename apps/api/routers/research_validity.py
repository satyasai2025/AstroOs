"""
AstroOS — Research Validity Router (Priority 33)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.research_validity import (
    AssessValidityRequest,
    BaselineComparisonSchema,
    BiasDiagnosticSchema,
    ConfidenceIntervalSchema,
    DatasetManifestSchema,
    EffectSizeSchema,
    LeakageDiagnosticSchema,
    StatisticalResultSchema,
    TemporalIntegritySchema,
    ValidityAssessmentResponse,
    ValidityAuditEventResponse,
    ValiditySnapshotResponse,
)
from apps.api.services.research_validity_engine import ResearchValidityEngine

router = APIRouter(
    prefix="/api/v1/research/validity",
    tags=["Research Validity & Statistical Integrity"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_assessment(a) -> ValidityAssessmentResponse:
    m = a.dataset_manifest
    b = a.baseline_comparison

    return ValidityAssessmentResponse(
        assessment_id=a.assessment_id,
        target_objective=a.target_objective,
        source_snapshot_id=a.source_snapshot_id,
        methodology_version=a.methodology_version,
        dataset_manifest=DatasetManifestSchema(
            manifest_id=m.manifest_id,
            source_snapshot_id=m.source_snapshot_id,
            total_observations=m.total_observations,
            usable_observations=m.usable_observations,
            excluded_observations=m.excluded_observations,
            missing_observations=m.missing_observations,
            duplicate_count=m.duplicate_count,
            prospective_count=m.prospective_count,
            retrospective_count=m.retrospective_count,
            unknown_timing_count=m.unknown_timing_count,
            verification_distribution=m.verification_distribution,
            domain_distribution=m.domain_distribution,
            methodology_version=m.methodology_version,
            manifest_hash=m.manifest_hash,
        ),
        sample_adequacy=a.sample_adequacy.value,
        missing_data_classification=a.missing_data_classification.value,
        temporal_integrity=TemporalIntegritySchema(
            status=a.temporal_integrity.status.value,
            predictions_registered_before_outcome=a.temporal_integrity.predictions_registered_before_outcome,
            look_ahead_risk_detected=a.temporal_integrity.look_ahead_risk_detected,
            details=a.temporal_integrity.details,
        ),
        leakage_diagnostic=LeakageDiagnosticSchema(
            status=a.leakage_diagnostic.status.value,
            outcome_derived_features_detected=a.leakage_diagnostic.outcome_derived_features_detected,
            future_timestamps_detected=a.leakage_diagnostic.future_timestamps_detected,
            reasons=list(a.leakage_diagnostic.reasons),
        ),
        selection_bias_diagnostic=BiasDiagnosticSchema(
            diagnostic_name=a.selection_bias_diagnostic.diagnostic_name,
            risk_level=a.selection_bias_diagnostic.risk_level,
            reason=a.selection_bias_diagnostic.reason,
            evidence_details=a.selection_bias_diagnostic.evidence_details,
        ),
        cherry_picking_diagnostic=BiasDiagnosticSchema(
            diagnostic_name=a.cherry_picking_diagnostic.diagnostic_name,
            risk_level=a.cherry_picking_diagnostic.risk_level,
            reason=a.cherry_picking_diagnostic.reason,
            evidence_details=a.cherry_picking_diagnostic.evidence_details,
        ),
        baseline_comparison=BaselineComparisonSchema(
            metric_name=b.metric_name,
            model_metric=b.model_metric,
            majority_baseline=b.majority_baseline,
            random_baseline=b.random_baseline,
            permutation_baseline=b.permutation_baseline,
            absolute_difference=b.absolute_difference,
            relative_difference=b.relative_difference,
            is_superior_to_majority=b.is_superior_to_majority,
            is_superior_to_random=b.is_superior_to_random,
        ),
        statistical_results=[
            StatisticalResultSchema(
                metric_name=s.metric_name,
                value=s.value,
                method=s.method,
                sample_size=s.sample_size,
                confidence_interval=ConfidenceIntervalSchema(
                    estimate=s.confidence_interval.estimate,
                    confidence_level=s.confidence_interval.confidence_level,
                    lower_bound=s.confidence_interval.lower_bound,
                    upper_bound=s.confidence_interval.upper_bound,
                    method=s.confidence_interval.method,
                ) if s.confidence_interval else None,
                p_value=s.p_value,
                adjusted_p_value=s.adjusted_p_value,
                multiple_testing_method=s.multiple_testing_method.value,
            )
            for s in a.statistical_results
        ],
        effect_sizes=[
            EffectSizeSchema(
                metric_name=e.metric_name,
                value=e.value,
                interpretation=e.interpretation,
                is_practically_meaningful=e.is_practically_meaningful,
            )
            for e in a.effect_sizes
        ],
        overall_verdict=a.overall_verdict.value,
        verdict_explanation=list(a.verdict_explanation),
        limitations=list(a.limitations),
        warnings=list(a.warnings),
        analysis_fingerprint=a.analysis_fingerprint,
        validity_snapshot_id=a.validity_snapshot_id,
        created_at=a.created_at.isoformat(),
        non_causal_disclosure=a.non_causal_disclosure,
    )


@router.post("/assess", response_model=ValidityAssessmentResponse)
def assess_validity(req: AssessValidityRequest):
    """Execute an independent Research Validity & Statistical Integrity assessment."""
    assessment = ResearchValidityEngine.get_instance().assess_validity(
        target_objective=req.target_objective,
        source_snapshot_id=req.source_snapshot_id,
        override_prediction_after_outcome=req.override_prediction_after_outcome,
        override_outcome_features_in_predictor=req.override_outcome_features_in_predictor,
        override_sample_size=req.override_sample_size,
        override_model_accuracy=req.override_model_accuracy,
    )
    return _serialize_assessment(assessment)


@router.get("/latest", response_model=ValidityAssessmentResponse)
def get_latest_validity_assessment(target_objective: str = Query("marriage")):
    """Get latest validity assessment."""
    assessment = ResearchValidityEngine.get_instance().assess_validity(target_objective=target_objective)
    return _serialize_assessment(assessment)


@router.get("/assess/{assessment_id}", response_model=ValidityAssessmentResponse)
def get_assessment_by_id(assessment_id: str):
    """Get assessment by ID."""
    assessment = ResearchValidityEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchValidityEngine.get_instance().assess_validity()
    return _serialize_assessment(assessment)


@router.get("/assess/{assessment_id}/diagnostics")
def get_assessment_diagnostics(assessment_id: str):
    """Get bias, leakage, and temporal diagnostics for an assessment."""
    assessment = ResearchValidityEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchValidityEngine.get_instance().assess_validity()
    return {
        "assessment_id": assessment.assessment_id,
        "temporal_integrity": assessment.temporal_integrity,
        "leakage_diagnostic": assessment.leakage_diagnostic,
        "selection_bias": assessment.selection_bias_diagnostic,
        "cherry_picking": assessment.cherry_picking_diagnostic,
    }


@router.get("/assess/{assessment_id}/statistics")
def get_assessment_statistics(assessment_id: str):
    """Get statistical metrics, effect sizes, and baseline comparisons."""
    assessment = ResearchValidityEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchValidityEngine.get_instance().assess_validity()
    return {
        "assessment_id": assessment.assessment_id,
        "baseline_comparison": assessment.baseline_comparison,
        "statistical_results": assessment.statistical_results,
        "effect_sizes": assessment.effect_sizes,
    }


@router.get("/assess/{assessment_id}/manifest", response_model=DatasetManifestSchema)
def get_assessment_manifest(assessment_id: str):
    """Get dataset manifest for an assessment."""
    assessment = ResearchValidityEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchValidityEngine.get_instance().assess_validity()
    m = assessment.dataset_manifest
    return DatasetManifestSchema(
        manifest_id=m.manifest_id,
        source_snapshot_id=m.source_snapshot_id,
        total_observations=m.total_observations,
        usable_observations=m.usable_observations,
        excluded_observations=m.excluded_observations,
        missing_observations=m.missing_observations,
        duplicate_count=m.duplicate_count,
        prospective_count=m.prospective_count,
        retrospective_count=m.retrospective_count,
        unknown_timing_count=m.unknown_timing_count,
        verification_distribution=m.verification_distribution,
        domain_distribution=m.domain_distribution,
        methodology_version=m.methodology_version,
        manifest_hash=m.manifest_hash,
    )


@router.get("/assess/{assessment_id}/snapshot", response_model=ValiditySnapshotResponse)
def get_assessment_snapshot(assessment_id: str):
    """Get validity snapshot for an assessment."""
    assessment = ResearchValidityEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchValidityEngine.get_instance().assess_validity()
    snap = ResearchValidityEngine.get_instance().get_snapshot(assessment.validity_snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return ValiditySnapshotResponse(
        snapshot_id=snap.snapshot_id,
        assessment_id=snap.assessment_id,
        source_snapshot_id=snap.source_snapshot_id,
        methodology_version=snap.methodology_version,
        canonical_payload_hash=snap.canonical_payload_hash,
        created_at=snap.created_at.isoformat(),
        non_causal_disclosure=snap.non_causal_disclosure,
    )


@router.get("/assess/{assessment_id}/audit", response_model=List[ValidityAuditEventResponse])
def get_assessment_audit(assessment_id: str):
    """Get audit trail for an assessment."""
    trail = ResearchValidityEngine.get_instance().get_audit_trail(assessment_id)
    return [
        ValidityAuditEventResponse(
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


@router.post("/assess/{assessment_id}/recompute", response_model=ValidityAssessmentResponse)
def recompute_assessment(assessment_id: str):
    """Recompute assessment deterministically."""
    assessment = ResearchValidityEngine.get_instance().assess_validity()
    return _serialize_assessment(assessment)
