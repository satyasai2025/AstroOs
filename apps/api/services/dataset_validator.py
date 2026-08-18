"""
AstroOS — Dataset Validator & Quality Control Service

Performs multi-tier validation on raw historical event records:
  1. Computational Validity (Swiss Ephemeris chart generation & coordinate bounds)
  2. 3-Tier Duplicate & Conflict Detection (Hard, Conflicting, Possible)
  3. Inclusion Policy Auditing (Rodden threshold & Date precision)
  4. Auditable Rejection Logging (Never silently delete research data)
  5. Cryptographic SHA-256 Content Hashing
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Optional, Sequence

from apps.api.domain.benchmark_dataset import (
    DatasetValidationResult,
    InclusionCriteria,
    PossibleDuplicateWarning,
    RejectedEventRecord,
    RejectionCode,
)
from apps.api.domain.research_calibration import (
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine


_RODDEN_RANK = {
    BirthDataConfidence.AA: 5,
    BirthDataConfidence.A: 4,
    BirthDataConfidence.B: 3,
    BirthDataConfidence.C: 2,
    BirthDataConfidence.DD: 1,
}


class DatasetValidator:
    """Rigorous quality control and audit service for historical research datasets."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        horoscope_engine: Optional[HoroscopeEngine] = None,
    ) -> None:
        from apps.api.config import get_settings
        settings = get_settings()
        self._wrapper = ephemeris_wrapper or EphemerisWrapper(settings.EPHEMERIS_PATH)
        self._horoscope_engine = horoscope_engine or HoroscopeEngine(self._wrapper)

    def validate_and_audit(
        self,
        raw_records: Sequence[dict[str, Any]],
        inclusion_criteria: InclusionCriteria,
    ) -> DatasetValidationResult:
        """Audits a list of raw event records against QC rules and inclusion policies."""
        accepted: list[GroundTruthEvent] = []
        rejected: list[RejectedEventRecord] = []
        warnings: list[PossibleDuplicateWarning] = []

        seen_hard_keys: set[tuple[Any, ...]] = set()
        subject_event_map: dict[tuple[str, str, date], GroundTruthEvent] = {}

        for raw in raw_records:
            event_id = str(raw.get("event_id", ""))
            subject_id = str(raw.get("subject_id", ""))

            # 1. Coordinate & Timestamp Bounds Check
            lat = raw.get("birth_latitude")
            lon = raw.get("birth_longitude")
            dt_raw = raw.get("birth_datetime_utc")
            actual_date_raw = raw.get("actual_date")

            if lat is None or lon is None or not (-90.0 <= float(lat) <= 90.0) or not (-180.0 <= float(lon) <= 180.0):
                rejected.append(
                    RejectedEventRecord(
                        event_id=event_id,
                        subject_id=subject_id,
                        raw_payload=raw,
                        rejection_code=RejectionCode.INVALID_COORDINATES,
                        reason=f"Invalid geographic coordinates: lat={lat}, lon={lon}",
                    )
                )
                continue

            try:
                if isinstance(dt_raw, str):
                    birth_dt = datetime.fromisoformat(dt_raw)
                else:
                    birth_dt = dt_raw

                if isinstance(actual_date_raw, str):
                    actual_date = date.fromisoformat(actual_date_raw)
                else:
                    actual_date = actual_date_raw
            except Exception as e:
                rejected.append(
                    RejectedEventRecord(
                        event_id=event_id,
                        subject_id=subject_id,
                        raw_payload=raw,
                        rejection_code=RejectionCode.INVALID_DATETIME,
                        reason=f"Unparseable datetime or date: {e}",
                    )
                )
                continue

            # 2. Computational Validity Check (Swiss Ephemeris Chart Generation)
            try:
                _ = self._horoscope_engine.generate_d1(birth_dt, float(lat), float(lon), ayanamsa="lahiri")
            except Exception as e:
                rejected.append(
                    RejectedEventRecord(
                        event_id=event_id,
                        subject_id=subject_id,
                        raw_payload=raw,
                        rejection_code=RejectionCode.CHART_GENERATION_FAILED,
                        reason=f"Swiss Ephemeris calculation failed: {e}",
                    )
                )
                continue

            # 3. Provenance & Confidence Enums
            birth_conf_str = str(raw.get("birth_confidence", "AA"))
            birth_conf = (
                BirthDataConfidence(birth_conf_str)
                if birth_conf_str in BirthDataConfidence.__members__
                else BirthDataConfidence.C
            )

            date_conf_str = str(raw.get("event_date_confidence", "exact_date"))
            date_conf = (
                EventDateConfidence(date_conf_str)
                if date_conf_str in EventDateConfidence.__members__
                else EventDateConfidence.EXACT_DATE
            )

            verif_str = str(raw.get("event_verification", "official_document"))
            verif = (
                EventVerification(verif_str)
                if verif_str in EventVerification.__members__
                else EventVerification.SECONDARY_REPORT
            )

            event_type = str(raw.get("event_type", "career"))

            # 4. Inclusion Policy Check
            if _RODDEN_RANK.get(birth_conf, 0) < _RODDEN_RANK.get(inclusion_criteria.min_birth_confidence, 0):
                rejected.append(
                    RejectedEventRecord(
                        event_id=event_id,
                        subject_id=subject_id,
                        raw_payload=raw,
                        rejection_code=RejectionCode.BELOW_RODDEN_THRESHOLD,
                        reason=f"Birth data confidence {birth_conf.value} is below minimum {inclusion_criteria.min_birth_confidence.value}",
                    )
                )
                continue

            if date_conf not in inclusion_criteria.allowed_date_confidences:
                rejected.append(
                    RejectedEventRecord(
                        event_id=event_id,
                        subject_id=subject_id,
                        raw_payload=raw,
                        rejection_code=RejectionCode.BELOW_DATE_PRECISION_THRESHOLD,
                        reason=f"Event date confidence {date_conf.value} is not in allowed precision set",
                    )
                )
                continue

            # 5. 3-Tier Duplicate & Conflict Detection
            hard_key = (subject_id, birth_dt.isoformat(), round(float(lat), 3), round(float(lon), 3), event_type, actual_date.isoformat())
            if hard_key in seen_hard_keys:
                rejected.append(
                    RejectedEventRecord(
                        event_id=event_id,
                        subject_id=subject_id,
                        raw_payload=raw,
                        rejection_code=RejectionCode.HARD_DUPLICATE_COLLISION,
                        reason=f"Exact duplicate collision with previously admitted record for subject {subject_id}",
                    )
                )
                continue

            subj_event_key = (subject_id, event_type, actual_date)
            if subj_event_key in subject_event_map:
                existing = subject_event_map[subj_event_key]
                # If birth data differs, it's a conflict
                if existing.birth_datetime_utc != birth_dt or abs(existing.birth_latitude - float(lat)) > 0.01:
                    rejected.append(
                        RejectedEventRecord(
                            event_id=event_id,
                            subject_id=subject_id,
                            raw_payload=raw,
                            rejection_code=RejectionCode.CONFLICTING_RECORD_COLLISION,
                            reason=f"Conflicting birth data for same subject {subject_id} and event date {actual_date} (existing: {existing.event_id})",
                        )
                    )
                    continue

            # Near-duplicate check
            for acc in accepted:
                if acc.subject_id == subject_id and acc.event_type == event_type:
                    day_diff = abs((acc.actual_date - actual_date).days)
                    if 0 < day_diff <= 30:
                        warnings.append(
                            PossibleDuplicateWarning(
                                primary_event_id=acc.event_id,
                                flagged_event_id=event_id,
                                subject_id=subject_id,
                                reason=f"Subject has another {event_type} event within {day_diff} days on {acc.actual_date}",
                            )
                        )

            # Record accepted
            event_obj = GroundTruthEvent(
                event_id=event_id,
                subject_id=subject_id,
                event_type=event_type,
                actual_date=actual_date,
                birth_datetime_utc=birth_dt,
                birth_latitude=float(lat),
                birth_longitude=float(lon),
                birth_confidence=birth_conf,
                event_date_confidence=date_conf,
                event_verification=verif,
                source_citation=str(raw.get("source_citation", "")),
                notes=str(raw.get("notes", "")),
            )
            seen_hard_keys.add(hard_key)
            subject_event_map[subj_event_key] = event_obj
            accepted.append(event_obj)

        # 6. Compute Cryptographic Content Hash (SHA-256)
        content_hash = self.compute_content_hash(accepted)

        return DatasetValidationResult(
            is_valid=(len(accepted) > 0 and len(rejected) == 0),
            total_submitted=len(raw_records),
            accepted_events=tuple(accepted),
            rejected_records=tuple(rejected),
            flagged_warnings=tuple(warnings),
            content_hash_sha256=content_hash,
        )

    @staticmethod
    def compute_content_hash(events: Sequence[GroundTruthEvent]) -> str:
        """Computes deterministic SHA-256 content hash across accepted events."""
        sorted_events = sorted(events, key=lambda e: (e.subject_id, e.event_type, e.actual_date.isoformat(), e.event_id))
        hash_payload = [
            {
                "event_id": e.event_id,
                "subject_id": e.subject_id,
                "event_type": e.event_type,
                "actual_date": e.actual_date.isoformat(),
                "birth_datetime_utc": e.birth_datetime_utc.isoformat(),
                "birth_latitude": round(e.birth_latitude, 4),
                "birth_longitude": round(e.birth_longitude, 4),
                "birth_confidence": e.birth_confidence.value,
                "event_date_confidence": e.event_date_confidence.value,
            }
            for e in sorted_events
        ]
        payload_bytes = json.dumps(hash_payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload_bytes).hexdigest()