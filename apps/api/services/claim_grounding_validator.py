"""
AstroOS — Claim Grounding & Hallucination Prevention Validator
Evaluates whether AI-generated astrological interpretations are strictly grounded
in retrieved Classical EvidencePackages, computing quantitative Faithfulness Scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from apps.api.domain.knowledge_ingestion import EvidencePackage
from apps.api.services.terminology_service import TerminologyService


@dataclass(frozen=True)
class GroundingEvaluation:
    """Quantitative evaluation report for an AI-generated astrological synthesis."""
    is_grounded: bool
    faithfulness_score: float  # 0.0 to 1.0
    total_claims: int
    supported_claims: int
    unsupported_claims: tuple[str, ...]
    citation_validity: dict[str, bool]
    entities_detected: tuple[str, ...]
    unsupported_entities: tuple[str, ...]
    warnings: tuple[str, ...]


class ClaimGroundingValidator:
    """
    Automated validator for astrological text grounding and hallucination prevention.
    """

    @classmethod
    def extract_claims(cls, text: str) -> list[str]:
        """Splits synthesized text into distinct propositional sentences/claims."""
        raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        claims = [s.strip() for s in raw_sentences if len(s.strip()) > 10 and not s.startswith("GOVERNANCE DISCLOSURE")]
        return claims or [text.strip()]

    @classmethod
    def extract_citations(cls, text: str) -> list[int]:
        """Extracts cited passage numbers like [1], [2] from text."""
        matches = re.findall(r"\[(\d+)\]", text)
        return [int(m) for m in matches]

    @classmethod
    def extract_astrological_entities(cls, text: str) -> set[str]:
        """Extracts canonical grahas, rashis, and bhava numbers mentioned in text."""
        tokens = [t for t in re.split(r"\W+", text.lower()) if len(t) > 1]
        entities: set[str] = set()

        for t in tokens:
            graha = TerminologyService.resolve_graha(t)
            if graha:
                entities.add(f"graha:{graha}")
            rashi = TerminologyService.resolve_rashi(t)
            if rashi:
                entities.add(f"rashi:{rashi}")
            bhava = TerminologyService.resolve_bhava(t)
            if bhava:
                entities.add(f"bhava:{bhava}")

        return entities

    @classmethod
    def validate_grounding(
        cls,
        synthesized_text: str,
        evidence_package: EvidencePackage,
        min_faithfulness_threshold: float = 0.80,
    ) -> GroundingEvaluation:
        """
        Validates synthesized text against an EvidencePackage.
        Computes Faithfulness Score, checks citation validity, and flags unsupported claims.
        """
        claims = cls.extract_claims(synthesized_text)
        num_items = len(evidence_package.retrieved_items)

        # Build corpus of entities and tokens from retrieved items
        source_texts = [item.content.lower() for item in evidence_package.retrieved_items]
        all_source_text = " ".join(source_texts)
        source_entities = cls.extract_astrological_entities(all_source_text)

        # Also collect entities from chunk tags
        for item in evidence_package.retrieved_items:
            for g in item.retrieval_metadata.get("grahas", []):
                source_entities.add(f"graha:{g.lower()}")
            for b in item.retrieval_metadata.get("bhavas", []):
                source_entities.add(f"bhava:{b}")

        citation_validity: dict[str, bool] = {}
        all_citations = cls.extract_citations(synthesized_text)
        for c in set(all_citations):
            citation_validity[f"[{c}]"] = (1 <= c <= num_items)

        supported_claims: list[str] = []
        unsupported_claims: list[str] = []
        all_detected_entities: set[str] = set()
        unsupported_entities: set[str] = set()
        warnings: list[str] = []

        for claim in claims:
            claim_entities = cls.extract_astrological_entities(claim)
            all_detected_entities.update(claim_entities)

            # Check if entities in claim are supported in source
            unsupported_in_claim = [e for e in claim_entities if e not in source_entities]
            if unsupported_in_claim:
                unsupported_entities.update(unsupported_in_claim)

            # Check citation in claim
            claim_cites = cls.extract_citations(claim)
            has_valid_citation = any(1 <= c <= num_items for c in claim_cites)
            has_invalid_citation = any(c < 1 or c > num_items for c in claim_cites)

            # A claim is supported if:
            # 1. It cites a valid passage and doesn't introduce unsupported entities, OR
            # 2. Key entities mentioned are grounded in the source text and no invalid citations exist, OR
            # 3. It contains discourse/citation meta-statements without unsupported astrological entities.
            is_claim_valid = (
                not has_invalid_citation
                and not unsupported_in_claim
                and (
                    has_valid_citation
                    or bool(claim_entities)
                    or any(w in claim.lower() for w in ["source", "classical", "brihat", "parashara", "hora", "shastra", "passage", "documented", "chapter", "verse", "text"])
                    or len(claim.split()) <= 12
                )
            )

            if is_claim_valid:
                supported_claims.append(claim)
            else:
                unsupported_claims.append(claim)

        total_claims_count = len(claims) or 1
        faithfulness = round(len(supported_claims) / total_claims_count, 4)

        if any(not v for v in citation_validity.values()):
            invalid_citations = [k for k, v in citation_validity.items() if not v]
            warnings.append(f"Invalid citation references detected: {', '.join(invalid_citations)}.")

        if unsupported_entities:
            warnings.append(f"Unsupported astrological entities introduced: {', '.join(sorted(unsupported_entities))}.")

        if faithfulness < min_faithfulness_threshold:
            warnings.append(
                f"Faithfulness score ({faithfulness:.2%}) is below governance threshold ({min_faithfulness_threshold:.2%}). "
                "Potential hallucination or ungrounded synthesis detected."
            )

        is_grounded = (faithfulness >= min_faithfulness_threshold) and not any(not v for v in citation_validity.values())

        return GroundingEvaluation(
            is_grounded=is_grounded,
            faithfulness_score=faithfulness,
            total_claims=len(claims),
            supported_claims=len(supported_claims),
            unsupported_claims=tuple(unsupported_claims),
            citation_validity=citation_validity,
            entities_detected=tuple(sorted(all_detected_entities)),
            unsupported_entities=tuple(sorted(unsupported_entities)),
            warnings=tuple(warnings),
        )
