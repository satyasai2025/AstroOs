"""
AstroOS — Research Publication & Cryptographic Audit Report Router (Priority 30)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.domain.research_publication import PublicationStatus
from apps.api.schemas.research_publication import (
    GeneratePublicationRequest,
    ResearchPublicationReportResponse,
)
from apps.api.services.research_publication_engine import ResearchPublicationEngine

router = APIRouter(
    prefix="/api/v1/research/publication",
    tags=["Research Publication"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_report(rep) -> ResearchPublicationReportResponse:
    return ResearchPublicationReportResponse(
        report_id=rep.report_id,
        title=rep.title,
        target_objective=rep.target_objective,
        status=rep.status.value,
        sections=[
            {
                "section_id": s.section_id,
                "section_type": s.section_type.value,
                "title": s.title,
                "content": s.content,
                "source_priority_refs": list(s.source_priority_refs),
                "is_non_causal_compliant": s.is_non_causal_compliant,
            }
            for s in rep.sections
        ],
        cryptographic_audit_chain=[
            {
                "entry_id": e.entry_id,
                "priority_ref": e.priority_ref,
                "snapshot_id": e.snapshot_id,
                "sha256_hash": e.sha256_hash,
                "description": e.description,
                "recorded_at": e.recorded_at.isoformat(),
            }
            for e in rep.cryptographic_audit_chain
        ],
        p11_root_snapshot_id=rep.p11_root_snapshot_id,
        report_sha256_seal=rep.report_sha256_seal,
        publication_non_causal_declaration=rep.publication_non_causal_declaration,
        total_pipeline_stages_covered=rep.total_pipeline_stages_covered,
        generated_at=rep.generated_at.isoformat(),
    )


@router.post("/generate", response_model=ResearchPublicationReportResponse)
def generate_publication_report(request: GeneratePublicationRequest):
    """Generate a complete publication-grade research report from P1→P29 evidence."""
    status_enum = PublicationStatus(request.status)
    rep = ResearchPublicationEngine.get_instance().generate_publication_report(
        target_objective=request.target_objective,
        snapshot_id=request.snapshot_id,
        status=status_enum,
    )
    return _serialize_report(rep)


@router.get("/latest", response_model=ResearchPublicationReportResponse)
def get_latest_publication_report(target_objective: str = Query("marriage")):
    """Generate or retrieve the latest publication report."""
    rep = ResearchPublicationEngine.get_instance().generate_publication_report(
        target_objective=target_objective,
    )
    return _serialize_report(rep)


@router.get("/list", response_model=List[ResearchPublicationReportResponse])
def list_publication_reports():
    """List all generated publication reports."""
    return [_serialize_report(r) for r in ResearchPublicationEngine.get_instance().list_reports()]
