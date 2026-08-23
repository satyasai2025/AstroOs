"""
AstroOS — Longitudinal Evidence Synthesis & Research Knowledge State Router (Priority 36)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_knowledge_state import ResearchKnowledgeSnapshot
from apps.api.schemas.research_knowledge_state import (
    KnowledgeStateAuditEventResponse,
    KnowledgeStateSynthesisAssessmentResponse,
    KnowledgeStateTransitionSchema,
    MetaAnalysisResultSchema,
    ResearchKnowledgeSnapshotResponse,
    ResearchKnowledgeStateRecordSchema,
    StudyEvidenceEntrySchema,
    SynthesizeKnowledgeStateRequest,
)
from apps.api.services.research_knowledge_state_engine import ResearchKnowledgeStateEngine

router = APIRouter(
    prefix="/api/v1/research/knowledge-state",
    tags=["Longitudinal Evidence Synthesis & Research Knowledge State"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_record(r) -> ResearchKnowledgeStateRecordSchema:
    ma = r.meta_analysis
    return ResearchKnowledgeStateRecordSchema(
        state_id=r.state_id,
        state_version=r.state_version,
        target_objective=r.target_objective,
        current_state=r.current_state.value,
        evidence_grade=r.evidence_grade.value,
        certainty_score=r.certainty_score,
        meta_analysis=MetaAnalysisResultSchema(
            pooled_effect_size=ma.pooled_effect_size,
            pooled_variance=ma.pooled_variance,
            confidence_interval=list(ma.confidence_interval),
            i_squared_heterogeneity=ma.i_squared_heterogeneity,
            heterogeneity_level=ma.heterogeneity_level.value,
            tau_squared=ma.tau_squared,
            p_value=ma.p_value,
            total_samples=ma.total_samples,
            forest_plot_data=ma.forest_plot_data,
        ),
        accumulated_studies=[
            StudyEvidenceEntrySchema(
                study_id=s.study_id,
                study_type=s.study_type,
                title=s.title,
                sample_size=s.sample_size,
                metric_name=s.metric_name,
                observed_metric=s.observed_metric,
                variance=s.variance,
                is_prospective=s.is_prospective,
                is_independent=s.is_independent,
                weight=s.weight,
            )
            for s in r.accumulated_studies
        ],
        transitions=[
            KnowledgeStateTransitionSchema(
                transition_id=t.transition_id,
                from_state=t.from_state.value,
                to_state=t.to_state.value,
                trigger_study_id=t.trigger_study_id,
                reason=t.reason,
                timestamp=t.timestamp.isoformat(),
            )
            for t in r.transitions
        ],
        superseded_state_id=r.superseded_state_id,
        created_at=r.created_at.isoformat(),
    )


def _serialize_assessment(a) -> KnowledgeStateSynthesisAssessmentResponse:
    return KnowledgeStateSynthesisAssessmentResponse(
        assessment_id=a.assessment_id,
        knowledge_state=_serialize_record(a.knowledge_state),
        overall_verdict=a.overall_verdict.value,
        verdict_explanation=list(a.verdict_explanation),
        limitations=list(a.limitations),
        warnings=list(a.warnings),
        knowledge_state_fingerprint=a.knowledge_state_fingerprint,
        knowledge_snapshot_id=a.knowledge_snapshot_id,
        created_at=a.created_at.isoformat(),
        non_causal_disclosure=a.non_causal_disclosure,
    )


@router.post("/synthesize", response_model=KnowledgeStateSynthesisAssessmentResponse)
def synthesize_knowledge_state(req: SynthesizeKnowledgeStateRequest):
    """Synthesize longitudinal evidence and update Research Knowledge State."""
    assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state(
        target_objective=req.target_objective,
        superseded_state_id=req.superseded_state_id,
        override_replication_falsified=req.override_replication_falsified,
        override_low_sample=req.override_low_sample,
    )
    return _serialize_assessment(assessment)


@router.get("/latest", response_model=KnowledgeStateSynthesisAssessmentResponse)
def get_latest_knowledge_state():
    """Get latest research knowledge state assessment."""
    assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state()
    return _serialize_assessment(assessment)


@router.get("/synthesize/{assessment_id}", response_model=KnowledgeStateSynthesisAssessmentResponse)
def get_assessment_by_id(assessment_id: str):
    """Get synthesis assessment by ID."""
    assessment = ResearchKnowledgeStateEngine.get_instance().get_assessment(assessment_id)
    if not assessment:
        assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state()
    return _serialize_assessment(assessment)


@router.get("/meta-analysis/{state_id}", response_model=MetaAnalysisResultSchema)
def get_meta_analysis(state_id: str):
    """Get meta-analysis result for a knowledge state."""
    state = ResearchKnowledgeStateEngine.get_instance().get_knowledge_state(state_id)
    if not state:
        assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state()
        state = assessment.knowledge_state
    ma = state.meta_analysis
    return MetaAnalysisResultSchema(
        pooled_effect_size=ma.pooled_effect_size,
        pooled_variance=ma.pooled_variance,
        confidence_interval=list(ma.confidence_interval),
        i_squared_heterogeneity=ma.i_squared_heterogeneity,
        heterogeneity_level=ma.heterogeneity_level.value,
        tau_squared=ma.tau_squared,
        p_value=ma.p_value,
        total_samples=ma.total_samples,
        forest_plot_data=ma.forest_plot_data,
    )


@router.get("/lineage/{state_id}", response_model=List[StudyEvidenceEntrySchema])
def get_evidence_lineage(state_id: str):
    """Get accumulated study evidence lineage."""
    state = ResearchKnowledgeStateEngine.get_instance().get_knowledge_state(state_id)
    if not state:
        assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state()
        state = assessment.knowledge_state
    return [
        StudyEvidenceEntrySchema(
            study_id=s.study_id,
            study_type=s.study_type,
            title=s.title,
            sample_size=s.sample_size,
            metric_name=s.metric_name,
            observed_metric=s.observed_metric,
            variance=s.variance,
            is_prospective=s.is_prospective,
            is_independent=s.is_independent,
            weight=s.weight,
        )
        for s in state.accumulated_studies
    ]


@router.get("/transitions/{state_id}", response_model=List[KnowledgeStateTransitionSchema])
def get_state_transitions(state_id: str):
    """Get knowledge state transitions."""
    state = ResearchKnowledgeStateEngine.get_instance().get_knowledge_state(state_id)
    if not state:
        assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state()
        state = assessment.knowledge_state
    return [
        KnowledgeStateTransitionSchema(
            transition_id=t.transition_id,
            from_state=t.from_state.value,
            to_state=t.to_state.value,
            trigger_study_id=t.trigger_study_id,
            reason=t.reason,
            timestamp=t.timestamp.isoformat(),
        )
        for t in state.transitions
    ]


@router.get("/snapshot/{state_id}", response_model=ResearchKnowledgeSnapshotResponse)
def get_snapshot(state_id: str):
    """Get research knowledge snapshot."""
    state = ResearchKnowledgeStateEngine.get_instance().get_knowledge_state(state_id)
    if not state:
        assessment = ResearchKnowledgeStateEngine.get_instance().synthesize_knowledge_state()
        state = assessment.knowledge_state
    assessment = ResearchKnowledgeStateEngine.get_instance().get_assessment(state_id)
    snap_id = assessment.knowledge_snapshot_id if assessment else f"snap-{state_id}"
    snap = ResearchKnowledgeStateEngine.get_instance().get_snapshot(snap_id)
    if not snap:
        snap = ResearchKnowledgeSnapshot(
            snapshot_id=snap_id,
            state_id=state_id,
            state_version=state.state_version,
            canonical_payload_hash="default_payload_hash",
            created_at=state.created_at,
        )
    return ResearchKnowledgeSnapshotResponse(
        snapshot_id=snap.snapshot_id,
        state_id=snap.state_id,
        state_version=snap.state_version,
        canonical_payload_hash=snap.canonical_payload_hash,
        created_at=snap.created_at.isoformat(),
        non_causal_disclosure=snap.non_causal_disclosure,
    )


@router.get("/audit/{state_id}", response_model=List[KnowledgeStateAuditEventResponse])
def get_audit_trail(state_id: str):
    """Get audit trail for a knowledge state."""
    trail = ResearchKnowledgeStateEngine.get_instance().get_audit_trail(state_id)
    return [
        KnowledgeStateAuditEventResponse(
            audit_event_id=e.audit_event_id,
            state_id=e.state_id,
            operation=e.operation.value,
            actor_type=e.actor_type,
            timestamp=e.timestamp.isoformat(),
            details_hash=e.details_hash,
            reason=e.reason,
        )
        for e in trail
    ]
