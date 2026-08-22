"""
Unit tests for Local-First Mobile Sync Engine (Module 21, Priority 6)
"""

import time
import pytest
from datetime import datetime, timedelta, timezone
from apps.api.domain.sync import (
    CanonicalSyncEntityType,
    compute_payload_hash,
)
from apps.api.services.mobile_sync_service import MobileSyncService
from apps.api.services.sync_conflict_engine import SyncConflictResolutionEngine


class TestMobileSyncService:
    @pytest.fixture(autouse=True)
    def clean_service(self):
        # Create a fresh isolated instance for each test
        service = MobileSyncService()
        MobileSyncService._instance = service
        return service

    def test_ephemeral_pairing_flow_success(self, clean_service):
        session = clean_service.generate_pairing_session()
        assert len(session.pin_code) == 6
        assert session.is_expired is False
        assert session.is_claimed is False

        # Claim with valid PIN
        device, token, err = clean_service.verify_pairing(
            session_id=session.session_id,
            pin_code=session.pin_code,
            device_name="Pixel 9 Pro",
            device_type="android",
        )
        assert err is None
        assert device is not None
        assert token is not None
        assert device.device_name == "Pixel 9 Pro"
        assert device.is_active is True

        # Re-claiming the same session MUST fail (Single-Use)
        d2, t2, err2 = clean_service.verify_pairing(
            session_id=session.session_id,
            pin_code=session.pin_code,
            device_name="Intruder Device",
        )
        assert d2 is None
        assert "already been claimed" in err2

    def test_pairing_pin_rate_limiting_and_lockout(self, clean_service):
        session = clean_service.generate_pairing_session()

        # 3 wrong PIN attempts
        for attempt in range(1, 4):
            dev, tok, err = clean_service.verify_pairing(
                session_id=session.session_id,
                pin_code="000000",
            )
            assert dev is None
            assert tok is None

        # 4th attempt should be locked out
        dev, tok, err = clean_service.verify_pairing(
            session_id=session.session_id,
            pin_code=session.pin_code,  # even with correct PIN
        )
        assert dev is None
        assert "locked" in err.lower() or "rate limited" in err.lower()

    def test_pairing_session_expiry(self, clean_service):
        session = clean_service.generate_pairing_session()
        # Force expiration
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        assert session.is_expired is True

        dev, tok, err = clean_service.verify_pairing(
            session_id=session.session_id,
            pin_code=session.pin_code,
        )
        assert dev is None
        assert "expired" in err.lower()

    def test_device_authentication_and_revocation(self, clean_service):
        session = clean_service.generate_pairing_session()
        device, token, _ = clean_service.verify_pairing(session.session_id, pin_code=session.pin_code)

        # Authenticate valid credentials
        assert clean_service.authenticate_device(device.device_id, token) is True
        # Authenticate invalid credentials
        assert clean_service.authenticate_device(device.device_id, "invalid_secret") is False

        # Revoke device
        revoked = clean_service.revoke_device(device.device_id)
        assert revoked is True
        # Authenticate revoked device MUST fail
        assert clean_service.authenticate_device(device.device_id, token) is False

    def test_push_pull_and_sha256_checksum(self, clean_service):
        session = clean_service.generate_pairing_session()
        device, token, _ = clean_service.verify_pairing(session.session_id, pin_code=session.pin_code)

        chart_payload = {
            "name": "Mahatma Gandhi",
            "birth_date": "1869-10-02",
            "birth_time": "07:12",
            "latitude": 21.6417,
            "longitude": 69.6293,
        }
        correct_hash = compute_payload_hash(chart_payload)

        # 1. Valid Push
        mut = {
            "mutation_id": "mut_001",
            "entity_id": "chart_gandhi",
            "entity_type": "birth_chart",
            "payload": chart_payload,
            "revision": 1,
            "payload_hash": correct_hash,
            "created_at_iso": datetime.now(timezone.utc).isoformat(),
            "updated_at_iso": datetime.now(timezone.utc).isoformat(),
        }
        accepted, rejected, conflicts, new_cursor = clean_service.push_mutations(device.device_id, [mut])
        assert "mut_001" in accepted
        assert len(rejected) == 0

        # 2. Corrupted Hash Push MUST be rejected
        corrupt_mut = {
            "mutation_id": "mut_002",
            "entity_id": "chart_corrupt",
            "entity_type": "birth_chart",
            "payload": chart_payload,
            "revision": 1,
            "payload_hash": "bad_corrupted_sha256_checksum",
        }
        accepted2, rejected2, _, _ = clean_service.push_mutations(device.device_id, [corrupt_mut])
        assert "mut_002" in rejected2

        # 3. Pull Delta
        deltas, cursor = clean_service.pull_deltas(device.device_id, last_known_cursor=0)
        entity_ids = [d.entity_id for d in deltas]
        assert "chart_gandhi" in entity_ids

    def test_idempotency_duplicate_push(self, clean_service):
        session = clean_service.generate_pairing_session()
        device, token, _ = clean_service.verify_pairing(session.session_id, pin_code=session.pin_code)

        payload = {"title": "Solar Return Correlation", "notes": "Initial analysis"}
        mut = {
            "mutation_id": "mut_idemp_100",
            "entity_id": "res_hypo_01",
            "entity_type": "research_hypothesis",
            "payload": payload,
            "revision": 1,
            "payload_hash": compute_payload_hash(payload),
        }
        # First submission
        acc1, rej1, _, _ = clean_service.push_mutations(device.device_id, [mut])
        assert "mut_idemp_100" in acc1

        # Duplicate submission with exact same mutation_id
        acc2, rej2, _, _ = clean_service.push_mutations(device.device_id, [mut])
        assert "mut_idemp_100" in acc2
        assert len(rej2) == 0

    def test_deterministic_conflict_resolution_and_archival(self, clean_service):
        session1 = clean_service.generate_pairing_session()
        dev_a, _, _ = clean_service.verify_pairing(session1.session_id, pin_code=session1.pin_code, device_name="Device A")
        session2 = clean_service.generate_pairing_session()
        dev_b, _, _ = clean_service.verify_pairing(session2.session_id, pin_code=session2.pin_code, device_name="Device B")

        entity_id = "chart_shared_001"

        # Device A commits revision 2
        payload_a = {"title": "Shared Chart Edit A"}
        mut_a = {
            "mutation_id": "mut_a_1",
            "entity_id": entity_id,
            "entity_type": "birth_chart",
            "payload": payload_a,
            "revision": 2,
            "payload_hash": compute_payload_hash(payload_a),
        }
        clean_service.push_mutations(dev_a.device_id, [mut_a])

        # Device B attempts revision 3 (Higher revision -> Device B must WIN)
        payload_b = {"title": "Shared Chart Edit B (Rev 3)"}
        mut_b = {
            "mutation_id": "mut_b_1",
            "entity_id": entity_id,
            "entity_type": "birth_chart",
            "payload": payload_b,
            "revision": 3,
            "payload_hash": compute_payload_hash(payload_b),
        }
        _, _, conflicts, _ = clean_service.push_mutations(dev_b.device_id, [mut_b])

        # Check entity store has winner
        deltas, _ = clean_service.pull_deltas(dev_a.device_id, last_known_cursor=0)
        shared = next(d for d in deltas if d.entity_id == entity_id)
        assert shared.revision == 3
        assert shared.payload["title"] == "Shared Chart Edit B (Rev 3)"

        # Check conflict ledger recorded losing version (Rev 2)
        ledger = clean_service.get_conflict_ledger()
        assert len(ledger) >= 1
        conf = next(c for c in ledger if c.entity_id == entity_id)
        assert conf.winning_revision == 3
        assert conf.losing_revision == 2
        assert conf.losing_payload["title"] == "Shared Chart Edit A"

    def test_tombstone_propagation(self, clean_service):
        session = clean_service.generate_pairing_session()
        device, _, _ = clean_service.verify_pairing(session.session_id, pin_code=session.pin_code)

        entity_id = "note_to_delete"
        payload = {"text": "Temporary research note"}

        # 1. Create
        mut_create = {
            "mutation_id": "mut_c_1",
            "entity_id": entity_id,
            "entity_type": "astrological_note",
            "payload": payload,
            "revision": 1,
            "payload_hash": compute_payload_hash(payload),
        }
        clean_service.push_mutations(device.device_id, [mut_create])

        # 2. Tombstone Delete
        mut_delete = {
            "mutation_id": "mut_d_1",
            "entity_id": entity_id,
            "entity_type": "astrological_note",
            "payload": payload,
            "revision": 2,
            "payload_hash": compute_payload_hash(payload),
            "deleted_at_iso": datetime.now(timezone.utc).isoformat(),
        }
        clean_service.push_mutations(device.device_id, [mut_delete])

        # 3. Pull MUST return tombstone with deleted_at != None
        deltas, _ = clean_service.pull_deltas(device.device_id, last_known_cursor=0)
        tombstone = next(d for d in deltas if d.entity_id == entity_id)
        assert tombstone.is_tombstone is True
        assert tombstone.deleted_at is not None

    def test_unauthorized_entity_type_rejected(self, clean_service):
        session = clean_service.generate_pairing_session()
        device, token, _ = clean_service.verify_pairing(session.session_id, pin_code=session.pin_code)

        unauthorized_mut = {
            "mutation_id": "mut_unauth_001",
            "entity_id": "server_log_001",
            "entity_type": "arbitrary_unauthorized_type",
            "payload": {"log": "secret"},
            "revision": 1,
            "payload_hash": compute_payload_hash({"log": "secret"}),
        }
        accepted, rejected, _, _ = clean_service.push_mutations(device.device_id, [unauthorized_mut])
        assert "mut_unauth_001" in rejected
        assert len(accepted) == 0

    def test_deterministic_device_id_tie_break(self, clean_service):
        session1 = clean_service.generate_pairing_session()
        dev_a, _, _ = clean_service.verify_pairing(session1.session_id, pin_code=session1.pin_code, device_name="Device Alpha")
        session2 = clean_service.generate_pairing_session()
        dev_b, _, _ = clean_service.verify_pairing(session2.session_id, pin_code=session2.pin_code, device_name="Device Beta")

        entity_id = "chart_tie_break_001"
        payload_1 = {"title": "First Version"}
        mut_1 = {
            "mutation_id": "mut_tb_1",
            "entity_id": entity_id,
            "entity_type": "birth_chart",
            "payload": payload_1,
            "revision": 2,
            "payload_hash": compute_payload_hash(payload_1),
        }
        clean_service.push_mutations(dev_a.device_id, [mut_1])

        # Second device attempts same revision (2) with different payload
        payload_2 = {"title": "Second Version with Same Revision"}
        mut_2 = {
            "mutation_id": "mut_tb_2",
            "entity_id": entity_id,
            "entity_type": "birth_chart",
            "payload": payload_2,
            "revision": 2,
            "payload_hash": compute_payload_hash(payload_2),
        }
        clean_service.push_mutations(dev_b.device_id, [mut_2])

        deltas, _ = clean_service.pull_deltas(dev_a.device_id, last_known_cursor=0)
        final_record = next(d for d in deltas if d.entity_id == entity_id)

        # Lexical order of device_ids dictates deterministic winner
        expected_winner_dev = dev_b.device_id if dev_b.device_id > dev_a.device_id else dev_a.device_id
        assert final_record.originating_device_id == expected_winner_dev

