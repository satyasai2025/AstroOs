"""
AstroOS — Ground Truth Event Data Contract
==========================================
Enforces strict provenance, date precision, and verification status
for all ground-truth life events used in empirical calibration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GroundTruthEvent:
    case_id: str
    event_type: str          # "death" | "marriage" | "divorce" | "career.office" | "accident" | "health.disease" | "family"
    date: str                # ISO format: "YYYY-MM-DD", "YYYY-MM", or "YYYY"
    precision: str           # "day" | "month" | "year"
    source: str              # e.g. "Birth Certificate", "Hospital Record", "NCGR"
    source_url: str = ""
    verified_by: str = "AstroOS-Curator"
    notes: str = ""
    verified: bool = True
