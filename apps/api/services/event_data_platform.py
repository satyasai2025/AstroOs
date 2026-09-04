"""
AstroOS — Gap 1: Event Data Platform.

Purpose: Make the expanded cohort (n+ >= 100/domain) scorable honestly.
The dataset is a first-class governed artifact, not a pile of records.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class EvidenceTier(str, Enum):
    T1_DOCUMENT = "T1"   # certificate/official record with exact date
    T2_SELF     = "T2"   # self-report, date precision >= month
    T3_THIRD    = "T3"   # third-party report, or year-only precision


class DatePrecision(str, Enum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    UNKNOWN = "unknown"


class Domain(str, Enum):
    CAREER = "career"
    MARRIAGE = "marriage"
    HEALTH = "health"
    FINANCE = "finance"
    ACCIDENT = "accident"


EVENT_ONTOLOGY: Dict[str, dict] = {
    # marriage
    "MARRIAGE-FIRST-LEGAL": {"domain": "marriage", "tolerance_days": 365, "min_tier": "T2"},
    "MARRIAGE-COHAB-START": {"domain": "marriage", "tolerance_days": 180, "min_tier": "T2"},
    "MARRIAGE-ENGAGEMENT": {"domain": "marriage", "tolerance_days": 180, "min_tier": "T3"},
    # career
    "CAREER-FIRST-JOB": {"domain": "career", "tolerance_days": 180, "min_tier": "T2"},
    "CAREER-PROMOTION": {"domain": "career", "tolerance_days": 90, "min_tier": "T2"},
    "CAREER-JOB-LOSS": {"domain": "career", "tolerance_days": 90, "min_tier": "T2"},
    "CAREER-BUSINESS-START": {"domain": "career", "tolerance_days": 180, "min_tier": "T2"},
    # health
    "HEALTH-SERIOUS-DIAG": {"domain": "health", "tolerance_days": 90, "min_tier": "T1", "severity": "serious"},
    "HEALTH-SURGERY": {"domain": "health", "tolerance_days": 30, "min_tier": "T1"},
    "HEALTH-ACCIDENT-INJURY": {"domain": "health", "tolerance_days": 14, "min_tier": "T2"},
    "HEALTH-MINOR": {"domain": "health", "tolerance_days": 7, "min_tier": "T3"},
    # finance
    "FIN-WINDFALL": {"domain": "finance", "tolerance_days": 90, "min_tier": "T1"},
    "FIN-MAJOR-LOSS": {"domain": "finance", "tolerance_days": 90, "min_tier": "T1"},
}


@dataclass(frozen=True)
class ScoringContract:
    version: str
    hit_rule: str = (
        "A window W is a HIT for event E iff event_date(E) falls within "
        "[W.start - tolerance(E.type), W.end + tolerance(E.type)] where "
        "tolerance comes from EVENT_ONTOLOGY."
    )
    primary_scoring: str = "hazard-peak ± tolerance(E.type)/2"
    window_assignment: str = "credit the window with the HIGHEST gate score among windows the event touches"
    label_propagation: str = "windows overlapping a hit via tolerance only are labeled NEGATIVE for primary metrics"

    def content_hash(self) -> str:
        blob = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


ACTIVE_CONTRACT = ScoringContract(version="SCORING-CONTRACT-v1.0")


class ConsentRecord(BaseModel):
    subject_ref: str
    consent_version: str = "CONSENT-v1.0"
    research_use: bool
    revocable: bool = True
    granted_at: datetime
    revoked_at: Optional[datetime] = None

    @property
    def active(self) -> bool:
        return self.research_use and self.revoked_at is None


class BirthDataQuality(BaseModel):
    source: Literal["certificate", "hospital-record", "self-reported", "rectified"]
    time_precision: Literal["exact", "minute", "hour", "unknown"]
    rectification_confidence: float = Field(..., ge=0.0, le=1.0)


class EventRecord(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EV-{uuid4().hex[:12]}")
    subject_ref: str
    domain: Domain
    event_type: str
    event_date: date
    date_precision: DatePrecision
    evidence_tier: EvidenceTier
    evidence_refs: List[str] = Field(default_factory=list)
    severity: Optional[int] = Field(None, ge=1, le=5)
    annotator_ids: List[str] = Field(..., min_length=1)
    adjudicated: bool = False
    cohort_strata: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ontology_check(self) -> EventRecord:
        spec = EVENT_ONTOLOGY.get(self.event_type)
        if spec is None:
            raise ValueError(f"event_type '{self.event_type}' not in ontology")
        if spec["domain"] != self.domain.value:
            raise ValueError(f"type/domain mismatch for {self.event_type}")
        tier_ranks = {"T1": 3, "T2": 2, "T3": 1}
        if tier_ranks.get(self.evidence_tier.value, 0) < tier_ranks.get(spec["min_tier"], 0):
            raise ValueError(f"{self.event_type} requires tier >= {spec['min_tier']}")
        return self


class IngestionResult(BaseModel):
    accepted: List[str]
    rejected: List[Tuple[str, str]]
    routed_to_second_annotator: List[str]


class EventIngestor:
    AMBIGUITY_RULES = [
        ("MARRIAGE-COHAB-START", "ambiguous onset"),
        ("CAREER-PROMOTION", "effective-date vs announcement-date ambiguity"),
        ("HEALTH-MINOR", "severity threshold subjectivity"),
    ]

    def __init__(
        self,
        existing_events: List[EventRecord],
        consents: Dict[str, ConsentRecord],
        birth_quality: Dict[str, BirthDataQuality],
    ):
        self.existing = existing_events
        self.consents = consents
        self.birth_q = birth_quality

    def ingest(self, rec: EventRecord) -> IngestionResult:
        reasons: List[str] = []
        c = self.consents.get(rec.subject_ref)
        if c is None or not c.active:
            reasons.append("CONSENT_INACTIVE")

        bq = self.birth_q.get(rec.subject_ref)
        if bq is None or bq.rectification_confidence < 0.70:
            reasons.append("BIRTH_TIME_BELOW_GATE")

        if rec.evidence_tier != EvidenceTier.T3_THIRD and not rec.evidence_refs:
            reasons.append("MISSING_EVIDENCE_REFS")

        for e in self.existing:
            if (
                e.subject_ref == rec.subject_ref
                and e.event_type == rec.event_type
                and abs((e.event_date - rec.event_date).days) <= 45
            ):
                reasons.append(f"NEAR_DUPLICATE_OF:{e.event_id}")
                break

        if reasons:
            return IngestionResult(accepted=[], rejected=[(rec.event_id, ";".join(reasons))], routed_to_second_annotator=[])

        ambiguous = any(rec.event_type == t for t, _ in self.AMBIGUITY_RULES)
        return IngestionResult(
            accepted=[rec.event_id] if not ambiguous else [],
            rejected=[],
            routed_to_second_annotator=[rec.event_id] if ambiguous else [],
        )


class SnapshotManifest(BaseModel):
    snapshot_id: str
    contract_hash: str
    ontology_version: str
    n_subjects: int
    n_events: int
    n_positives_by_domain: Dict[str, int]
    evidence_tier_dist: Dict[str, int]
    iaa: float
    birth_gate_exclusions: int
    content_hash: str
    created_at: datetime

    @classmethod
    def build(
        cls,
        events: List[EventRecord],
        records_hashes: List[str],
        iaa: float,
        exclusions: int,
    ) -> SnapshotManifest:
        by_domain: Dict[str, int] = {}
        tiers: Dict[str, int] = {}
        for e in events:
            by_domain[e.domain.value] = by_domain.get(e.domain.value, 0) + 1
            tiers[e.evidence_tier.value] = tiers.get(e.evidence_tier.value, 0) + 1
        ch = hashlib.sha256("".join(sorted(records_hashes)).encode()).hexdigest()[:16]
        return cls(
            snapshot_id=f"COHORT-v2.0-{datetime.utcnow():%Y%m%d}",
            contract_hash=ACTIVE_CONTRACT.content_hash(),
            ontology_version="ONTOLOGY-v1.0",
            n_subjects=len({e.subject_ref for e in events}),
            n_events=len(events),
            n_positives_by_domain=by_domain,
            evidence_tier_dist=tiers,
            iaa=iaa,
            birth_gate_exclusions=exclusions,
            content_hash=ch,
            created_at=datetime.utcnow(),
        )

    def benchmark_eligible(self, target: Optional[Dict[str, int]] = None) -> bool:
        if not math.isnan(self.iaa) and self.iaa <= 0.85:
            return False
        t12 = self.evidence_tier_dist.get("T1", 0) + self.evidence_tier_dist.get("T2", 0)
        if self.n_events and (t12 / self.n_events) < 0.80:
            return False
        if target:
            for d, n in target.items():
                if self.n_positives_by_domain.get(d, 0) < n:
                    return False
        return True

