"""
AstroOS — Knowledge Ingestion & Retrieval Pydantic Schemas

Request/response DTOs for the governed ingestion and retrieval REST endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Ingestion Schemas ──────────────────────────────────────────────────────────

class DocumentIngestRequest(BaseModel):
    title: str = Field(..., description="Full title of the source document.")
    author: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    language: str = "Sanskrit/English"
    tradition: str = "Parashari"
    source_id: Optional[uuid.UUID] = Field(
        None,
        description="External source reliability record ID (from Knowledge Reliability Framework)."
    )
    book_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional FK to existing canonical BookModel — links without duplicating."
    )


class ChunkIngestRequest(BaseModel):
    document_id: uuid.UUID
    chapter_section: str = Field(..., description="Chapter and section reference (e.g. 'Chapter 24: Planetary Effects').")
    page_location: str = Field(..., description="Page number or sloka location (e.g. 'Page 142' or 'Sloka 20-22').")
    passage_reference: str = Field(..., description="Citable passage slug (e.g. 'BPHS:Ch.24:v20').")
    chunk_index: int = Field(..., ge=0, description="Zero-based position of this chunk within the document/section.")
    content: str = Field(..., description="Verbatim source text content. Must not be AI-generated.")
    technique_framework: str = Field(default="Parashari", description="TechniqueFramework enum value.")
    verse_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional FK to existing canonical VerseModel — links without duplicating verse data."
    )
    grahas: List[str] = Field(default_factory=list, description="Planet/graha tags (e.g. ['jupiter', 'moon']).")
    bhavas: List[int] = Field(default_factory=list, description="House numbers (1-12).")
    rashis: List[str] = Field(default_factory=list, description="Rashi/sign tags.")
    nakshatras: List[str] = Field(default_factory=list, description="Nakshatra tags.")
    yogas: List[str] = Field(default_factory=list, description="Yoga names (e.g. ['Gaja Kesari Yoga']).")
    event_types: List[str] = Field(default_factory=list, description="Event/topic categories.")
    is_ai_extracted: bool = Field(
        default=False,
        description="True if astrological metadata was suggested by AI — treated as non-authoritative."
    )
    extraction_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extraction provenance: model, version, confidence."
    )


class DocumentIngestResponse(BaseModel):
    document_id: uuid.UUID
    title: str
    status: str
    message: str


class ChunkIngestResponse(BaseModel):
    chunk_id: str
    document_id: uuid.UUID
    passage_reference: str
    lifecycle_state: str
    evidence_level: str
    is_ai_extracted: bool
    message: str


# ── Retrieval Schemas ──────────────────────────────────────────────────────────

class RetrievalRequest(BaseModel):
    query: str = Field(..., description="Natural language retrieval query.")
    technique_framework: Optional[str] = Field(
        None,
        description="Restrict to a technique framework. Cross-framework results will be warned."
    )
    include_unvalidated: bool = Field(
        default=False,
        description="If True, UNVALIDATED/UNKNOWN lifecycle items are included and explicitly labelled."
    )
    grahas: List[str] = Field(default_factory=list)
    bhavas: List[int] = Field(default_factory=list)
    rashis: List[str] = Field(default_factory=list)
    nakshatras: List[str] = Field(default_factory=list)
    yogas: List[str] = Field(default_factory=list)
    event_types: List[str] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=50)
    min_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    embedding_model: Optional[str] = None


class ProvenanceChainSchema(BaseModel):
    document_id: str
    source_id: Optional[str]
    chapter_section: str
    page_location: str
    passage_reference: str


class RetrievedEvidenceItemSchema(BaseModel):
    item_id: str
    content: str
    source_title: str
    source_id: uuid.UUID
    document_id: uuid.UUID
    passage_reference: str
    provenance_chain: ProvenanceChainSchema
    technique_framework: str
    lifecycle_state: str
    evidence_level: str
    relevance_score: float
    retrieval_metadata: Dict[str, Any]
    evidence_family_id: Optional[str]
    is_unvalidated: bool


class EvidenceWarningSchema(BaseModel):
    warning_type: str
    message: str
    affected_item_ids: List[str]


class EvidencePackageSchema(BaseModel):
    package_id: str
    query: str
    retrieval_method: str
    filters_applied: Dict[str, Any]
    retrieved_items: List[RetrievedEvidenceItemSchema]
    warnings: List[EvidenceWarningSchema]
    total_items_matched: int
    generated_at: datetime


class GroundedQARequest(BaseModel):
    question: str
    technique_framework: Optional[str] = None
    include_unvalidated: bool = False
    top_k: int = Field(default=5, ge=1, le=20)
    embedding_model: Optional[str] = None


class GroundedQAResponseSchema(BaseModel):
    response_id: str
    question: str
    source_facts: List[str]
    grounded_synthesis: str
    governance_disclosure: str
    is_astrological_prediction: bool
    evidence_package: EvidencePackageSchema
    generated_at: datetime
