"""
AstroOS — Research Evidence Registry Pydantic Schemas (Priority 32)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RegisterObservationRequest(BaseModel):
    subject_reference: str = Field(..., description="Pseudonymous subject identifier (e.g., 'subj-anon-8821')")
    domain: str = Field(default="MARRIAGE", description="Controlled research domain")
    event_type: str = Field(default="MARRIAGE_VERIFIED_DATE")
    event_description: str = Field(..., description="Observed event description")
    event_date: str = Field(..., description="ISO event date YYYY-MM-DD")
    event_timezone: str = Field(default="UTC")
    event_time: Optional[str] = Field(default=None)
    timestamp_precision: str = Field(default="DAY")
    observation_source_type: str = Field(default="PARTICIPANT_SELF_REPORT")
    evidence_origin: str = Field(default="OBSERVED_REAL_WORLD_EVIDENCE")
    verification_status: str = Field(default="SELF_REPORTED")
    verification_method: str = Field(default="SELF_REPORTED_DECLARATION")
    verifier_reference: str = Field(default="RESEARCH_PARTICIPANT")
    prospective_rule_id: Optional[str] = Field(default=None)
    experiment_id: Optional[str] = Field(default=None)
    p11_snapshot_id: Optional[str] = Field(default=None)
    provenance_parent: Optional[str] = Field(default=None)
    consent_status: str = Field(default="CONSENT_GRANTED")
    notes: str = Field(default="")


class VerifyObservationRequest(BaseModel):
    verification_status: str = Field(..., description="Target OutcomeVerificationStatus")
    verification_method: str = Field(..., description="Verification method (e.g. 'MARRIAGE_CERTIFICATE_INSPECTION')")
    verifier_reference: str = Field(..., description="Verifier reference ID or role")
    notes: str = Field(default="")


class CorrectObservationRequest(BaseModel):
    updated_event_description: str = Field(..., description="Updated event description")
    updated_event_date: str = Field(..., description="Updated YYYY-MM-DD date")
    correction_reason: str = Field(..., description="Reason for correction")


class ObservedOutcomeResponse(BaseModel):
    outcome_id: str
    subject_reference: str
    domain: str
    event_type: str
    event_description: str
    event_date: str
    event_time: Optional[str] = None
    event_timezone: str
    timestamp_precision: str
    observation_source_type: str
    evidence_origin: str
    verification_status: str
    verification_method: str
    verifier_reference: str
    evidence_hash: str
    source_hash: str
    created_at: str
    updated_at: str
    prospective_rule_id: Optional[str] = None
    experiment_id: Optional[str] = None
    p11_snapshot_id: Optional[str] = None
    provenance_parent: Optional[str] = None
    consent_status: str
    privacy_classification: str
    notes: str
    non_causal_disclosure: str


class EvidenceAuditEventResponse(BaseModel):
    audit_event_id: str
    outcome_id: str
    operation: str
    previous_hash: Optional[str] = None
    new_hash: str
    actor_type: str
    timestamp: str
    reason: str
    p11_snapshot_id: Optional[str] = None


class EvidenceRegistrySnapshotResponse(BaseModel):
    snapshot_id: str
    record_count: int
    verified_record_count: int
    rejected_record_count: int
    unverified_record_count: int
    source_distribution: Dict[str, int]
    domain_distribution: Dict[str, int]
    timestamp_precision_distribution: Dict[str, int]
    canonical_payload_hash: str
    p11_parent_snapshot: Optional[str] = None
    created_at: str
    non_causal_disclosure: str
    health_safety_disclosure: str
