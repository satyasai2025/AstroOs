"""
AstroOS — Source-Grounded QA Service

Generates source-grounded explanations from an EvidencePackage.

ANTI-CONTAMINATION INVARIANT (MANDATORY — NEVER VIOLATE):
  AI-generated answers produced by this service must NEVER be:
    - inserted into IngestedChunk
    - inserted into KnowledgeEmbeddingModel
    - stored as authoritative source evidence
    - used as source_id in any knowledge record
    - retrieved as knowledge in future queries

  This invariant is enforced STRUCTURALLY:
    - This service holds NO reference to KnowledgeIngestionRepository.
    - This service holds NO reference to KnowledgeEmbeddingRepository.
    - The GroundedQAResponse is always marked is_astrological_prediction=False.
    - Generated summaries are returned to the caller only — never persisted.

  The response format explicitly distinguishes:
    === SOURCE FACTS ===         (verbatim retrieved passages with citations)
    === GROUNDED SYNTHESIS ===   (AI-generated summary, clearly labelled)
    === GOVERNANCE DISCLOSURE === (lifecycle states, warnings, limitations)
"""

from __future__ import annotations

import uuid
from typing import Optional, Tuple

from apps.api.domain.knowledge_ingestion import (
    EvidencePackage,
    GroundedQAResponse,
    RetrievalFilter,
)
from apps.api.services.governed_retrieval_engine import GovernedRetrievalEngine


class SourceGroundedQAService:
    """
    Source-grounded QA demonstration service.

    Takes a question, retrieves an EvidencePackage, builds structured
    source citations, and optionally generates a grounded synthesis via
    a local LLM. Never stores any generated output.
    """

    def __init__(
        self,
        retrieval_engine: GovernedRetrievalEngine,
        llm_client_fn=None,
        settings=None,
    ) -> None:
        """
        Args:
            retrieval_engine: The governed retrieval engine to use.
            llm_client_fn: Optional callable for grounded synthesis generation.
                Signature: (base_url, model, timeout_seconds, grounding_text, instruction) -> str|None
                If None, returns 'LLM not configured. Refer to source facts above.'
            settings: Optional settings object.
        """
        self._retrieval_engine = retrieval_engine
        self._llm_client_fn = llm_client_fn
        self._settings = settings
        # STRUCTURAL INVARIANT: no write repositories are held.
        # If a code change adds _ingestion_repository or _embedding_repository here,
        # it violates the anti-contamination contract.

    def _get_settings(self):
        if self._settings is not None:
            return self._settings
        from apps.api.config import get_settings
        return get_settings()

    async def answer(
        self,
        question: str,
        retrieval_filter: RetrievalFilter,
        embedding_model: Optional[str] = None,
    ) -> GroundedQAResponse:
        """
        Generate a source-grounded answer for a knowledge question.

        Flow:
          1. Retrieve EvidencePackage via GovernedRetrievalEngine.
          2. Build verbatim source_facts from retrieved passages.
          3. Optionally generate grounded_synthesis via local LLM.
          4. Build governance_disclosure with lifecycle states and warnings.
          5. Return GroundedQAResponse — NEVER persist generated text.

        Returns:
            GroundedQAResponse with is_astrological_prediction=False (always).
        """
        # Step 1: Retrieve evidence
        evidence_package = await self._retrieval_engine.retrieve(
            query=question,
            filters=retrieval_filter,
            embedding_model=embedding_model,
        )

        # Step 2: Handle empty evidence
        if not evidence_package.retrieved_items:
            return GroundedQAResponse(
                response_id=f"QA-{str(uuid.uuid4())[:8]}",
                question=question,
                evidence_package=evidence_package,
                source_facts=(),
                grounded_synthesis=(
                    "No evidence found in the governed knowledge corpus for this query. "
                    "The question may require knowledge that has not yet been ingested, "
                    "or may be outside the scope of the current knowledge base."
                ),
                governance_disclosure=(
                    "GOVERNANCE: No classical source passages were retrieved. "
                    "This response contains no source citations. "
                    "This is NOT an astrological prediction."
                ),
                is_astrological_prediction=False,
            )

        # Step 3: Build verbatim source facts (numbered, with passage citations)
        source_facts: Tuple[str, ...] = tuple(
            f"[{i + 1}] {item.passage_reference} "
            f"(Technique: {item.technique_framework.value}, "
            f"Lifecycle: {item.lifecycle_state.value}, "
            f"Evidence: {item.evidence_level.value}): "
            f"{item.content[:400]}"
            for i, item in enumerate(evidence_package.retrieved_items)
        )

        grounding_text = "\n\n".join(source_facts)

        # Step 4: Generate grounded synthesis
        grounded_synthesis: str
        if self._llm_client_fn is not None:
            settings = self._get_settings()
            instruction = (
                f"Answer using ONLY the numbered source passages below. "
                f"Cite each passage by number [1], [2], etc. "
                f"Do NOT make astrological predictions. "
                f"Do NOT add information not present in the passages. "
                f"Question: {question}"
            )
            try:
                generated = self._llm_client_fn(
                    base_url=settings.LOCAL_LLM_BASE_URL,
                    model=settings.LOCAL_LLM_MODEL,
                    timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
                    grounding_text=grounding_text,
                    instruction=instruction,
                )
                if generated and generated.strip():
                    grounded_synthesis = generated.strip()
                else:
                    grounded_synthesis = "LLM unavailable. Refer to source facts above."
            except Exception:  # noqa: BLE001
                grounded_synthesis = "LLM unavailable. Refer to source facts above."
        else:
            grounded_synthesis = "LLM not configured. Refer to source facts above."

        # Step 5: Build governance disclosure
        lifecycle_states_seen = sorted({
            item.lifecycle_state.value
            for item in evidence_package.retrieved_items
        })
        warning_summaries = [
            f"  • {w.warning_type.value}: {w.message}"
            for w in evidence_package.warnings
        ]

        governance_disclosure = (
            f"GOVERNANCE DISCLOSURE\n"
            f"  Retrieved items: {len(evidence_package.retrieved_items)}\n"
            f"  Lifecycle states present: {', '.join(lifecycle_states_seen)}\n"
            f"  Retrieval method: {evidence_package.retrieval_method.value}\n"
        )
        if warning_summaries:
            governance_disclosure += "  Warnings:\n" + "\n".join(warning_summaries) + "\n"
        governance_disclosure += (
            "  IMPORTANT: The 'Grounded Synthesis' above is AI-generated text based on the "
            "source passages listed. It is NOT authoritative classical knowledge. "
            "It has NOT been stored in the knowledge corpus. "
            "This response is NOT an astrological prediction."
        )

        # ANTI-CONTAMINATION: grounded_synthesis is returned to caller only.
        # It is NEVER passed to any repository write method.
        return GroundedQAResponse(
            response_id=f"QA-{str(uuid.uuid4())[:8]}",
            question=question,
            evidence_package=evidence_package,
            source_facts=source_facts,
            grounded_synthesis=grounded_synthesis,
            governance_disclosure=governance_disclosure,
            is_astrological_prediction=False,  # MUST ALWAYS BE FALSE — do not change
        )
