"""
AstroOS — Empirical Pattern Discovery API Router
=================================================
Serves statistically validated pattern discovery findings from the 66,732-case dataset.
"""

from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/research/patterns", tags=["Research Pattern Discovery"])


@router.get("")
def get_discovered_patterns() -> dict[str, Any]:
    """
    Returns the complete statistical pattern discovery report
    including categories, sample sizes, lift scores, and Wilson confidence.
    """
    report_path = os.path.join("data", "discovered_patterns_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Pattern discovery report not found. Run discovery pipeline first.",
        )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read pattern report: {e}")
