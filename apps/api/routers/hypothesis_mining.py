"""
AstroOS — Research Discovery & Hypothesis Mining Router (Priority 19)

Endpoints:
  - POST /api/v1/research/mining/mine
  - GET  /api/v1/research/mining/hypotheses
  - GET  /api/v1/research/mining/hypotheses/{hypothesis_id}
"""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.domain.hypothesis_mining import HypothesisStatus
from apps.api.schemas.hypothesis_mining import (
    AstrologicalPatternPrimitiveItem,
    DiscoveredHypothesisItem,
    HypothesisMiningReportResponse,
    ReplicationRecordItem,
    RunHypothesisMiningRequest,
)
from apps.api.services.hypothesis_mining_engine import HypothesisMiningEngine

router = APIRouter(prefix="/research/mining", tags=["Research: Discovery & Hypothesis Mining Engine"])


def _map_hypothesis(h) -> DiscoveredHypothesisItem:
    return DiscoveredHypothesisItem(
        hypothesis_id=h.hypothesis_id,
        name=h.name,
        target_objective=h.target_objective,
        pattern_primitives=[
            AstrologicalPatternPrimitiveItem(
                dimension=p.dimension.value if hasattr(p.dimension, "value") else str(p.dimension),
                operator=p.operator,
                value=p.value,
                description=p.description,
            )
            for p in h.pattern_primitives
        ],
        discovery_dataset_id=h.discovery_dataset_id,
        discovery_sample_size=h.discovery_sample_size,
        discovery_support_percent=h.discovery_support_percent,
        discovery_confidence_percent=h.discovery_confidence_percent,
        discovery_statistical_lift=h.discovery_statistical_lift,
        discovery_raw_p_value=h.discovery_raw_p_value,
        discovery_fdr_q_value=h.discovery_fdr_q_value,
        status=h.status.value if hasattr(h.status, "value") else str(h.status),
        replication_records=[
            ReplicationRecordItem(
                holdout_dataset_id=r.holdout_dataset_id,
                holdout_sample_size=r.holdout_sample_size,
                holdout_support_percent=r.holdout_support_percent,
                holdout_confidence_percent=r.holdout_confidence_percent,
                holdout_statistical_lift=r.holdout_statistical_lift,
                holdout_fdr_q_value=r.holdout_fdr_q_value,
                is_replication_confirmed=r.is_replication_confirmed,
                replicated_at=r.replicated_at,
            )
            for r in h.replication_records
        ],
        lineage_snapshot_id=h.lineage_snapshot_id,
        discovered_at=h.discovered_at,
        classical_provenance_note=h.classical_provenance_note,
    )


def _map_report(r) -> HypothesisMiningReportResponse:
    return HypothesisMiningReportResponse(
        mining_run_id=r.mining_run_id,
        discovery_dataset_id=r.discovery_dataset_id,
        holdout_dataset_id=r.holdout_dataset_id,
        target_objective=r.target_objective,
        total_combinations_evaluated=r.total_combinations_evaluated,
        candidate_hypotheses_count=r.candidate_hypotheses_count,
        replicated_validated_count=r.replicated_validated_count,
        rejected_fdr_count=r.rejected_fdr_count,
        top_hypotheses=[_map_hypothesis(h) for h in r.top_hypotheses],
        execution_time_seconds=r.execution_time_seconds,
        mined_at=r.mined_at,
    )


@router.post("/mine", response_model=HypothesisMiningReportResponse, status_code=status.HTTP_200_OK)
def run_hypothesis_mining(req: RunHypothesisMiningRequest) -> HypothesisMiningReportResponse:
    """Executes frequent pattern mining with FDR control and independent holdout cohort replication."""
    engine = HypothesisMiningEngine.get_instance()
    report = engine.run_hypothesis_mining(
        discovery_dataset_id=req.discovery_dataset_id,
        holdout_dataset_id=req.holdout_dataset_id,
        target_objective=req.target_objective,
        min_support_percent=req.min_support_percent,
        min_statistical_lift=req.min_statistical_lift,
        max_fdr_q_value=req.max_fdr_q_value,
    )
    return _map_report(report)


@router.get("/hypotheses", response_model=List[DiscoveredHypothesisItem], status_code=status.HTTP_200_OK)
def list_discovered_hypotheses(
    objective: Optional[str] = Query(None, description="Filter by target objective"),
    status_filter: Optional[str] = Query(None, description="Filter by status (e.g. REPLICATED_VALIDATED)"),
) -> List[DiscoveredHypothesisItem]:
    """Lists discovered candidate astrological hypotheses with optional status filtering."""
    engine = HypothesisMiningEngine.get_instance()
    status_enum = None
    if status_filter:
        try:
            status_enum = HypothesisStatus(status_filter.upper())
        except ValueError:
            pass

    hypotheses = engine.list_hypotheses(objective=objective, status=status_enum)
    return [_map_hypothesis(h) for h in hypotheses]


@router.get("/hypotheses/{hypothesis_id}", response_model=DiscoveredHypothesisItem, status_code=status.HTTP_200_OK)
def get_discovered_hypothesis(hypothesis_id: str) -> DiscoveredHypothesisItem:
    """Retrieves full replication and lineage provenance details for a specific hypothesis."""
    engine = HypothesisMiningEngine.get_instance()
    h = engine.get_hypothesis(hypothesis_id)
    if not h:
        raise HTTPException(status_code=404, detail=f"Hypothesis '{hypothesis_id}' not found.")
    return _map_hypothesis(h)
