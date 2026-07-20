"""Schemas for the Phase II.4 batch job API."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, Field

from apps.api.schemas.report import BirthDataInput


class BatchSubjectInput(BirthDataInput):
    """One subject within a batch chart-report request."""

    label: Annotated[
        Optional[str], Field(default=None, description="Optional identifier, e.g. a name or row id.")
    ] = None


class BatchChartReportRequest(BaseModel):
    """Submit up to 1000+ births for chart-report generation as one job."""

    subjects: Annotated[
        list[BatchSubjectInput],
        Field(min_length=1, max_length=5000, description="Births to compute reports for."),
    ]
    title_prefix: Annotated[str, Field(default="AstroOS Chart")] = "AstroOS Chart"
    format: Annotated[
        str,
        Field(
            default="csv",
            pattern="^(pdf|csv)$",
            description=(
                "'csv' is recommended and fully verified end-to-end. 'pdf' depends on "
                "apps/api/services/report_template_engine.py's HTML templates, which are "
                "currently missing from the repository (see architecture/decisions/AMP-010) — "
                "PDF subjects will fail individually with the error recorded in the batch's "
                "MANIFEST.txt rather than aborting the whole job."
            ),
        ),
    ] = "csv"


class JobProgress(BaseModel):
    current: int
    total: int


class JobStatusResponse(BaseModel):
    id: str
    pool: str
    priority: str
    status: str
    attempt: int
    progress: JobProgress
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchSubmitResponse(BaseModel):
    job_id: str
    pool: str
    status: str
    subject_count: int
