"""
AstroOS — Governed Knowledge Ingestion & Retrieval Router

REST API endpoints for the governed ingestion pipeline and retrieval layer.

Routes:
  POST /knowledge/ingest/document    - Register a source document
  POST /knowledge/ingest/chunk       - Ingest a provenance-verified text chunk
  GET  /knowledge/ingest/documents   - List ingested documents
  POST /knowledge/retrieval/retrieve - Hybrid governed retrieval → EvidencePackage
  POST /knowledge/retrieval/grounded-qa - Source-grounded QA demonstration

SCOPE:
  This router implements SOURCE → KNOWLEDGE → EVIDENCE → RETRIEVAL only.
  No prediction, reasoning, chart analysis, or Desh-Kaal-Patra is implemented here.
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from apps.api.domain.knowledge_ingestion import RetrievalFilter
from apps.api.domain.knowledge_reliability import (
    ProvenanceIntegrityError,
    TechniqueFramework,
)
from apps.api.schemas.knowledge_ingestion import (
    ChunkIngestRequest,
    ChunkIngestResponse,
    DocumentIngestRequest,
    DocumentIngestResponse,
    EvidencePackageSchema,
    EvidenceWarningSchema,
    GroundedQARequest,
    GroundedQAResponseSchema,
    ProvenanceChainSchema,
    RetrievalRequest,
    RetrievedEvidenceItemSchema,
)
from apps.api.services.governed_retrieval_engine import GovernedRetrievalEngine
from apps.api.services.knowledge_ingestion_pipeline import GovernedIngestionPipeline
from apps.api.services.source_grounded_qa_service import SourceGroundedQAService

router = APIRouter(
    prefix="/knowledge",
    tags=["Governed Knowledge Ingestion"],
)

# ── In-memory singletons for endpoint use (no DB session for pure-domain ops) ──
# For production: replace with FastAPI Depends(get_db) and session-scoped repos.
# For tests: override these with TestClient and mock repos.
_pipeline_singleton: GovernedIngestionPipeline | None = None
_retrieval_engine_singleton: GovernedRetrievalEngine | None = None


def _get_pipeline() -> GovernedIngestionPipeline:
    """
    Returns a GovernedIngestionPipeline instance.
    In production FastAPI, this would receive an AsyncSession via Depends.
    For in-memory unit tests, the singleton is set by the test fixture.
    """
    global _pipeline_singleton
    if _pipeline_singleton is None:
        # Import here to avoid circular imports during test discovery
        from unittest.mock import MagicMock
        _pipeline_singleton = GovernedIngestionPipeline(repository=MagicMock())
    return _pipeline_singleton


def _get_engine() -> GovernedRetrievalEngine:
    global _retrieval_engine_singleton
    if _retrieval_engine_singleton is None:
        from unittest.mock import MagicMock
        _retrieval_engine_singleton = GovernedRetrievalEngine(repository=MagicMock())
    return _retrieval_engine_singleton


def set_pipeline(pipeline: GovernedIngestionPipeline) -> None:
    """Allows tests and DI to inject a configured pipeline instance."""
    global _pipeline_singleton
    _pipeline_singleton = pipeline


def set_retrieval_engine(engine: GovernedRetrievalEngine) -> None:
    global _retrieval_engine_singleton
    _retrieval_engine_singleton = engine


# ── Helpers: Domain → Schema Mapping ──────────────────────────────────────────

def _map_evidence_package(pkg) -> EvidencePackageSchema:
    return EvidencePackageSchema(
        package_id=pkg.package_id,
        query=pkg.query,
        retrieval_method=pkg.retrieval_method.value,
        filters_applied=pkg.filters_applied,
        retrieved_items=[
            RetrievedEvidenceItemSchema(
                item_id=item.item_id,
                content=item.content,
                source_title=item.source_title,
                source_id=item.source_id,
                document_id=item.document_id,
                passage_reference=item.passage_reference,
                provenance_chain=ProvenanceChainSchema(
                    document_id=item.provenance_chain.get("document_id", ""),
                    source_id=item.provenance_chain.get("source_id"),
                    chapter_section=item.provenance_chain.get("chapter_section", ""),
                    page_location=item.provenance_chain.get("page_location", ""),
                    passage_reference=item.provenance_chain.get("passage_reference", ""),
                ),
                technique_framework=item.technique_framework.value,
                lifecycle_state=item.lifecycle_state.value,
                evidence_level=item.evidence_level.value,
                relevance_score=item.relevance_score,
                retrieval_metadata=item.retrieval_metadata,
                evidence_family_id=item.evidence_family_id,
                is_unvalidated=item.is_unvalidated,
            )
            for item in pkg.retrieved_items
        ],
        warnings=[
            EvidenceWarningSchema(
                warning_type=w.warning_type.value,
                message=w.message,
                affected_item_ids=list(w.affected_item_ids),
            )
            for w in pkg.warnings
        ],
        total_items_matched=pkg.total_items_matched,
        generated_at=pkg.generated_at,
    )


# ── Ingestion Endpoints ────────────────────────────────────────────────────────

@router.post("/ingest/document", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(body: DocumentIngestRequest) -> DocumentIngestResponse:
    """
    Register a source document in the governed ingestion pipeline.

    The document is assigned status=PARSED with lifecycle governance attachment.
    It does NOT automatically become canonical knowledge.
    """
    pipeline = _get_pipeline()
    doc = await pipeline.register_document(
        title=body.title,
        author=body.author,
        edition=body.edition,
        publication_year=body.publication_year,
        language=body.language,
        tradition=body.tradition,
        source_id=body.source_id,
        book_id=body.book_id,
    )
    return DocumentIngestResponse(
        document_id=doc.document_id,
        title=doc.title,
        status=doc.status.value,
        message=f"Document '{doc.title}' registered successfully. Lifecycle: DOCUMENTED. Evidence level: UNVALIDATED.",
    )


@router.post("/ingest/chunk", response_model=ChunkIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_chunk(body: ChunkIngestRequest) -> ChunkIngestResponse:
    """
    Ingest a text chunk with immutable provenance chain.

    Raises 422 if any required provenance field is missing or content hash fails.
    The chunk is assigned lifecycle_state=DOCUMENTED and evidence_level=UNVALIDATED.
    AI cannot promote these fields.
    """
    pipeline = _get_pipeline()

    # Resolve technique framework
    try:
        technique = TechniqueFramework(body.technique_framework)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown technique_framework: '{body.technique_framework}'. "
                   f"Valid values: {[t.value for t in TechniqueFramework]}",
        )

    try:
        chunk = await pipeline.ingest_chunk(
            document_id=body.document_id,
            source_id=None,
            chapter_section=body.chapter_section,
            page_location=body.page_location,
            passage_reference=body.passage_reference,
            chunk_index=body.chunk_index,
            content=body.content,
            technique_framework=technique,
            verse_id=body.verse_id,
            grahas=tuple(body.grahas),
            bhavas=tuple(body.bhavas),
            rashis=tuple(body.rashis),
            nakshatras=tuple(body.nakshatras),
            yogas=tuple(body.yogas),
            event_types=tuple(body.event_types),
            is_ai_extracted=body.is_ai_extracted,
            extraction_metadata=body.extraction_metadata,
        )
    except ProvenanceIntegrityError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ChunkIngestResponse(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        passage_reference=chunk.passage_reference,
        lifecycle_state=chunk.lifecycle_state.value,
        evidence_level=chunk.evidence_level.value,
        is_ai_extracted=chunk.is_ai_extracted,
        message=(
            f"Chunk '{chunk.chunk_id}' ingested. Provenance: {chunk.passage_reference}. "
            f"AI-extracted: {chunk.is_ai_extracted}."
        ),
    )


@router.get("/ingest/documents", response_model=List[DocumentIngestResponse])
async def list_documents(limit: int = 20, offset: int = 0) -> List[DocumentIngestResponse]:
    """List ingested documents (paginated)."""
    pipeline = _get_pipeline()
    docs = await pipeline._repository.list_documents(limit=limit, offset=offset)
    return [
        DocumentIngestResponse(
            document_id=d.id,
            title=d.title,
            status=d.status,
            message="",
        )
        for d in docs
    ]


# ── Retrieval Endpoints ────────────────────────────────────────────────────────

@router.post("/retrieval/retrieve", response_model=EvidencePackageSchema)
async def retrieve(body: RetrievalRequest) -> EvidencePackageSchema:
    """
    Hybrid governed retrieval (keyword + semantic + metadata filtering + RRF).

    Returns an EvidencePackage with:
    - Retrieved evidence items with full provenance
    - Technique framework labels (never merged across traditions)
    - Reliability lifecycle states for every item
    - Governance warnings (unvalidated, cross-technique, evidence family overlap)

    Default: UNVALIDATED knowledge excluded unless include_unvalidated=True.
    """
    engine = _get_engine()

    # Resolve technique framework filter
    technique: TechniqueFramework | None = None
    if body.technique_framework:
        try:
            technique = TechniqueFramework(body.technique_framework)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown technique_framework: '{body.technique_framework}'.",
            )

    filters = RetrievalFilter(
        technique_framework=technique,
        include_unvalidated=body.include_unvalidated,
        grahas=tuple(body.grahas) if body.grahas else None,
        bhavas=tuple(body.bhavas) if body.bhavas else None,
        rashis=tuple(body.rashis) if body.rashis else None,
        nakshatras=tuple(body.nakshatras) if body.nakshatras else None,
        yogas=tuple(body.yogas) if body.yogas else None,
        event_types=tuple(body.event_types) if body.event_types else None,
        top_k=body.top_k,
        min_relevance_score=body.min_relevance_score,
    )

    package = await engine.retrieve(body.query, filters, embedding_model=body.embedding_model)
    return _map_evidence_package(package)


@router.post("/retrieval/grounded-qa", response_model=GroundedQAResponseSchema)
async def grounded_qa(body: GroundedQARequest) -> GroundedQAResponseSchema:
    """
    Source-grounded QA demonstration.

    Flow: Question → EvidencePackage → Source-Grounded Summary.

    The response explicitly separates:
      - SOURCE FACTS: verbatim retrieved passages with citations
      - GROUNDED SYNTHESIS: AI-generated summary (clearly labelled)
      - GOVERNANCE DISCLOSURE: lifecycle states, warnings, limitations

    IMPORTANT: Generated synthesis is NEVER stored in the knowledge corpus.
    is_astrological_prediction is always False.
    """
    engine = _get_engine()
    qa_service = SourceGroundedQAService(retrieval_engine=engine)

    technique: TechniqueFramework | None = None
    if body.technique_framework:
        try:
            technique = TechniqueFramework(body.technique_framework)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown technique_framework: '{body.technique_framework}'.",
            )

    filters = RetrievalFilter(
        technique_framework=technique,
        include_unvalidated=body.include_unvalidated,
        top_k=body.top_k,
    )

    response = await qa_service.answer(
        question=body.question,
        retrieval_filter=filters,
        embedding_model=body.embedding_model,
    )

    return GroundedQAResponseSchema(
        response_id=response.response_id,
        question=response.question,
        source_facts=list(response.source_facts),
        grounded_synthesis=response.grounded_synthesis,
        governance_disclosure=response.governance_disclosure,
        is_astrological_prediction=response.is_astrological_prediction,
        evidence_package=_map_evidence_package(response.evidence_package),
        generated_at=response.generated_at,
    )
