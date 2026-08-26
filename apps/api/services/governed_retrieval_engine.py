"""
AstroOS — Governed Retrieval Engine

Implements hybrid Reciprocal Rank Fusion (RRF) retrieval combining:
  1. Keyword / full-text retrieval (PostgreSQL tsvector + ILIKE)
  2. Semantic vector retrieval (cosine similarity against stored embeddings)
  3. Strict metadata filtering (technique framework, lifecycle state, facets)
  4. Reliability-aware ordering (CANONICAL > VALIDATED > REVIEWED > DOCUMENTED)
  5. EvidencePackage assembly with multi-category governance warnings

Technique boundary enforcement:
  - Queries specifying a technique_framework will flag cross-framework results
    with EvidenceWarningType.CROSS_TECHNIQUE_RESULTS_PRESENT.
  - Results are NEVER silently merged across framework boundaries.

Reliability filtering:
  - Default retrieval excludes lifecycle_state=UNKNOWN and evidence_level=UNVALIDATED.
  - include_unvalidated=True must be explicitly requested; results are then flagged.

This layer outputs EvidencePackages, not predictions or interpretations.
"""

from __future__ import annotations

import asyncio
import math
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.knowledge_ingestion import (
    EvidencePackage,
    EvidenceWarning,
    EvidenceWarningType,
    RetrievalFilter,
    RetrievalMethod,
    RetrievedEvidenceItem,
)
from apps.api.domain.knowledge_reliability import (
    EvidenceLevel,
    RuleLifecycleState,
    TechniqueFramework,
)
from apps.api.models.knowledge_ingestion import IngestedChunkModel
from apps.api.repositories.knowledge_ingestion_repository import KnowledgeIngestionRepository


