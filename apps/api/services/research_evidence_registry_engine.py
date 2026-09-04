"""
AstroOS — Research Evidence Intake & Real-World Outcome Registry Engine (Priority 32)

Implements a controlled, append-only, provenance-preserving outcome observation registry:
  - Ingests strictly OBSERVED_REAL_WORLD_EVIDENCE as primary records
  - Enforces health safety guardrails (rejecting clinical/diagnostic terms)
  - Manages consent status and privacy data minimization
  - Emits append-only audit events for every mutation
  - Generates immutable, deterministic evidence snapshots linked to P11 lineage
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.research_evidence_registry import (
    AuditEventOperation,
    ConsentStatus,
    ControlledResearchDomain,
    EvidenceAuditEvent,
    EvidenceOrigin,
    EvidenceRegistrySnapshot,
    EvidenceSourceType,
    MANDATORY_EVIDENCE_DISTINCTION_DISCLOSURE,
    MANDATORY_EVIDENCE_REGISTRY_NON_CAUSAL_DISCLOSURE,
    MANDATORY_HEALTH_SAFETY_DISCLOSURE,
    ObservedOutcomeRecord,
    OutcomeVerificationStatus,
    PROHIBITED_HEALTH_CLINICAL_TERMS,
    TimestampPrecision,
)
from apps.api.services.experiment_service import ExperimentRegistry


def _canonical_hash(payload: Any) -> str:
    """Computes a deterministic SHA-256 hash over canonical JSON representation."""
    if isinstance(payload, str):
        data_str = payload
    else:
        data_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()


class ResearchEvidenceRegistryEngine:
    """
    Governed evidence registry engine for recording real-world outcomes.
    """

    _instance: Optional[ResearchEvidenceRegistryEngine] = None

    def __init__(
        self,
        experiment_registry: Optional[ExperimentRegistry] = None,
    ) -> None:
        self._exp_reg = experiment_registry or ExperimentRegistry.get_instance()
        self._records: Dict[str, ObservedOutcomeRecord] = {}
        self._audit_log: List[EvidenceAuditEvent] = []
        self._snapshots: Dict[str, EvidenceRegistrySnapshot] = {}

    @classmethod
    def get_instance(cls) -> ResearchEvidenceRegistryEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _verify_health_safety(self, domain: ControlledResearchDomain, description: str, notes: str) -> None:
        """Verifies that health records do not contain prohibited clinical/diagnostic terms."""
        combined_text = f"{description} {notes}".lower()
        for prohibited_term in PROHIBITED_HEALTH_CLINICAL_TERMS:
            if prohibited_term in combined_text:
                raise ValueError(
                    f"HEALTH_SAFETY_VIOLATION: Outcome description/notes contain prohibited clinical term: '{prohibited_term}'. "
                    "Health astrology records must evaluate traditional vitality typologies only and cannot contain clinical claims."
                )

    def register_observation(
        self,
        subject_reference: str,
        domain: ControlledResearchDomain,
        event_type: str,
        event_description: str,
        event_date: str,
        event_timezone: str = "UTC",
        event_time: Optional[str] = None,
        timestamp_precision: TimestampPrecision = TimestampPrecision.DAY,
        observation_source_type: EvidenceSourceType = EvidenceSourceType.PARTICIPANT_SELF_REPORT,
        evidence_origin: EvidenceOrigin = EvidenceOrigin.OBSERVED_REAL_WORLD_EVIDENCE,
        verification_status: OutcomeVerificationStatus = OutcomeVerificationStatus.SELF_REPORTED,
        verification_method: str = "SELF_REPORTED_DECLARATION",
        verifier_reference: str = "RESEARCH_PARTICIPANT",
        prospective_rule_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        p11_snapshot_id: Optional[str] = None,
        provenance_parent: Optional[str] = None,
        consent_status: ConsentStatus = ConsentStatus.CONSENT_GRANTED,
        notes: str = "",
    ) -> ObservedOutcomeRecord:
        """
        Ingests a new real-world outcome observation record.
        Strictly rejects synthetic/simulated evidence passed as primary intake.
        """
        if evidence_origin != EvidenceOrigin.OBSERVED_REAL_WORLD_EVIDENCE:
            raise ValueError(
                f"INVALID_EVIDENCE_ORIGIN: Primary registry intake only accepts OBSERVED_REAL_WORLD_EVIDENCE. "
                f"Received '{evidence_origin}'. Synthetic or computational artifacts cannot be ingested as primary outcomes."
            )

        self._verify_health_safety(domain, event_description, notes)

        outcome_id = f"out-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        p11_snap = p11_snapshot_id or "snap-p11-evidence-root"

        payload_for_hashing = {
            "outcome_id": outcome_id,
            "subject_reference": subject_reference,
            "domain": domain.value,
            "event_type": event_type,
            "event_description": event_description,
            "event_date": event_date,
            "event_time": event_time,
            "event_timezone": event_timezone,
            "precision": timestamp_precision.value,
            "source_type": observation_source_type.value,
            "evidence_origin": evidence_origin.value,
            "consent": consent_status.value,
        }
        ev_hash = _canonical_hash(payload_for_hashing)
        src_hash = _canonical_hash({"source": verifier_reference, "method": verification_method})

        record = ObservedOutcomeRecord(
            outcome_id=outcome_id,
            subject_reference=subject_reference,
            domain=domain,
            event_type=event_type,
            event_description=event_description,
            event_date=event_date,
            event_time=event_time,
            event_timezone=event_timezone,
            timestamp_precision=timestamp_precision,
            observation_source_type=observation_source_type,
            evidence_origin=evidence_origin,
            verification_status=verification_status,
            verification_method=verification_method,
            verifier_reference=verifier_reference,
            evidence_hash=ev_hash,
            source_hash=src_hash,
            created_at=now,
            updated_at=now,
            prospective_rule_id=prospective_rule_id,
            experiment_id=experiment_id,
            p11_snapshot_id=p11_snap,
            provenance_parent=provenance_parent,
            consent_status=consent_status,
            privacy_classification="PSEUDONYMOUS_RESEARCH_DATA",
            notes=notes,
            non_causal_disclosure=MANDATORY_EVIDENCE_REGISTRY_NON_CAUSAL_DISCLOSURE,
        )

        self._records[outcome_id] = record

        # Log append-only audit event
        audit_event = EvidenceAuditEvent(
            audit_event_id=f"audit-{uuid.uuid4().hex[:8]}",
            outcome_id=outcome_id,
            operation=AuditEventOperation.CREATED,
            previous_hash=None,
            new_hash=ev_hash,
            actor_type="RESEARCHER",
            timestamp=now,
            reason="Initial observation intake registration",
            p11_snapshot_id=p11_snap,
        )
        self._audit_log.append(audit_event)

        return record

    def verify_observation(
        self,
        outcome_id: str,
        verification_status: OutcomeVerificationStatus,
        verification_method: str,
        verifier_reference: str,
        notes: str = "",
    ) -> ObservedOutcomeRecord:
        """
        Updates the verification status of an existing outcome observation record (append-only audit).
        """
        if outcome_id not in self._records:
            raise KeyError(f"Outcome record '{outcome_id}' not found.")

        existing = self._records[outcome_id]
        now = datetime.now(timezone.utc)

        new_src_hash = _canonical_hash({"source": verifier_reference, "method": verification_method, "prev": existing.source_hash})

        updated_record = ObservedOutcomeRecord(
            outcome_id=existing.outcome_id,
            subject_reference=existing.subject_reference,
            domain=existing.domain,
            event_type=existing.event_type,
            event_description=existing.event_description,
            event_date=existing.event_date,
            event_time=existing.event_time,
            event_timezone=existing.event_timezone,
            timestamp_precision=existing.timestamp_precision,
            observation_source_type=existing.observation_source_type,
            evidence_origin=existing.evidence_origin,
            verification_status=verification_status,
            verification_method=verification_method,
            verifier_reference=verifier_reference,
            evidence_hash=existing.evidence_hash,
            source_hash=new_src_hash,
            created_at=existing.created_at,
            updated_at=now,
            prospective_rule_id=existing.prospective_rule_id,
            experiment_id=existing.experiment_id,
            p11_snapshot_id=existing.p11_snapshot_id,
            provenance_parent=existing.provenance_parent,
            consent_status=existing.consent_status,
            privacy_classification=existing.privacy_classification,
            notes=notes if notes else existing.notes,
            non_causal_disclosure=existing.non_causal_disclosure,
        )

        self._records[outcome_id] = updated_record

        # Log append-only audit event
        audit_event = EvidenceAuditEvent(
            audit_event_id=f"audit-{uuid.uuid4().hex[:8]}",
            outcome_id=outcome_id,
            operation=AuditEventOperation.VERIFIED if verification_status != OutcomeVerificationStatus.REJECTED else AuditEventOperation.REJECTED,
            previous_hash=existing.source_hash,
            new_hash=new_src_hash,
            actor_type="VERIFIER",
            timestamp=now,
            reason=f"Verification status updated to {verification_status.value} via {verification_method}",
            p11_snapshot_id=existing.p11_snapshot_id,
        )
        self._audit_log.append(audit_event)

        return updated_record

    def reject_observation(self, outcome_id: str, reason: str) -> ObservedOutcomeRecord:
        """Rejects an observation record."""
        return self.verify_observation(
            outcome_id=outcome_id,
            verification_status=OutcomeVerificationStatus.REJECTED,
            verification_method="REJECTED_BY_AUDITOR",
            verifier_reference="EVIDENCE_AUDITOR",
            notes=reason,
        )

    def correct_observation(
        self,
        outcome_id: str,
        updated_event_description: str,
        updated_event_date: str,
        correction_reason: str,
    ) -> ObservedOutcomeRecord:
        """
        Applies an append-only correction to an observation description/date, updating the evidence hash.
        """
        if outcome_id not in self._records:
            raise KeyError(f"Outcome record '{outcome_id}' not found.")

        existing = self._records[outcome_id]
        now = datetime.now(timezone.utc)

        self._verify_health_safety(existing.domain, updated_event_description, correction_reason)

        payload_for_hashing = {
            "outcome_id": existing.outcome_id,
            "subject_reference": existing.subject_reference,
            "domain": existing.domain.value,
            "event_type": existing.event_type,
            "event_description": updated_event_description,
            "event_date": updated_event_date,
            "prev_hash": existing.evidence_hash,
            "correction_reason": correction_reason,
        }
        new_ev_hash = _canonical_hash(payload_for_hashing)

        corrected_record = ObservedOutcomeRecord(
            outcome_id=existing.outcome_id,
            subject_reference=existing.subject_reference,
            domain=existing.domain,
            event_type=existing.event_type,
            event_description=updated_event_description,
            event_date=updated_event_date,
            event_time=existing.event_time,
            event_timezone=existing.event_timezone,
            timestamp_precision=existing.timestamp_precision,
            observation_source_type=existing.observation_source_type,
            evidence_origin=existing.evidence_origin,
            verification_status=existing.verification_status,
            verification_method=existing.verification_method,
            verifier_reference=existing.verifier_reference,
            evidence_hash=new_ev_hash,
            source_hash=existing.source_hash,
            created_at=existing.created_at,
            updated_at=now,
            prospective_rule_id=existing.prospective_rule_id,
            experiment_id=existing.experiment_id,
            p11_snapshot_id=existing.p11_snapshot_id,
            provenance_parent=existing.evidence_hash,
            consent_status=existing.consent_status,
            privacy_classification=existing.privacy_classification,
            notes=f"CORRECTED: {correction_reason}. Prev notes: {existing.notes}",
            non_causal_disclosure=existing.non_causal_disclosure,
        )

        self._records[outcome_id] = corrected_record

        audit_event = EvidenceAuditEvent(
            audit_event_id=f"audit-{uuid.uuid4().hex[:8]}",
            outcome_id=outcome_id,
            operation=AuditEventOperation.CORRECTED,
            previous_hash=existing.evidence_hash,
            new_hash=new_ev_hash,
            actor_type="RESEARCHER",
            timestamp=now,
            reason=f"Record corrected: {correction_reason}",
            p11_snapshot_id=existing.p11_snapshot_id,
        )
        self._audit_log.append(audit_event)

        return corrected_record

    def get_observation(self, outcome_id: str) -> Optional[ObservedOutcomeRecord]:
        return self._records.get(outcome_id)

    def list_observations(
        self,
        domain: Optional[ControlledResearchDomain] = None,
        verification_status: Optional[OutcomeVerificationStatus] = None,
        real_world_only: bool = False,
    ) -> List[ObservedOutcomeRecord]:
        """Lists active observations (excluding consent withdrawn records)."""
        active_records = []
        for r in self._records.values():
            if r.consent_status == ConsentStatus.CONSENT_WITHDRAWN:
                continue
            if real_world_only and r.evidence_origin != EvidenceOrigin.OBSERVED_REAL_WORLD_EVIDENCE:
                continue
            if domain and r.domain != domain:
                continue
            if verification_status and r.verification_status != verification_status:
                continue
            active_records.append(r)
        return active_records

    def get_subject_history(self, subject_reference: str) -> List[ObservedOutcomeRecord]:
        return [r for r in self._records.values() if r.subject_reference == subject_reference and r.consent_status != ConsentStatus.CONSENT_WITHDRAWN]

    def get_rule_outcomes(self, prospective_rule_id: str) -> List[ObservedOutcomeRecord]:
        """Provides verified outcomes for P20 / P27 integration."""
        return [
            r for r in self._records.values()
            if r.prospective_rule_id == prospective_rule_id
            and r.consent_status != ConsentStatus.CONSENT_WITHDRAWN
            and r.verification_status in (OutcomeVerificationStatus.DOCUMENTARY_VERIFIED, OutcomeVerificationStatus.INDEPENDENTLY_VERIFIED)
        ]

    def get_experiment_outcomes(self, experiment_id: str) -> List[ObservedOutcomeRecord]:
        return [
            r for r in self._records.values()
            if r.experiment_id == experiment_id
            and r.consent_status != ConsentStatus.CONSENT_WITHDRAWN
        ]

    def get_audit_trail(self, outcome_id: Optional[str] = None) -> List[EvidenceAuditEvent]:
        if outcome_id:
            return [e for e in self._audit_log if e.outcome_id == outcome_id]
        return list(self._audit_log)

    def build_evidence_snapshot(
        self,
        p11_parent_snapshot: Optional[str] = None,
    ) -> EvidenceRegistrySnapshot:
        """
        Builds a deterministic, immutable EvidenceRegistrySnapshot with a SHA-256 canonical hash.
        """
        snapshot_id = f"snap-ev-{uuid.uuid4().hex[:8]}"
        p11_parent = p11_parent_snapshot or "snap-p11-publication-root"
        now = datetime.now(timezone.utc)

        active_records = [r for r in self._records.values() if r.consent_status != ConsentStatus.CONSENT_WITHDRAWN]

        verified_cnt = sum(1 for r in active_records if r.verification_status in (OutcomeVerificationStatus.DOCUMENTARY_VERIFIED, OutcomeVerificationStatus.INDEPENDENTLY_VERIFIED))
        rejected_cnt = sum(1 for r in active_records if r.verification_status == OutcomeVerificationStatus.REJECTED)
        unverified_cnt = sum(1 for r in active_records if r.verification_status in (OutcomeVerificationStatus.UNVERIFIED, OutcomeVerificationStatus.SELF_REPORTED))

        src_dist: Dict[str, int] = {}
        dom_dist: Dict[str, int] = {}
        prec_dist: Dict[str, int] = {}

        for r in active_records:
            src_dist[r.observation_source_type.value] = src_dist.get(r.observation_source_type.value, 0) + 1
            dom_dist[r.domain.value] = dom_dist.get(r.domain.value, 0) + 1
            prec_dist[r.timestamp_precision.value] = prec_dist.get(r.timestamp_precision.value, 0) + 1

        payload_for_hashing = {
            "snapshot_id": snapshot_id,
            "p11_parent": p11_parent,
            "records": [
                {
                    "id": r.outcome_id,
                    "ev_hash": r.evidence_hash,
                    "src_hash": r.source_hash,
                    "status": r.verification_status.value,
                    "precision": r.timestamp_precision.value,
                }
                for r in sorted(active_records, key=lambda x: x.outcome_id)
            ],
            "verified_cnt": verified_cnt,
            "rejected_cnt": rejected_cnt,
            "unverified_cnt": unverified_cnt,
        }
        canonical_hash = _canonical_hash(payload_for_hashing)

        snapshot = EvidenceRegistrySnapshot(
            snapshot_id=snapshot_id,
            record_count=len(active_records),
            verified_record_count=verified_cnt,
            rejected_record_count=rejected_cnt,
            unverified_record_count=unverified_cnt,
            source_distribution=src_dist,
            domain_distribution=dom_dist,
            timestamp_precision_distribution=prec_dist,
            canonical_payload_hash=canonical_hash,
            p11_parent_snapshot=p11_parent,
            created_at=now,
            non_causal_disclosure=MANDATORY_EVIDENCE_REGISTRY_NON_CAUSAL_DISCLOSURE,
            health_safety_disclosure=MANDATORY_HEALTH_SAFETY_DISCLOSURE,
        )

        self._snapshots[snapshot_id] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[EvidenceRegistrySnapshot]:
        return self._snapshots.get(snapshot_id)
