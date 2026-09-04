"""
AstroOS — Research Publication Schemas (Priority 30)
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ReportSectionSchema(BaseModel):
    section_id: str
    section_type: str
    title: str
    content: str
    source_priority_refs: List[str]
    is_non_causal_compliant: bool


class CryptographicAuditEntrySchema(BaseModel):
    entry_id: str
    priority_ref: str
    snapshot_id: str
    sha256_hash: str
    description: str
    recorded_at: str


class ResearchPublicationReportResponse(BaseModel):
    report_id: str
    title: str
    target_objective: str
    status: str
    sections: List[ReportSectionSchema]
    cryptographic_audit_chain: List[CryptographicAuditEntrySchema]
    p11_root_snapshot_id: str
    report_sha256_seal: str
    publication_non_causal_declaration: str
    total_pipeline_stages_covered: int
    generated_at: str


class GeneratePublicationRequest(BaseModel):
    target_objective: str = Field(default="marriage")
    snapshot_id: Optional[str] = Field(default=None)
    status: str = Field(default="PEER_REVIEW_READY")
