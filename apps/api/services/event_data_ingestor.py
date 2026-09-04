"""
AstroOS — Reference Event Data Ingestor & Pseudonymization Adapter.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, date
from typing import List, Optional

from apps.api.services.event_data_platform import (
    DatePrecision,
    Domain,
    EventIngestor,
    EventRecord,
    EvidenceTier,
    SnapshotManifest,
)

RODDEN_TIER = {
    "AA": EvidenceTier.T1_DOCUMENT,
    "A": EvidenceTier.T2_SELF,
    "B": EvidenceTier.T2_SELF,
    "C": None,
    "D": None,
    "X": None,
}

ONTOLOGY_MAP = {
    ("marriage", "marriage"): "MARRIAGE-FIRST-LEGAL",
    ("marriage", "wedding"): "MARRIAGE-FIRST-LEGAL",
    ("career", "job"): "CAREER-FIRST-JOB",
    ("career", "promotion"): "CAREER-PROMOTION",
    ("career", "work"): "CAREER-FIRST-JOB",
    ("health", "disease"): "HEALTH-SERIOUS-DIAG",
    ("health", "surgery"): "HEALTH-SURGERY",
    ("health", "death"): "HEALTH-SERIOUS-DIAG",
    ("finance", "wealth"): "FIN-WINDFALL",
    ("finance", "loss"): "FIN-MAJOR-LOSS",
}


def pseudonymize(adb_id: str, salt: str = "astroos-salt-2026") -> str:
    return "S-" + hashlib.sha256(f"{salt}:{adb_id}".encode()).hexdigest()[:12]


def parse_precision(date_str: str) -> tuple[Optional[date], DatePrecision]:
    for fmt, prec in (
        ("%Y-%m-%d", DatePrecision.DAY),
        ("%Y-%m", DatePrecision.MONTH),
        ("%Y", DatePrecision.YEAR),
    ):
        try:
            return datetime.strptime(date_str.strip(), fmt).date(), prec
        except ValueError:
            continue
    return None, DatePrecision.UNKNOWN


class ReferenceEventDataIngestor:
    def __init__(self, ingestor: EventIngestor, pseudonym_salt: str = "astroos-salt-2026"):
        self.ingestor = ingestor
        self.salt = pseudonym_salt

    def convert(self, rec: dict) -> Optional[EventRecord]:
        rating = rec.get("rodden_rating", "").strip().upper()
        tier = RODDEN_TIER.get(rating)
        if tier is None:
            return None

        ev_date, prec = parse_precision(rec.get("event_date", ""))
        if ev_date is None or prec is DatePrecision.UNKNOWN:
            return None

        dom_str = rec.get("domain", "").lower().strip()
        cls_str = rec.get("adb_event_class", "").lower().strip()
        etype = ONTOLOGY_MAP.get((dom_str, cls_str))
        if etype is None:
            return None

        sid = pseudonymize(rec.get("adb_id", "adb-0"), self.salt)

        try:
            domain_enum = Domain(dom_str)
        except ValueError:
            return None

        b_year = str(rec.get("birth_year", "1980"))
        decade = b_year[:3] + "0s" if len(b_year) >= 4 else "unknown"

        return EventRecord(
            subject_ref=sid,
            domain=domain_enum,
            event_type=etype,
            event_date=ev_date,
            date_precision=prec,
            evidence_tier=tier,
            evidence_refs=[f"adb:{rec.get('adb_id')}:rod{rating}"],
            severity=rec.get("severity"),
            annotator_ids=["ASTRODATABANK-SOURCE"],
            cohort_strata={"birth_decade": decade, "source": "astrodatabank"},
        )

    def ingest_batch(self, records: List[dict]) -> SnapshotManifest:
        events, rejects = [], []
        for r in records:
            e = self.convert(r)
            if e is None:
                continue
            res = self.ingestor.ingest(e)
            if res.accepted:
                events.append(e)
            else:
                rejects.extend(res.rejected)

        return SnapshotManifest.build(
            events=events,
            records_hashes=[e.event_id for e in events],
            iaa=float("nan"),
            exclusions=len(rejects),
        )
