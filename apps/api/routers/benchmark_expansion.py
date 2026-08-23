"""
AstroOS — Research Benchmark Expansion Router (Priority 29)

Endpoints for:
  - Querying governed benchmark test cases across Career, Wealth, and Vitality domains.
  - Executing domain benchmark suites against independently established ground truths.
  - Generating cross-domain synthesis reports with mandatory non-medical safety disclosures.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.domain.benchmark_expansion import ExpandedBenchmarkSuiteType
from apps.api.schemas.benchmark_expansion import (
    CrossDomainBenchmarkReportResponse,
    DomainBenchmarkExecutionResultSchema,
    GovernedBenchmarkTestCaseSchema,
    RunBenchmarkSuiteRequest,
)
from apps.api.services.benchmark_expansion_engine import BenchmarkExpansionEngine

router = APIRouter(
    prefix="/api/v1/research/benchmark-expansion",
    tags=["Research Benchmark Expansion"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("/cases", response_model=List[GovernedBenchmarkTestCaseSchema])
def list_governed_benchmark_cases():
    """
    List all governed test cases with independently established ground truth references.
    """
    cases = BenchmarkExpansionEngine.get_instance().list_test_cases()
    return [
        GovernedBenchmarkTestCaseSchema(
            case_id=c.case_id,
            suite_type=c.suite_type.value,
            domain=c.domain.value,
            description=c.description,
            birth_datetime_iso=c.birth_datetime_iso,
            latitude=c.latitude,
            longitude=c.longitude,
            independent_reference_source=c.independent_reference_source,
            expected_ground_truth_output=c.expected_ground_truth_output,
            comparison_tolerance=c.comparison_tolerance,
        )
        for c in cases
    ]


@router.post("/run", response_model=DomainBenchmarkExecutionResultSchema)
def run_benchmark_suite(request: RunBenchmarkSuiteRequest):
    """
    Execute a domain benchmark suite against independent ground truth references.
    """
    suite_enum = ExpandedBenchmarkSuiteType(request.suite_type)
    res = BenchmarkExpansionEngine.get_instance().run_benchmark_suite(
        suite_type=suite_enum,
        snapshot_id=request.snapshot_id,
    )

    return DomainBenchmarkExecutionResultSchema(
        run_id=res.run_id,
        suite_type=res.suite_type.value,
        domain=res.domain.value,
        total_cases_evaluated=res.total_cases_evaluated,
        passed_cases_count=res.passed_cases_count,
        reproduction_accuracy_percent=res.reproduction_accuracy_percent,
        reference_engine_source=res.reference_engine_source,
        is_reference_verified=res.is_reference_verified,
        mean_latency_microseconds=res.mean_latency_microseconds,
        non_medical_safety_declaration=res.non_medical_safety_declaration,
        epistemic_benchmark_disclosure=res.epistemic_benchmark_disclosure,
        p11_lineage_snapshot_id=res.p11_lineage_snapshot_id,
        result_provenance_hash=res.result_provenance_hash,
        executed_at=res.executed_at.isoformat(),
    )


@router.post("/report", response_model=CrossDomainBenchmarkReportResponse)
def generate_cross_domain_report(snapshot_id: Optional[str] = None):
    """
    Execute all domain benchmark suites and generate an integrated cross-domain report.
    """
    rep = BenchmarkExpansionEngine.get_instance().generate_cross_domain_report(
        snapshot_id=snapshot_id
    )

    return CrossDomainBenchmarkReportResponse(
        report_id=rep.report_id,
        total_suites_evaluated=rep.total_suites_evaluated,
        total_test_cases_evaluated=rep.total_test_cases_evaluated,
        overall_mean_reproduction_accuracy=rep.overall_mean_reproduction_accuracy,
        suite_results=[
            DomainBenchmarkExecutionResultSchema(
                run_id=r.run_id,
                suite_type=r.suite_type.value,
                domain=r.domain.value,
                total_cases_evaluated=r.total_cases_evaluated,
                passed_cases_count=r.passed_cases_count,
                reproduction_accuracy_percent=r.reproduction_accuracy_percent,
                reference_engine_source=r.reference_engine_source,
                is_reference_verified=r.is_reference_verified,
                mean_latency_microseconds=r.mean_latency_microseconds,
                non_medical_safety_declaration=r.non_medical_safety_declaration,
                epistemic_benchmark_disclosure=r.epistemic_benchmark_disclosure,
                p11_lineage_snapshot_id=r.p11_lineage_snapshot_id,
                result_provenance_hash=r.result_provenance_hash,
                executed_at=r.executed_at.isoformat(),
            )
            for r in rep.suite_results
        ],
        non_medical_compliance_verified=rep.non_medical_compliance_verified,
        p11_snapshot_id=rep.p11_snapshot_id,
        report_provenance_hash=rep.report_provenance_hash,
        epistemic_scope_statement=rep.epistemic_scope_statement,
        generated_at=rep.generated_at.isoformat(),
    )


@router.get("/latest", response_model=CrossDomainBenchmarkReportResponse)
def get_latest_cross_domain_report():
    """
    Get or evaluate the latest cross-domain benchmark expansion report.
    """
    return generate_cross_domain_report()
