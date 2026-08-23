"""
AstroOS — Research Forensics Router (Priority 31)
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.research_forensics import (
    ForensicAuditReportResponse,
    ForensicEvidenceItemSchema,
    ForensicReconstructionResponse,
    ForensicTraceStepSchema,
    ReconstructRequest,
)
from apps.api.services.research_forensic_engine import ResearchForensicEngine

router = APIRouter(
    prefix="/api/v1/research/forensics",
    tags=["Research Forensics"],
    dependencies=[Depends(require_authenticated)],
)


def _serialize_reconstruction(res) -> ForensicReconstructionResponse:
    return ForensicReconstructionResponse(
        reconstruction_id=res.reconstruction_id,
        target_result_id=res.target_result_id,
        verdict=res.verdict.value,
        evidence_items=[
            {
                "evidence_id": item.evidence_id,
                "evidence_type": item.evidence_type,
                "origin": item.origin.value,
                "source_priority": item.source_priority,
                "source_identifier": item.source_identifier,
                "snapshot_hash": item.snapshot_hash,
                "content_hash": item.content_hash,
                "timestamp": item.timestamp.isoformat(),
                "provenance_parent": item.provenance_parent,
                "integrity_status": item.integrity_status,
            }
            for item in res.evidence_items
        ],
        trace_steps=[
            {
                "step_id": s.step_id,
                "priority": s.priority,
                "engine": s.engine,
                "input_hash": s.input_hash,
                "configuration_hash": s.configuration_hash,
                "formula_hash": s.formula_hash,
                "output_hash": s.output_hash,
                "execution_timestamp": s.execution_timestamp.isoformat(),
                "status": s.status,
                "drift_detected": s.drift_detected,
            }
            for s in res.trace_steps
        ],
        original_output_hash=res.original_output_hash,
        reconstructed_output_hash=res.reconstructed_output_hash,
        hash_match=res.hash_match,
        numerical_drift=res.numerical_drift,
        relative_drift=res.relative_drift,
        drift_classification=res.drift_classification.value,
        provenance_intact=res.provenance_intact,
        evidence_completeness=res.evidence_completeness,
        evidence_origin_summary=res.evidence_origin_summary,
        failed_checks=list(res.failed_checks),
        warnings=list(res.warnings),
        p11_lineage_snapshot_id=res.p11_lineage_snapshot_id,
        p30_publication_seal=res.p30_publication_seal,
        non_causal_disclosure=res.non_causal_disclosure,
        synthetic_data_disclosure=res.synthetic_data_disclosure,
    )


def _serialize_report(rep) -> ForensicAuditReportResponse:
    return ForensicAuditReportResponse(
        report_id=rep.report_id,
        target_objective=rep.target_objective,
        verdict=rep.verdict.value,
        reconstruction_status=rep.reconstruction_status,
        integrity_status=rep.integrity_status,
        evidence_integrity=rep.evidence_integrity,
        calculation_integrity=rep.calculation_integrity,
        provenance_integrity=rep.provenance_integrity,
        evidence_origin_summary=rep.evidence_origin_summary,
        timeline=[
            {
                "step_id": s.step_id,
                "priority": s.priority,
                "engine": s.engine,
                "input_hash": s.input_hash,
                "configuration_hash": s.configuration_hash,
                "formula_hash": s.formula_hash,
                "output_hash": s.output_hash,
                "execution_timestamp": s.execution_timestamp.isoformat(),
                "status": s.status,
                "drift_detected": s.drift_detected,
            }
            for s in rep.timeline
        ],
        p11_root_snapshot_id=rep.p11_root_snapshot_id,
        p30_publication_seal=rep.p30_publication_seal,
        p31_forensic_seal=rep.p31_forensic_seal,
        generated_at=rep.generated_at.isoformat(),
        non_causal_epistemic_declaration=rep.non_causal_epistemic_declaration,
        synthetic_data_epistemic_declaration=rep.synthetic_data_epistemic_declaration,
    )


@router.post("/reconstruct", response_model=ForensicReconstructionResponse)
def reconstruct_research_result(request: ReconstructRequest):
    """Independently reconstruct a research result and replay calculations."""
    res = ResearchForensicEngine.get_instance().reconstruct_research_result(
        target_objective=request.target_objective,
        snapshot_id=request.snapshot_id,
        simulate_modified_evidence=request.simulate_modified_evidence,
        simulate_provenance_break=request.simulate_provenance_break,
    )
    return _serialize_reconstruction(res)


@router.post("/verify", response_model=ForensicAuditReportResponse)
def verify_research_result(request: ReconstructRequest):
    """Run full forensic audit and generate a P31 forensic audit report."""
    rep = ResearchForensicEngine.get_instance().generate_forensic_audit_report(
        target_objective=request.target_objective,
        snapshot_id=request.snapshot_id,
    )
    return _serialize_report(rep)


@router.get("/latest", response_model=ForensicAuditReportResponse)
def get_latest_forensic_report(target_objective: str = Query("marriage")):
    """Get latest forensic audit report."""
    rep = ResearchForensicEngine.get_instance().generate_forensic_audit_report(
        target_objective=target_objective,
    )
    return _serialize_report(rep)


@router.get("/report/{id}", response_model=ForensicAuditReportResponse)
def get_forensic_report_by_id(id: str):
    """Get forensic report by report_id."""
    reports = ResearchForensicEngine.get_instance().list_reports()
    for r in reports:
        if r.report_id == id:
            return _serialize_report(r)
    # If not in cache, generate one
    rep = ResearchForensicEngine.get_instance().generate_forensic_audit_report(target_objective="marriage")
    return _serialize_report(rep)


@router.get("/timeline/{id}", response_model=List[ForensicTraceStepSchema])
def get_forensic_timeline(id: str):
    """Get forensic reconstruction trace timeline."""
    rep = ResearchForensicEngine.get_instance().generate_forensic_audit_report(target_objective="marriage")
    return [
        {
            "step_id": s.step_id,
            "priority": s.priority,
            "engine": s.engine,
            "input_hash": s.input_hash,
            "configuration_hash": s.configuration_hash,
            "formula_hash": s.formula_hash,
            "output_hash": s.output_hash,
            "execution_timestamp": s.execution_timestamp.isoformat(),
            "status": s.status,
            "drift_detected": s.drift_detected,
        }
        for s in rep.timeline
    ]


@router.get("/evidence/{id}", response_model=List[ForensicEvidenceItemSchema])
def get_forensic_evidence_chain(id: str):
    """Get forensic evidence items collected across P1→P30."""
    chain = ResearchForensicEngine.get_instance().collect_evidence_chain(target_objective="marriage")
    return [
        {
            "evidence_id": item.evidence_id,
            "evidence_type": item.evidence_type,
            "origin": item.origin.value,
            "source_priority": item.source_priority,
            "source_identifier": item.source_identifier,
            "snapshot_hash": item.snapshot_hash,
            "content_hash": item.content_hash,
            "timestamp": item.timestamp.isoformat(),
            "provenance_parent": item.provenance_parent,
            "integrity_status": item.integrity_status,
        }
        for item in chain
    ]
