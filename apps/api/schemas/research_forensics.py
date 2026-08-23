"""
AstroOS — Research Forensics Schemas (Priority 31)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ForensicEvidenceItemSchema(BaseModel):
    evidence_id: str
    evidence_type: str
    origin: str
    source_priority: str
    source_identifier: str
    snapshot_hash: str
    content_hash: str
    timestamp: str
    provenance_parent: Optional[str] = None
    integrity_status: str


class ForensicTraceStepSchema(BaseModel):
    step_id: str
    priority: str
    engine: str
    input_hash: str
    configuration_hash: str
    formula_hash: str
    output_hash: str
    execution_timestamp: str
    status: str
    drift_detected: bool


class ForensicReconstructionResponse(BaseModel):
    reconstruction_id: str
    target_result_id: str
    verdict: str
    evidence_items: List[ForensicEvidenceItemSchema]
    trace_steps: List[ForensicTraceStepSchema]
    original_output_hash: str
    reconstructed_output_hash: str
    hash_match: bool
    numerical_drift: float
    relative_drift: float
    drift_classification: str
    provenance_intact: bool
    evidence_completeness: float
    evidence_origin_summary: Dict[str, int]
    failed_checks: List[str]
    warnings: List[str]
    p11_lineage_snapshot_id: str
    p30_publication_seal: Optional[str] = None
    non_causal_disclosure: str
    synthetic_data_disclosure: str


class ForensicAuditReportResponse(BaseModel):
    report_id: str
    target_objective: str
    verdict: str
    reconstruction_status: str
    integrity_status: str
    evidence_integrity: bool
    calculation_integrity: bool
    provenance_integrity: bool
    evidence_origin_summary: Dict[str, int]
    timeline: List[ForensicTraceStepSchema]
    p11_root_snapshot_id: str
    p30_publication_seal: Optional[str] = None
    p31_forensic_seal: str
    generated_at: str
    non_causal_epistemic_declaration: str
    synthetic_data_epistemic_declaration: str


class ReconstructRequest(BaseModel):
    target_objective: str = Field(default="marriage")
    snapshot_id: Optional[str] = Field(default=None)
    simulate_modified_evidence: bool = Field(default=False)
    simulate_provenance_break: bool = Field(default=False)
