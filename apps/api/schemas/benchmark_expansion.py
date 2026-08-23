"""
AstroOS — Research Benchmark Expansion Schemas (Priority 29)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GovernedBenchmarkTestCaseSchema(BaseModel):
    case_id: str
    suite_type: str
    domain: str
    description: str
    birth_datetime_iso: str
    latitude: float
    longitude: float
    independent_reference_source: str
    expected_ground_truth_output: Dict[str, Any]
    comparison_tolerance: float


class DomainBenchmarkExecutionResultSchema(BaseModel):
    run_id: str
    suite_type: str
    domain: str
    total_cases_evaluated: int
    passed_cases_count: int
    reproduction_accuracy_percent: float
    reference_engine_source: str
    is_reference_verified: bool
    mean_latency_microseconds: float
    non_medical_safety_declaration: str
    epistemic_benchmark_disclosure: str
    p11_lineage_snapshot_id: str
    result_provenance_hash: str
    executed_at: str


class CrossDomainBenchmarkReportResponse(BaseModel):
    report_id: str
    total_suites_evaluated: int
    total_test_cases_evaluated: int
    overall_mean_reproduction_accuracy: float
    suite_results: List[DomainBenchmarkExecutionResultSchema]
    non_medical_compliance_verified: bool
    p11_snapshot_id: str
    report_provenance_hash: str
    epistemic_scope_statement: str
    generated_at: str


class RunBenchmarkSuiteRequest(BaseModel):
    suite_type: str = Field(description="BM_CAREER_D10_PROMOTION, BM_WEALTH_DHANA_YOGA, BM_HEALTH_VITALITY_TYPOLOGY, BM_CROSS_DOMAIN_COMPOSITE")
    snapshot_id: Optional[str] = Field(default=None, description="Optional P11 snapshot ID")
