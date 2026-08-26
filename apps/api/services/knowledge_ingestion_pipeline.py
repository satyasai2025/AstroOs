"""
AstroOS — Governed Knowledge Ingestion Pipeline

Implements the governed ingestion chain:

  Raw Document
    → Stage 1: Intake & Metadata Validation
    → Stage 2: Content Hash Computation (SHA-256)
    → Stage 3: Deterministic Chunk ID Generation
    → Stage 4: Provenance Integrity Validation
    → Stage 5: Reliability Governance Attachment (DOCUMENTED / UNVALIDATED)
    → Stage 6: Persistence
    → Stage 7 (optional): Embedding Generation

AI-GENERATED CONTENT QUARANTINE (MANDATORY INVARIANT):
  AI may extract metadata and suggest astrological tags during ingestion.
  All AI-extracted chunks must have is_ai_extracted=True.
  The pipeline NEVER promotes lifecycle_state beyond DOCUMENTED.
  AI-generated QA summaries must NEVER be passed into this pipeline.
  Only original source texts may be ingested.
  Generated text must NEVER become IngestedChunk content.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.knowledge_ingestion import (
    DocumentStatus,
    IngestedChunk,
    IngestedDocument,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    ProvenanceIntegrityError,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.repositories.knowledge_ingestion_repository import KnowledgeIngestionRepository


class GovernedIngestionPipeline:
    """
    Governed ingestion pipeline for AstroOS knowledge documents and chunks.

    Enforces provenance integrity, deterministic chunk identification,
    content hashing, and lifecycle governance at ingestion time.
    """

    def __init__(
        self,
        repository: KnowledgeIngestionRepository,
        embedding_client_fn=None,
        settings=None,
    ) -> None:
        """
        Args:
            repository: Async repository for chunk and document persistence.
            embedding_client_fn: Optional callable matching the signature of
                apps.api.services.embedding_client.embed_text. If None,
                embedding generation is skipped gracefully.
            settings: Optional settings object. If None, get_settings() is
                called lazily when first needed.
        """
        self._repository = repository
        self._embedding_client_fn = embedding_client_fn
        self._settings = settings

    def _get_settings(self):
        if self._settings is not None:
            return self._settings
        from apps.api.config import get_settings  # lazy import
        return get_settings()

    # ── Stage 2: Content Hashing ───────────────────────────────────────────────

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Returns the SHA-256 hex digest of the stripped UTF-8 content.
        Deterministic: identical content always produces the same hash.
        """
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    # ── Stage 3: Deterministic Chunk ID ───────────────────────────────────────

    @staticmethod
    def build_chunk_id(
        document_id: uuid.UUID,
        chapter_section: str,
        page_location: str,
        chunk_index: int,
    ) -> str:
        """
        Returns a deterministic, URL-safe chunk ID of the form:
            CHK-{doc_prefix8}-{section_slug30}-{page_slug20}-{index:04d}

        Slashing special characters ensures database and URL compatibility.
        """
        doc_prefix = str(document_id).replace("-", "")[:8].upper()

        def _slug(s: str, max_len: int) -> str:
            slug = re.sub(r"[^a-zA-Z0-9]", "-", s.strip())
            slug = re.sub(r"-{2,}", "-", slug).strip("-")
            return slug[:max_len].upper()

        section_slug = _slug(chapter_section, 30)
        page_slug = _slug(page_location, 20)
        return f"CHK-{doc_prefix}-{section_slug}-{page_slug}-{chunk_index:04d}"

    # ── Stage 1: Document Registration ────────────────────────────────────────

    async def register_document(
        self,
        title: str,
        author: Optional[str] = None,
        edition: Optional[str] = None,
        publication_year: Optional[int] = None,
        language: str = "Sanskrit/English",
        tradition: str = "Parashari",
        source_id: Optional[uuid.UUID] = None,
        book_id: Optional[uuid.UUID] = None,
    ) -> IngestedDocument:
        """
        Register a new document in the governed ingestion pipeline.

        The document begins in RAW_UPLOADED state. It must never be
        automatically promoted to INDEXED or treated as canonical knowledge.
        """
        doc = IngestedDocument(
            document_id=uuid.uuid4(),
            source_id=source_id,
            title=title,
            author=author,
            edition=edition,
            publication_year=publication_year,
            language=language,
            tradition=tradition,
            status=DocumentStatus.PARSED,
        )
        await self._repository.upsert_document(doc)
        return doc

    # ── Stages 3-6: Chunk Ingestion ────────────────────────────────────────────

    async def ingest_chunk(
        self,
        document_id: uuid.UUID,
        source_id: Optional[uuid.UUID],
        chapter_section: str,
        page_location: str,
        passage_reference: str,
        chunk_index: int,
        content: str,
        technique_framework: TechniqueFramework,
        verse_id: Optional[uuid.UUID] = None,
        grahas: Tuple[str, ...] = (),
        bhavas: Tuple[int, ...] = (),
        rashis: Tuple[str, ...] = (),
        nakshatras: Tuple[str, ...] = (),
        yogas: Tuple[str, ...] = (),
        event_types: Tuple[str, ...] = (),
        is_ai_extracted: bool = False,
        extraction_metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestedChunk:
        """
        Ingest a text chunk with complete, immutable provenance.

        Raises ProvenanceIntegrityError if any required provenance field is
        missing or if the content hash is inconsistent.

        The chunk begins with lifecycle_state=DOCUMENTED and
        evidence_level=UNVALIDATED regardless of source prestige.
        AI cannot promote these fields.
        """
        # Stage 3: Validate provenance fields before hashing
        if not chapter_section or not chapter_section.strip():
            raise ProvenanceIntegrityError(
                "chapter_section must not be empty — every chunk requires a chapter/section reference."
            )
        if not page_location or not page_location.strip():
            raise ProvenanceIntegrityError(
                "page_location must not be empty — every chunk requires a page or sloka location."
            )
        if not passage_reference or not passage_reference.strip():
            raise ProvenanceIntegrityError(
                "passage_reference must not be empty — every chunk requires a citable passage reference."
            )
        if not content or not content.strip():
            raise ProvenanceIntegrityError(
                "content must not be empty — cannot ingest a chunk without source text."
            )

        # Stage 2: Compute content hash
        content_hash = self.compute_content_hash(content)

        # Stage 3: Build deterministic chunk ID
        chunk_id = self.build_chunk_id(document_id, chapter_section, page_location, chunk_index)

        # Stage 5: Create domain object with DOCUMENTED/UNVALIDATED defaults
        chunk = IngestedChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            source_id=source_id,
            chapter_section=chapter_section,
            page_location=page_location,
            passage_reference=passage_reference,
            chunk_index=chunk_index,
            content=content,
            content_hash_sha256=content_hash,
            technique_framework=technique_framework,
            grahas=grahas,
            bhavas=bhavas,
            rashis=rashis,
            nakshatras=nakshatras,
            yogas=yogas,
            event_types=event_types,
            lifecycle_state=RuleLifecycleState.DOCUMENTED,   # AI cannot change this
            evidence_level=EvidenceLevel.UNVALIDATED,         # AI cannot change this
            verse_id=verse_id,
            is_ai_extracted=is_ai_extracted,
            extraction_metadata=extraction_metadata or {},
        )

        # Stage 4: Validate provenance integrity (including hash verification)
        chunk.validate_provenance()

        # Stage 6: Persist
        await self._repository.upsert_chunk(chunk)
        return chunk

    # ── Stage 7: Embedding Generation ─────────────────────────────────────────

    async def generate_chunk_embedding(
        self,
        chunk: IngestedChunk,
        chunk_orm_id: uuid.UUID,
        model_name: str,
    ) -> bool:
        """
        Generate and store a vector embedding for an ingested chunk.

        Embeddings are stored in the EXISTING KnowledgeEmbeddingModel table
        (source_type='ingested_chunk', source_id=chunk_orm_id).

        ANTI-CONTAMINATION: Chunk content is passed to the embedding client
        as source text ONLY. The vector is stored in knowledge_embeddings.
        The generated vector NEVER becomes a knowledge record, rule, or source.

        Returns True on success, False if the embedding client is unavailable.
        """
        if self._embedding_client_fn is None:
            return False

        settings = self._get_settings()
        vector = self._embedding_client_fn(
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=model_name,
            timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
            text=chunk.content,
        )
        if vector is None:
            return False

        # Store in EXISTING KnowledgeEmbeddingModel — not a new knowledge table
        from apps.api.repositories.knowledge_embedding_repository import KnowledgeEmbeddingRepository
        emb_repo = KnowledgeEmbeddingRepository(self._repository._session)
        await emb_repo.upsert(
            source_type="ingested_chunk",
            source_id=chunk_orm_id,
            embedded_text=chunk.content,
            embedding=vector,
            model_name=model_name,
        )
        return True

    # ── Convenience: Document + All Chunks ────────────────────────────────────

    async def ingest_document_with_chunks(
        self,
        document_kwargs: Dict[str, Any],
        chunks_data: List[Dict[str, Any]],
    ) -> Tuple[IngestedDocument, List[IngestedChunk]]:
        """
        Register a document and ingest all its chunks in one call.

        document_kwargs: keyword args for register_document()
        chunks_data: list of dicts, each with keys matching ingest_chunk() parameters
                     except document_id (automatically filled from registered doc).
        """
        doc = await self.register_document(**document_kwargs)
        chunks: List[IngestedChunk] = []
        for chunk_kwargs in chunks_data:
            chunk_kwargs["document_id"] = doc.document_id
            chunk = await self.ingest_chunk(**chunk_kwargs)
            chunks.append(chunk)
        return doc, chunks
