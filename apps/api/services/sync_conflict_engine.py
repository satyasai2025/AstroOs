"""
AstroOS — Sync Conflict Resolution Engine (Module 21, Priority 6)

Deterministic conflict resolution logic:
1. Validates canonical sync entity types.
2. Verifies cryptographic SHA-256 payload integrity.
3. Resolves mutation conflicts using logical revision ordering + deterministic device tie-break.
4. Archives losing versions non-destructively in the immutable conflict ledger.
"""

from __future__ import annotations

import uuid
from typing import Optional
from apps.api.domain.sync import (
    CanonicalSyncEntityType,
    SyncConflictRecord,
    SyncEntityRecord,
    compute_payload_hash,
)


class SyncConflictResolutionEngine:
    """
    Evaluates incoming entity mutations against current server state.
    """

    @staticmethod
    def validate_entity_type(entity_type_str: str) -> Optional[CanonicalSyncEntityType]:
        try:
            return CanonicalSyncEntityType(entity_type_str)
        except ValueError:
            return None

    @staticmethod
    def verify_payload_integrity(payload: dict, claimed_hash: str) -> bool:
        computed = compute_payload_hash(payload)
        return computed.lower() == claimed_hash.lower()

    @staticmethod
    def resolve_conflict(
        existing_record: SyncEntityRecord,
        incoming_record: SyncEntityRecord,
    ) -> tuple[bool, Optional[SyncConflictRecord], str]:
        """
        Determines whether incoming_record wins over existing_record.
        Returns: (incoming_wins: bool, conflict_record: Optional[SyncConflictRecord], reason: str)
        """
        # If identical revision and identical payload hash -> already synchronized / idempotent
        if existing_record.revision == incoming_record.revision and existing_record.payload_hash == incoming_record.payload_hash:
            return False, None, "Identical revision and payload (Idempotent No-Op)"

        incoming_wins = False
        reason = ""

        # 1. Primary Rule: Higher logical revision wins
        if incoming_record.revision > existing_record.revision:
            incoming_wins = True
            reason = f"Incoming revision ({incoming_record.revision}) exceeds existing ({existing_record.revision})."
        elif incoming_record.revision < existing_record.revision:
            incoming_wins = False
            reason = f"Existing revision ({existing_record.revision}) supersedes incoming ({incoming_record.revision})."
        else:
            # 2. Tie-break Rule: Deterministic originating_device_id lexical ordering
            if incoming_record.originating_device_id > existing_record.originating_device_id:
                incoming_wins = True
                reason = (
                    f"Revision tie ({incoming_record.revision}); incoming device "
                    f"'{incoming_record.originating_device_id}' won deterministic tie-break."
                )
            else:
                incoming_wins = False
                reason = (
                    f"Revision tie ({existing_record.revision}); existing device "
                    f"'{existing_record.originating_device_id}' retained via deterministic tie-break."
                )

        # Archive the losing version in immutable conflict ledger
        conflict_id = str(uuid.uuid4())
        if incoming_wins:
            conflict_record = SyncConflictRecord(
                conflict_id=conflict_id,
                entity_id=incoming_record.entity_id,
                entity_type=incoming_record.entity_type.value,
                winning_revision=incoming_record.revision,
                losing_revision=existing_record.revision,
                winning_device_id=incoming_record.originating_device_id,
                losing_device_id=existing_record.originating_device_id,
                winning_payload_hash=incoming_record.payload_hash,
                losing_payload_hash=existing_record.payload_hash,
                losing_payload=existing_record.payload,
                resolution_reason=reason,
            )
        else:
            conflict_record = SyncConflictRecord(
                conflict_id=conflict_id,
                entity_id=existing_record.entity_id,
                entity_type=existing_record.entity_type.value,
                winning_revision=existing_record.revision,
                losing_revision=incoming_record.revision,
                winning_device_id=existing_record.originating_device_id,
                losing_device_id=incoming_record.originating_device_id,
                winning_payload_hash=existing_record.payload_hash,
                losing_payload_hash=incoming_record.payload_hash,
                losing_payload=incoming_record.payload,
                resolution_reason=reason,
            )

        return incoming_wins, conflict_record, reason
