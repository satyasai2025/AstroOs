"""
AstroOS — Governed Knowledge Ingestion & Retrieval Domain Models

Defines domain contracts, chunk provenance hierarchies, hybrid retrieval structures,
structured EvidencePackages, and source-grounded QA responses.

Pure Python dataclasses — zero ORM or external framework dependencies.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.knowledge_reliability import (
    ActorRole,
    EvidenceLevel,
    ProvenanceIntegrityError,
    RuleLifecycleState,
    TechniqueFramework,
)


# ── Enums ─────────────────────────────────────────────────────────────────────

class DocumentStatus(str, Enum):
    RAW_UPLOADED = "RAW_UPLOADED"
    PARSED = "PARSED"
    CHUNKED = "CHUNKED"
    INDEXED = "INDEXED"
    ARCHIVED = "ARCHIVED"


class RetrievalMethod(str, Enum):
    KEYWORD_EXACT = "KEYWORD_EXACT"
    SEMANTIC_VECTOR = "SEMANTIC_VECTOR"
    HYBRID_RRF = "HYBRID_RRF"
    METADATA_FILTERED = "METADATA_FILTERED"


class EvidenceWarningType(str, Enum):
    UNVALIDATED_KNOWLEDGE_INCLUDED = "UNVALIDATED_KNOWLEDGE_INCLUDED"
    CROSS_TECHNIQUE_RESULTS_PRESENT = "CROSS_TECHNIQUE_RESULTS_PRESENT"
    CONFLICTING_SOURCES_DETECTED = "CONFLICTING_SOURCES_DETECTED"
    EVIDENCE_FAMILY_OVERLAP_DETECTED = "EVIDENCE_FAMILY_OVERLAP_DETECTED"
    INCOMPLETE_PROVENANCE = "INCOMPLETE_PROVENANCE"


# ── Domain Dataclasses ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class IngestedDocument:
    """A registered raw or catalogue document entering the governed ingestion pipeline."""
    document_id: uuid.UUID
    source_id: uuid.UUID
    title: str
    author: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    language: str = "Sanskrit/English"
    tradition: str = "Parashari"
    content_hash_sha256: str = ""
    status: DocumentStatus = DocumentStatus.RAW_UPLOADED
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class IngestedChunk:
    """
    An immutable text chunk with complete, deterministic provenance:
    Source -> Document -> Edition -> Chapter/Section -> Page/Sloka -> Chunk
    """
    chunk_id: str
    document_id: uuid.UUID
    source_id: uuid.UUID
    chapter_section: str
    page_location: str
    passage_reference: str
    chunk_index: int
    content: str
    content_hash_sha256: str
    technique_framework: TechniqueFramework = TechniqueFramework.PARASHARI
    grahas: Tuple[str, ...] = field(default_factory=tuple)
    bhavas: Tuple[int, ...] = field(default_factory=tuple)
    rashis: Tuple[str, ...] = field(default_factory=tuple)
    nakshatras: Tuple[str, ...] = field(default_factory=tuple)
    yogas: Tuple[str, ...] = field(default_factory=tuple)
    event_types: Tuple[str, ...] = field(default_factory=tuple)
    lifecycle_state: RuleLifecycleState = RuleLifecycleState.DOCUMENTED
    evidence_level: EvidenceLevel = EvidenceLevel.UNVALIDATED
    evidence_family_id: Optional[str] = None
    verse_id: Optional[uuid.UUID] = None  # Link to canonical VerseModel if applicable
    is_ai_extracted: bool = False
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    embedding_model: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def validate_provenance(self) -> None:
        """Validates that all required provenance fields are present and non-empty."""
        if not self.chunk_id or not self.chunk_id.strip():
            raise ProvenanceIntegrityError("Chunk ID must not be empty.")
        if not self.chapter_section or not self.chapter_section.strip():
            raise ProvenanceIntegrityError("Chapter/Section must not be empty.")
        if not self.page_location or not self.page_location.strip():
            raise ProvenanceIntegrityError("Page/Location must not be empty.")
        if not self.passage_reference or not self.passage_reference.strip():
            raise ProvenanceIntegrityError("Passage reference must not be empty.")
        if not self.content or not self.content.strip():
            raise ProvenanceIntegrityError("Chunk content must not be empty.")
        
        # Verify content hash integrity
        expected_hash = hashlib.sha256(self.content.strip().encode("utf-8")).hexdigest()
        if self.content_hash_sha256 and self.content_hash_sha256 != expected_hash:
            raise ProvenanceIntegrityError(
                f"Content hash mismatch for chunk {self.chunk_id}: "
                f"expected {expected_hash}, got {self.content_hash_sha256}"
            )


@dataclass(frozen=True)
class RetrievalFilter:
    """Filter parameters for governed hybrid retrieval."""
    technique_framework: Optional[TechniqueFramework] = None
    include_unvalidated: bool = False
    allowed_lifecycle_states: Optional[Tuple[RuleLifecycleState, ...]] = None
    allowed_evidence_levels: Optional[Tuple[EvidenceLevel, ...]] = None
    source_ids: Optional[Tuple[uuid.UUID, ...]] = None
    document_ids: Optional[Tuple[uuid.UUID, ...]] = None
    grahas: Optional[Tuple[str, ...]] = None
    bhavas: Optional[Tuple[int, ...]] = None
    rashis: Optional[Tuple[str, ...]] = None
    nakshatras: Optional[Tuple[str, ...]] = None
    yogas: Optional[Tuple[str, ...]] = None
    event_types: Optional[Tuple[str, ...]] = None
    top_k: int = 10
    min_relevance_score: float = 0.0


@dataclass(frozen=True)
class RetrievedEvidenceItem:
    """One individual evidence item retrieved from the governed knowledge corpus."""
    item_id: str
    content: str
    source_title: str
    source_id: uuid.UUID
    document_id: uuid.UUID
    passage_reference: str
    provenance_chain: Dict[str, Any]
    technique_framework: TechniqueFramework
    lifecycle_state: RuleLifecycleState
    evidence_level: EvidenceLevel
    relevance_score: float
    retrieval_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_family_id: Optional[str] = None
    is_unvalidated: bool = True


@dataclass(frozen=True)
class EvidenceWarning:
    """A governance or epistemic warning accompanying an EvidencePackage."""
    warning_type: EvidenceWarningType
    message: str
    affected_item_ids: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvidencePackage:
    """
    Auditable evidence package returned by the retrieval layer.
    Consumed by downstream reasoning layers.
    """
    package_id: str
    query: str
    retrieval_method: RetrievalMethod
    filters_applied: Dict[str, Any]
    retrieved_items: Tuple[RetrievedEvidenceItem, ...]
    warnings: Tuple[EvidenceWarning, ...]
    total_items_matched: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class GroundedQAResponse:
    """
    Structured source-grounded response for demonstration QA.
    Strictly separates verbatim source facts from grounded synthesis.
    """
    response_id: str
    question: str
    evidence_package: EvidencePackage
    source_facts: Tuple[str, ...]
    grounded_synthesis: str
    governance_disclosure: str
    is_astrological_prediction: bool = False  # MUST be False
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
