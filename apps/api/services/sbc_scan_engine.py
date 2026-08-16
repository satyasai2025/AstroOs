"""
AstroOS — Sarvatobhadra Chakra (SBC) Date-Range Scanner

A single SBCReport is a snapshot at one instant — most instants show no
active Vedha, since a hit needs a specific benefic planet in a specific
nakshatra casting in a specific direction that happens to land on the
selected Janma element. Locating a "sensitive period" (per the
sensitive-timing skill's convergence framework) requires scanning
forward across a date range and reporting every day a hit actually
occurs, not just checking "right now" — that's what this module adds
on top of sbc_report_service.py.

**Granularity caveat.** Daily sampling (one check per day, noon UTC by
default) can miss a hit that both starts and clears within the same
day — the Moon alone can cross an entire nakshatra in under a day at
perigee. This is a real, stated limitation, not silently glossed over:
callers wanting exact entry/exit times need a finer step or a proper
forward/backward boundary search, neither of which this module does
yet (same class of limitation VedhaAnalysisPanel.tsx already documents
for Rashi Vedha).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from apps.api.services.sbc_report_service import SBCReport, SBCReportService


@dataclass
class SBCScanHit:
    moment_utc: datetime
    report: SBCReport


class SBCScanEngine:
    def __init__(self, report_service: SBCReportService) -> None:
        self._report_service = report_service

    def scan(
        self,
        janma_nakshatra: str,
        start_utc: datetime,
        end_utc: datetime,
        step_days: int = 1,
        sample_hour_utc: int = 12,
    ) -> list[SBCScanHit]:
        if step_days < 1:
            raise ValueError("step_days must be >= 1")
        if end_utc <= start_utc:
            raise ValueError("end_utc must be after start_utc")

        hits: list[SBCScanHit] = []
        cursor = start_utc.replace(hour=sample_hour_utc, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        step = timedelta(days=step_days)

        while cursor <= end_utc:
            report = self._report_service.build_report(cursor, janma_nakshatra=janma_nakshatra)
            if report.vedha_result is not None and report.vedha_result.hits:
                hits.append(SBCScanHit(moment_utc=cursor, report=report))
            cursor += step

        return hits
