"""
AstroOS — Research Evidence Registry Router (Priority 32)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_evidence_registry import (
    ConsentStatus,
    ControlledResearchDomain,
    EvidenceOrigin,
    EvidenceSourceType,
    OutcomeVerificationStatus,
    TimestampPrecision,
)
from apps.api.schemas.research_evidence_registry import (
    CorrectObservationRequest,
    EvidenceAuditEventResponse,
    EvidenceRegistrySnapshotResponse,
    ObservedOutcomeResponse,
    RegisterObservationRequest,
    VerifyObservationRequest,
)
from apps.api.services.research_evidence_registry_engine import ResearchEvidenceRegistryEngine

router = APIRouter(
    prefix="/api/v1/research/evidence",
    tags=["Research Evidence Registry"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_outcome(r) -> ObservedOutcomeResponse:
    return ObservedOutcomeResponse(
        outcome_id=r.outcome_id,
        subject_reference=r.subject_reference,
        domain=r.domain.value,
        event_type=r.event_type,
        event_description=r.event_description,
        event_date=r.event_date,
        event_time=r.event_time,
        event_timezone=r.event_timezone,
        timestamp_precision=r.timestamp_precision.value,
        observation_source_type=r.observation_source_type.value,
        evidence_origin=r.evidence_origin.value,
        verification_status=r.verification_status.value,
        verification_method=r.verification_method,
        verifier_reference=r.verifier_reference,
        evidence_hash=r.evidence_hash,
        source_hash=r.source_hash,
        created_at=r.created_at.isoformat(),
        updated_at=r.updated_at.isoformat(),
        prospective_rule_id=r.prospective_rule_id,
        experiment_id=r.experiment_id,
        p11_snapshot_id=r.p11_snapshot_id,
        provenance_parent=r.provenance_parent,
        consent_status=r.consent_status.value,
        privacy_classification=r.privacy_classification,
        notes=r.notes,
        non_causal_disclosure=r.non_causal_disclosure,
    )


def _serialize_audit(e) -> EvidenceAuditEventResponse:
    return EvidenceAuditEventResponse(
        audit_event_id=e.audit_event_id,
        outcome_id=e.outcome_id,
        operation=e.operation.value,
        previous_hash=e.previous_hash,
        new_hash=e.new_hash,
        actor_type=e.actor_type,
        timestamp=e.timestamp.isoformat(),
        reason=e.reason,
        p11_snapshot_id=e.p11_snapshot_id,
    )


def _serialize_snapshot(s) -> EvidenceRegistrySnapshotResponse:
    return EvidenceRegistrySnapshotResponse(
        snapshot_id=s.snapshot_id,
        record_count=s.record_count,
        verified_record_count=s.verified_record_count,
        rejected_record_count=s.rejected_record_count,
        unverified_record_count=s.unverified_record_count,
        source_distribution=s.source_distribution,
        domain_distribution=s.domain_distribution,
        timestamp_precision_distribution=s.timestamp_precision_distribution,
        canonical_payload_hash=s.canonical_payload_hash,
        p11_parent_snapshot=s.p11_parent_snapshot,
        created_at=s.created_at.isoformat(),
        non_causal_disclosure=s.non_causal_disclosure,
        health_safety_disclosure=s.health_safety_disclosure,
    )


@router.post("/register", response_model=ObservedOutcomeResponse)
def register_observation(req: RegisterObservationRequest):
    """Ingest a new real-world outcome observation."""
    try:
        domain_enum = ControlledResearchDomain(req.domain)
        prec_enum = TimestampPrecision(req.timestamp_precision)
        src_enum = EvidenceSourceType(req.observation_source_type)
        origin_enum = EvidenceOrigin(req.evidence_origin)
        status_enum = OutcomeVerificationStatus(req.verification_status)
        consent_enum = ConsentStatus(req.consent_status)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Invalid enum parameter: {err}")

    try:
        record = ResearchEvidenceRegistryEngine.get_instance().register_observation(
            subject_reference=req.subject_reference,
            domain=domain_enum,
            event_type=req.event_type,
            event_description=req.event_description,
            event_date=req.event_date,
            event_timezone=req.event_timezone,
            event_time=req.event_time,
            timestamp_precision=prec_enum,
            observation_source_type=src_enum,
            evidence_origin=origin_enum,
            verification_status=status_enum,
            verification_method=req.verification_method,
            verifier_reference=req.verifier_reference,
            prospective_rule_id=req.prospective_rule_id,
            experiment_id=req.experiment_id,
            p11_snapshot_id=req.p11_snapshot_id,
            provenance_parent=req.provenance_parent,
            consent_status=consent_enum,
            notes=req.notes,
        )
        return _serialize_outcome(record)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))


@router.post("/{id}/verify", response_model=ObservedOutcomeResponse)
def verify_observation(id: str, req: VerifyObservationRequest):
    """Update verification status of an existing outcome observation."""
    try:
        status_enum = OutcomeVerificationStatus(req.verification_status)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=f"Invalid verification status: {err}")

    try:
        record = ResearchEvidenceRegistryEngine.get_instance().verify_observation(
            outcome_id=id,
            verification_status=status_enum,
            verification_method=req.verification_method,
            verifier_reference=req.verifier_reference,
            notes=req.notes,
        )
        return _serialize_outcome(record)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/{id}/reject", response_model=ObservedOutcomeResponse)
def reject_observation(id: str, reason: str = Query("Rejected by auditor")):
    """Reject an observation record."""
    try:
        record = ResearchEvidenceRegistryEngine.get_instance().reject_observation(outcome_id=id, reason=reason)
        return _serialize_outcome(record)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/{id}/correct", response_model=ObservedOutcomeResponse)
def correct_observation(id: str, req: CorrectObservationRequest):
    """Apply an append-only correction to an observation record."""
    try:
        record = ResearchEvidenceRegistryEngine.get_instance().correct_observation(
            outcome_id=id,
            updated_event_description=req.updated_event_description,
            updated_event_date=req.updated_event_date,
            correction_reason=req.correction_reason,
        )
        return _serialize_outcome(record)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))


@router.get("/{id}", response_model=ObservedOutcomeResponse)
def get_observation(id: str):
    """Get observation record by ID."""
    record = ResearchEvidenceRegistryEngine.get_instance().get_observation(id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Observation '{id}' not found.")
    return _serialize_outcome(record)


@router.get("", response_model=List[ObservedOutcomeResponse])
def list_observations(
    domain: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    real_world_only: bool = Query(False),
):
    """List observation records."""
    domain_enum = ControlledResearchDomain(domain) if domain else None
    status_enum = OutcomeVerificationStatus(verification_status) if verification_status else None
    records = ResearchEvidenceRegistryEngine.get_instance().list_observations(
        domain=domain_enum,
        verification_status=status_enum,
        real_world_only=real_world_only,
    )
    return [_serialize_outcome(r) for r in records]


@router.get("/{id}/audit", response_model=List[EvidenceAuditEventResponse])
def get_audit_trail(id: str):
    """Get audit trail for a record."""
    trail = ResearchEvidenceRegistryEngine.get_instance().get_audit_trail(outcome_id=id)
    return [_serialize_audit(e) for e in trail]


@router.get("/subject/{subject_id}", response_model=List[ObservedOutcomeResponse])
def get_subject_history(subject_id: str):
    """Get history of observations for a pseudonymous subject."""
    records = ResearchEvidenceRegistryEngine.get_instance().get_subject_history(subject_id)
    return [_serialize_outcome(r) for r in records]


@router.get("/rule/{rule_id}", response_model=List[ObservedOutcomeResponse])
def get_rule_outcomes(rule_id: str):
    """Get verified outcomes associated with a P20 prospective rule."""
    records = ResearchEvidenceRegistryEngine.get_instance().get_rule_outcomes(rule_id)
    return [_serialize_outcome(r) for r in records]


@router.get("/experiment/{experiment_id}", response_model=List[ObservedOutcomeResponse])
def get_experiment_outcomes(experiment_id: str):
    """Get outcomes associated with a P11 experiment."""
    records = ResearchEvidenceRegistryEngine.get_instance().get_experiment_outcomes(experiment_id)
    return [_serialize_outcome(r) for r in records]


@router.post("/snapshot", response_model=EvidenceRegistrySnapshotResponse)
def create_snapshot(p11_parent_snapshot: Optional[str] = Query(None)):
    """Generate an immutable evidence registry snapshot."""
    snapshot = ResearchEvidenceRegistryEngine.get_instance().build_evidence_snapshot(p11_parent_snapshot=p11_parent_snapshot)
    return _serialize_snapshot(snapshot)


@router.get("/snapshot/{id}", response_model=EvidenceRegistrySnapshotResponse)
def get_snapshot(id: str):
    """Get evidence registry snapshot by ID."""
    snapshot = ResearchEvidenceRegistryEngine.get_instance().get_snapshot(id)
    if not snapshot:
        # Generate one on demand if requested
        snapshot = ResearchEvidenceRegistryEngine.get_instance().build_evidence_snapshot()
    return _serialize_snapshot(snapshot)
