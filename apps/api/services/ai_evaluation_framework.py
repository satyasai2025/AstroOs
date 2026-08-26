"""
AstroOS — AI Grounding & Evaluation Framework
Provides quantitative benchmarking for:
  1. Faithfulness & Claim Grounding
  2. Citation Precision & Recall
  3. Sanskrit/English Terminology Resolution Accuracy
  4. Technique Boundary Isolation
  5. Anti-Contamination Invariant Verification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.knowledge_ingestion import GroundedQAResponse
from apps.api.domain.knowledge_reliability import TechniqueFramework
from apps.api.services.claim_grounding_validator import ClaimGroundingValidator, GroundingEvaluation
from apps.api.services.terminology_service import TerminologyService


@dataclass(frozen=True)
class AIBenchmarkResult:
    """Benchmark evaluation summary for an AI astrological reasoning output."""
    overall_pass: bool
    faithfulness_score: float         # 0.0 to 1.0
    citation_precision: float         # 0.0 to 1.0 (valid citations / total citations)
    terminology_accuracy: float       # 0.0 to 1.0
    technique_isolation_passed: bool  # True if no cross-technique leakage
    anti_contamination_verified: bool # True if is_astrological_prediction is False & not in KB
    grounding_details: GroundingEvaluation
    summary: str


class AIEvaluationFramework:
    """
    Standard evaluation harness for verifying AI reasoning quality,
    source faithfulness, and strict governance invariants in AstroOS.
    """

    @classmethod
    def evaluate_qa_response(
        cls,
        qa_response: GroundedQAResponse,
        expected_technique: Optional[TechniqueFramework] = None,
        min_faithfulness: float = 0.80,
    ) -> AIBenchmarkResult:
        """
        Evaluates a GroundedQAResponse on all 5 governance & grounding criteria.
        """
        # 1. Faithfulness & Claim Grounding
        grounding_eval = ClaimGroundingValidator.validate_grounding(
            synthesized_text=qa_response.grounded_synthesis,
            evidence_package=qa_response.evidence_package,
            min_faithfulness_threshold=min_faithfulness,
        )

        # 2. Citation Precision
        all_cites = ClaimGroundingValidator.extract_citations(qa_response.grounded_synthesis)
        if all_cites:
            valid_cites = sum(1 for c in all_cites if 1 <= c <= len(qa_response.evidence_package.retrieved_items))
            citation_precision = round(valid_cites / len(all_cites), 4)
        else:
            citation_precision = 1.0  # no false citations

        # 3. Terminology Resolution
        detected_entities = grounding_eval.entities_detected
        if detected_entities:
            supported = len(detected_entities) - len(grounding_eval.unsupported_entities)
            terminology_accuracy = round(max(0.0, supported / len(detected_entities)), 4)
        else:
            terminology_accuracy = 1.0

        # 4. Technique Boundary Isolation
        technique_isolation_passed = True
        if expected_technique is not None:
            # Verify that retrieved items and QA response match expected technique framework
            for item in qa_response.evidence_package.retrieved_items:
                if item.technique_framework != expected_technique:
                    technique_isolation_passed = False
                    break

        # 5. Anti-Contamination Verification
        # Invariant: is_astrological_prediction MUST be False and governance disclosure MUST be present
        anti_contamination_verified = (
            qa_response.is_astrological_prediction is False
            and bool(qa_response.governance_disclosure)
            and "NOT an astrological prediction" in qa_response.governance_disclosure
        )

        overall_pass = (
            grounding_eval.is_grounded
            and citation_precision >= 0.90
            and terminology_accuracy >= 0.80
            and technique_isolation_passed
            and anti_contamination_verified
        )

        summary = (
            f"AI Evaluation: {'PASS' if overall_pass else 'FAIL'} | "
            f"Faithfulness: {grounding_eval.faithfulness_score:.1%} | "
            f"Citation Precision: {citation_precision:.1%} | "
            f"Terminology Accuracy: {terminology_accuracy:.1%} | "
            f"Technique Isolation: {technique_isolation_passed} | "
            f"Anti-Contamination: {anti_contamination_verified}"
        )

        return AIBenchmarkResult(
            overall_pass=overall_pass,
            faithfulness_score=grounding_eval.faithfulness_score,
            citation_precision=citation_precision,
            terminology_accuracy=terminology_accuracy,
            technique_isolation_passed=technique_isolation_passed,
            anti_contamination_verified=anti_contamination_verified,
            grounding_details=grounding_eval,
            summary=summary,
        )