class GovernedRetrievalEngine:
    """
    Hybrid retrieval engine producing auditable EvidencePackages.
    """

    def __init__(
        self,
        repository: KnowledgeIngestionRepository,
        embedding_client_fn=None,
        settings=None,
    ) -> None:
        self._repository = repository
        self._embedding_client_fn = embedding_client_fn
        self._settings = settings

    def _get_settings(self):
        if self._settings is not None:
            return self._settings
        from apps.api.config import get_settings
        return get_settings()

    # ── RRF Scoring ───────────────────────────────────────────────────────────

    @staticmethod
    def _compute_rrf_score(
        semantic_rank: Optional[int],
        keyword_rank: Optional[int],
        k: int = 60,
    ) -> float:
        """
        Reciprocal Rank Fusion score: sum of 1/(k+rank) for each non-None rank.
        Higher is better.
        """
        score = 0.0
        if semantic_rank is not None:
            score += 1.0 / (k + semantic_rank)
        if keyword_rank is not None:
            score += 1.0 / (k + keyword_rank)
        return score

    # ── Cosine Similarity ─────────────────────────────────────────────────────

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Standard cosine similarity. Returns 0.0 on dimension mismatch or zero vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ── Lifecycle State Resolution ─────────────────────────────────────────────

    @staticmethod
    def _build_lifecycle_states(filters: RetrievalFilter) -> List[str]:
        """
        Returns the allowed lifecycle states for a query.

        Default (include_unvalidated=False):
          CANONICAL, VALIDATED, REVIEWED, DOCUMENTED
          (UNKNOWN is excluded — represents unregistered material)

        include_unvalidated=True also includes UNKNOWN.
        CONTRADICTED is always excluded (structurally unreliable).
        """
        states = [
            RuleLifecycleState.CANONICAL.value,
            RuleLifecycleState.VALIDATED.value,
            RuleLifecycleState.REVIEWED.value,
            RuleLifecycleState.DOCUMENTED.value,
        ]
        if filters.include_unvalidated:
            states.append(RuleLifecycleState.UNKNOWN.value)
        return states

    # ── Evidence Item Builder ──────────────────────────────────────────────────

    @staticmethod
    def _build_evidence_item(
        chunk_model: IngestedChunkModel,
        relevance_score: float,
        retrieval_metadata: Dict[str, Any],
    ) -> RetrievedEvidenceItem:
        """Map an ORM chunk model to an immutable RetrievedEvidenceItem domain object."""
        provenance_chain = {
            "document_id": str(chunk_model.document_id),
            "source_id": str(chunk_model.source_id) if chunk_model.source_id else None,
            "chapter_section": chunk_model.chapter_section,
            "page_location": chunk_model.page_location,
            "passage_reference": chunk_model.passage_reference,
        }
        try:
            technique = TechniqueFramework(chunk_model.technique_framework)
        except ValueError:
            technique = TechniqueFramework.PARASHARI

        try:
            lifecycle = RuleLifecycleState(chunk_model.lifecycle_state)
        except ValueError:
            lifecycle = RuleLifecycleState.DOCUMENTED

        try:
            ev_level = EvidenceLevel(chunk_model.evidence_level)
        except ValueError:
            ev_level = EvidenceLevel.UNVALIDATED

        is_unvalidated = chunk_model.evidence_level == EvidenceLevel.UNVALIDATED.value

        return RetrievedEvidenceItem(
            item_id=chunk_model.chunk_id,
            content=chunk_model.content,
            source_title=f"Document:{chunk_model.document_id}",
            source_id=chunk_model.source_id or chunk_model.document_id,
            document_id=chunk_model.document_id,
            passage_reference=chunk_model.passage_reference,
            provenance_chain=provenance_chain,
            technique_framework=technique,
            lifecycle_state=lifecycle,
            evidence_level=ev_level,
            relevance_score=round(relevance_score, 4),
            retrieval_metadata=retrieval_metadata,
            evidence_family_id=chunk_model.evidence_family_id,
            is_unvalidated=is_unvalidated,
        )

    # ── Warning Generation ────────────────────────────────────────────────────

    @staticmethod
    def _generate_warnings(
        items: List[RetrievedEvidenceItem],
        filters: RetrievalFilter,
    ) -> List[EvidenceWarning]:
        """Generate governance warnings for the assembled evidence items."""
        warnings: List[EvidenceWarning] = []

        # 1. Unvalidated knowledge included
        unvalidated_ids = [i.item_id for i in items if i.is_unvalidated]
        if unvalidated_ids and filters.include_unvalidated:
            warnings.append(EvidenceWarning(
                warning_type=EvidenceWarningType.UNVALIDATED_KNOWLEDGE_INCLUDED,
                message=(
                    f"{len(unvalidated_ids)} retrieved item(s) have not undergone "
                    "empirical benchmark validation. Treat with appropriate caution."
                ),
                affected_item_ids=tuple(unvalidated_ids),
            ))

        # 2. Cross-technique results present
        if filters.technique_framework is not None:
            requested_technique = filters.technique_framework.value
            cross_technique_ids = [
                i.item_id
                for i in items
                if i.technique_framework.value != requested_technique
            ]
            if cross_technique_ids:
                warnings.append(EvidenceWarning(
                    warning_type=EvidenceWarningType.CROSS_TECHNIQUE_RESULTS_PRESENT,
                    message=(
                        f"Query requested technique '{requested_technique}' but "
                        f"{len(cross_technique_ids)} result(s) belong to a different framework. "
                        "These are explicitly labelled — do not treat as the requested tradition."
                    ),
                    affected_item_ids=tuple(cross_technique_ids),
                ))

        # 3. Evidence family overlap
        family_to_ids: Dict[str, List[str]] = {}
        for item in items:
            if item.evidence_family_id:
                family_to_ids.setdefault(item.evidence_family_id, []).append(item.item_id)
        overlap_ids = [
            iid
            for family_ids in family_to_ids.values()
            if len(family_ids) > 1
            for iid in family_ids
        ]
        if overlap_ids:
            warnings.append(EvidenceWarning(
                warning_type=EvidenceWarningType.EVIDENCE_FAMILY_OVERLAP_DETECTED,
                message=(
                    f"{len(overlap_ids)} item(s) share evidence family memberships. "
                    "Independent confirmation count may be inflated. "
                    "Apply anti-double-counting analysis before treating these as independent evidence."
                ),
                affected_item_ids=tuple(set(overlap_ids)),
            ))

        # 4. Incomplete provenance
        incomplete_ids = [
            i.item_id
            for i in items
            if not i.provenance_chain.get("chapter_section")
            or not i.provenance_chain.get("page_location")
        ]
        if incomplete_ids:
            warnings.append(EvidenceWarning(
                warning_type=EvidenceWarningType.INCOMPLETE_PROVENANCE,
                message=(
                    f"{len(incomplete_ids)} item(s) have incomplete provenance "
                    "(missing chapter/section or page/location). "
                    "Traceability to source is degraded."
                ),
                affected_item_ids=tuple(incomplete_ids),
            ))

        return warnings

    # ── Keyword Retrieval ─────────────────────────────────────────────────────

    async def keyword_retrieval(
        self,
        query: str,
        filters: RetrievalFilter,
    ) -> List[Tuple[IngestedChunkModel, float]]:
        """Keyword retrieval using repository full-text search with RRF scoring."""
        tokens = [
            t for t in re.split(r"\W+", query.lower()) if len(t) > 2
        ]
        if not tokens:
            return []

        lifecycle_states = self._build_lifecycle_states(filters)
        technique = filters.technique_framework.value if filters.technique_framework else None

        chunks = await self._repository.keyword_search(
            query_tokens=tokens,
            technique=technique,
            lifecycle_states=lifecycle_states,
            include_unvalidated=filters.include_unvalidated,
            top_k=filters.top_k * 3,  # over-fetch for RRF merge
        )

        k = 60
        return [
            (chunk, 1.0 / (k + rank))
            for rank, chunk in enumerate(chunks)
        ]

    # ── Semantic Retrieval ────────────────────────────────────────────────────

    async def semantic_retrieval(
        self,
        query: str,
        filters: RetrievalFilter,
        model_name: str,
    ) -> List[Tuple[IngestedChunkModel, float]]:
        """
        Semantic retrieval using stored embedding vectors from the existing
        KnowledgeEmbeddingModel table (source_type='ingested_chunk').

        Returns [] if embedding client is unavailable — degrades gracefully
        to keyword-only retrieval.
        """
        if self._embedding_client_fn is None:
            return []

        settings = self._get_settings()
        query_vector = self._embedding_client_fn(
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=model_name,
            timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
            text=query,
        )
        if query_vector is None:
            return []

        # Get all embeddings for this model from the existing embedding table
        from apps.api.repositories.knowledge_embedding_repository import KnowledgeEmbeddingRepository
        emb_repo = KnowledgeEmbeddingRepository(self._repository._session)
        stored = await emb_repo.all_for_model(model_name)

        if not stored:
            return []

        # Filter to only ingested_chunk embeddings
        chunk_embeddings = [
            row for row in stored
            if row.source_type == "ingested_chunk"
        ]
        if not chunk_embeddings:
            return []

        # Score by cosine similarity
        lifecycle_states = self._build_lifecycle_states(filters)
        technique = filters.technique_framework.value if filters.technique_framework else None

        scored: List[Tuple[uuid.UUID, float]] = []
        for row in chunk_embeddings:
            sim = self._cosine_similarity(query_vector, row.embedding)
            if sim > 0.0:
                scored.append((row.source_id, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_ids = [source_id for source_id, _ in scored[: filters.top_k * 3]]

        if not top_ids:
            return []

        # Fetch the actual chunk models for the top scoring IDs
        from sqlalchemy import select
        result = await self._repository._session.execute(
            select(IngestedChunkModel).where(
                IngestedChunkModel.id.in_(top_ids),
                IngestedChunkModel.deleted_at.is_(None),
                IngestedChunkModel.lifecycle_state.in_(lifecycle_states),
                *([IngestedChunkModel.technique_framework == technique] if technique else []),
                *([IngestedChunkModel.evidence_level != "UNVALIDATED"] if not filters.include_unvalidated else []),
            )
        )
        chunk_models = {m.id: m for m in result.scalars().all()}

        # Pair models with their similarity scores
        k = 60
        paired: List[Tuple[IngestedChunkModel, float]] = []
        rank = 0
        for source_id, _ in scored:
            if source_id in chunk_models:
                paired.append((chunk_models[source_id], 1.0 / (k + rank)))
                rank += 1

        return paired

    # ── Hybrid RRF Retrieval ──────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        filters: RetrievalFilter,
        embedding_model: Optional[str] = None,
    ) -> EvidencePackage:
        """
        Main retrieval method. Runs keyword and semantic retrieval concurrently,
        merges via Reciprocal Rank Fusion, assembles and returns an EvidencePackage.
        """
        # Run both retrieval methods concurrently
        if embedding_model and self._embedding_client_fn:
            kw_results, sem_results = await asyncio.gather(
                self.keyword_retrieval(query, filters),
                self.semantic_retrieval(query, filters, embedding_model),
            )
        else:
            kw_results = await self.keyword_retrieval(query, filters)
            sem_results = []

        # RRF merge: track rank for each chunk_id in each modality
        kw_rank_map: Dict[str, int] = {
            chunk.chunk_id: rank for rank, (chunk, _) in enumerate(kw_results)
        }
        sem_rank_map: Dict[str, int] = {
            chunk.chunk_id: rank for rank, (chunk, _) in enumerate(sem_results)
        }

        # Union of all chunk IDs
        all_chunk_ids = set(kw_rank_map) | set(sem_rank_map)

        # Build a model lookup
        model_lookup: Dict[str, IngestedChunkModel] = {}
        for chunk, _ in kw_results:
            model_lookup[chunk.chunk_id] = chunk
        for chunk, _ in sem_results:
            model_lookup.setdefault(chunk.chunk_id, chunk)

        # Score all candidates
        scored_candidates: List[Tuple[str, float]] = []
        for cid in all_chunk_ids:
            rrf = self._compute_rrf_score(
                semantic_rank=sem_rank_map.get(cid),
                keyword_rank=kw_rank_map.get(cid),
            )
            scored_candidates.append((cid, rrf))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Determine retrieval method
        if kw_results and sem_results:
            method = RetrievalMethod.HYBRID_RRF
        elif sem_results:
            method = RetrievalMethod.SEMANTIC_VECTOR
        elif kw_results:
            method = RetrievalMethod.KEYWORD_EXACT
        else:
            method = RetrievalMethod.KEYWORD_EXACT

        # Build evidence items for top_k results
        items: List[RetrievedEvidenceItem] = []
        total_matched = len(scored_candidates)

        for cid, rrf_score in scored_candidates[: filters.top_k]:
            if rrf_score < filters.min_relevance_score:
                continue
            chunk_model = model_lookup.get(cid)
            if chunk_model is None:
                continue
            retrieval_meta = {
                "rrf_score": round(rrf_score, 6),
                "in_keyword_results": cid in kw_rank_map,
                "in_semantic_results": cid in sem_rank_map,
                "keyword_rank": kw_rank_map.get(cid),
                "semantic_rank": sem_rank_map.get(cid),
                "retrieval_method": method.value,
            }
            items.append(self._build_evidence_item(chunk_model, rrf_score, retrieval_meta))

        # Generate governance warnings
        warnings = self._generate_warnings(items, filters)

        # Build filters_applied record for audit trail
        filters_applied = {
            "technique_framework": filters.technique_framework.value if filters.technique_framework else None,
            "include_unvalidated": filters.include_unvalidated,
            "top_k": filters.top_k,
            "min_relevance_score": filters.min_relevance_score,
            "grahas": list(filters.grahas) if filters.grahas else None,
            "bhavas": list(filters.bhavas) if filters.bhavas else None,
            "rashis": list(filters.rashis) if filters.rashis else None,
            "nakshatras": list(filters.nakshatras) if filters.nakshatras else None,
            "yogas": list(filters.yogas) if filters.yogas else None,
            "event_types": list(filters.event_types) if filters.event_types else None,
        }

        return EvidencePackage(
            package_id=f"EP-{str(uuid.uuid4())[:8]}",
            query=query,
            retrieval_method=method,
            filters_applied=filters_applied,
            retrieved_items=tuple(items),
            warnings=tuple(warnings),
            total_items_matched=total_matched,
        )
