"""
AstroOS — Research Benchmark Expansion Domain Models (Priority 29)

Defines domain dataclasses for:
  - Expanded Governed Research Domains (CAREER, WEALTH_FINANCE, HEALTH_VITALITY, MARRIAGE)
  - Governed Benchmark Test Cases with Independently Established Ground Truths
  - Benchmark Suite Execution Results (Algorithmic & Reference Reproduction Accuracy)
  - Mandatory Non-Medical Safety Guardrails and Prohibited Term Enforcement
  - Epistemic Scope Disclosures: Benchmark Reproduction Accuracy != Real-World Predictive Validity
  - Cross-Domain Benchmark Synthesis Reports with P11 Snapshot DAG Provenance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


MANDATORY_NON_MEDICAL_DISCLAIMER = (
    "NON_MEDICAL_SAFETY_DECLARATION: Health-related astrological evaluations are strictly exploratory "
    "academic studies of classical vitality typologies. They must NEVER be used for medical diagnosis, "
    "clinical prediction, disease prognosis, or healthcare decisions."
)

MANDATORY_BENCHMARK_EPISTEMIC_DISCLOSURE = (
    "EPISTEMIC_SCOPE_DISCLOSURE: Benchmark accuracy measures AstroOS mathematical and algorithmic "
    "fidelity in reproducing independently established reference calculations. Benchmark accuracy "
    "does NOT assert or imply empirical real-world predictive validity of future life events."
)

PROHIBITED_HEALTH_TERMS: Tuple[str, ...] = (
    "disease prediction",
    "clinical outcome",
    "diagnosis",
    "treatment",
    "medical prognosis",
)


class ExpandedResearchDomain(str, Enum):
    MARRIAGE = "MARRIAGE"                       # Relationship timing & synastry
    CAREER = "CAREER"                           # D10 Dashamsha, 10th house governance, professional milestones
    WEALTH_FINANCE = "WEALTH_FINANCE"           # 2nd/11th house Dhana yogas, Ashtakavarga gain ratios
    HEALTH_VITALITY = "HEALTH_VITALITY"         # Classical vitality typologies & constitutional indicators ONLY (Non-medical)


class ExpandedBenchmarkSuiteType(str, Enum):
    BM_CAREER_D10_PROMOTION = "BM_CAREER_D10_PROMOTION"           # D10 varga accuracy & 10th lord dasha reference calculations
    BM_WEALTH_DHANA_YOGA = "BM_WEALTH_DHANA_YOGA"                 # 2nd/11th Dhana yoga & Ashtakavarga gain/expense ratio verification
    BM_HEALTH_VITALITY_TYPOLOGY = "BM_HEALTH_VITALITY_TYPOLOGY"   # Classical vitality strength indices (Strictly Non-Medical)
    BM_CROSS_DOMAIN_COMPOSITE = "BM_CROSS_DOMAIN_COMPOSITE"       # Multi-domain unified algorithmic benchmark


@dataclass(frozen=True)
class GovernedBenchmarkTestCase:
    """A benchmark test case with an independently established ground truth reference."""
    case_id: str
    suite_type: ExpandedBenchmarkSuiteType
    domain: ExpandedResearchDomain
    description: str
    birth_datetime_iso: str
    latitude: float
    longitude: float
    independent_reference_source: str           # e.g. "BPHS_CLASSICAL_EPHEMERIS_CANON", "INDEPENDENT_ASTRONOMICAL_CATALOG"
    expected_ground_truth_output: Dict[str, Any] # Independently established reference parameters
    comparison_tolerance: float                  # e.g. 0.001 for longitudes, 0.0 for discrete states


@dataclass(frozen=True)
class DomainBenchmarkExecutionResult:
    """Empirical output of executing a domain-specific benchmark suite against ground truths."""
    run_id: str
    suite_type: ExpandedBenchmarkSuiteType
    domain: ExpandedResearchDomain
    total_cases_evaluated: int
    passed_cases_count: int
    reproduction_accuracy_percent: float       # Reproduction fidelity to reference standard
    reference_engine_source: str
    is_reference_verified: bool
    mean_latency_microseconds: float
    non_medical_safety_declaration: str
    epistemic_benchmark_disclosure: str
    p11_lineage_snapshot_id: str
    result_provenance_hash: str
    executed_at: datetime


@dataclass(frozen=True)
class CrossDomainBenchmarkReport:
    """Authoritative synthesis comparing mathematical benchmark fidelity across all life domains."""
    report_id: str
    total_suites_evaluated: int
    total_test_cases_evaluated: int
    overall_mean_reproduction_accuracy: float
    suite_results: Tuple[DomainBenchmarkExecutionResult, ...]
    non_medical_compliance_verified: bool
    p11_snapshot_id: str
    report_provenance_hash: str
    epistemic_scope_statement: str
    generated_at: datetime
