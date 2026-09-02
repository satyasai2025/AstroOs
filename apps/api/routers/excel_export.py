"""
AstroOS — Excel Export & Office.js Integration Router.

Provides HTTP endpoints to:
1. Stream fully configured .xlsx workbooks (Kurma_Display + tblVedhaMap ListObject).
2. Serve structured 2D array payloads and reference tables for Office.js clients.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.excel_export_service import ExcelExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/excel", tags=["Excel & Office.js Integration"])


@router.get(
    "/export-kurma",
    summary="Download pre-configured Kurma Chakra & tblVedhaMap Excel workbook (.xlsx)",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
def export_kurma_workbook(
    dt_iso: Optional[str] = Query(default=None, description="ISO datetime string, defaults to UTC now"),
    ayanamsa: str = Query(default="lahiri", description="Ayanamsa system (lahiri, raman, etc.)"),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Response:
    """Generates and streams an Excel workbook containing the Kurma_Display sheet and tblVedhaMap ListObject."""
    dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00")) if dt_iso else datetime.now(timezone.utc)
    service = ExcelExportService(wrapper)
    file_bytes = service.generate_kurma_workbook_bytes(dt=dt, ayanamsa=ayanamsa)

    timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
    filename = f"AstroOS_Kurma_Display_{timestamp_str}.xlsx"

    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get(
    "/vedha-map-data",
    summary="Get raw 112-pada SBC vedha cross-reference data for Office.js ListObject population",
    status_code=status.HTTP_200_OK,
)
def get_vedha_map_data() -> Dict[str, Any]:
    """Returns the 112-pada Sarvatobhadra Chakra cross-reference table."""
    service = ExcelExportService()
    rows = service.get_vedha_map_rows()
    return {
        "count": len(rows),
        "headers": ["pada112", "position", "left", "front", "right"],
        "rows": rows,
    }


@router.get(
    "/kurma-display-payload",
    summary="Get 2D batched array values for Office.js Kurma_Display range updates",
    status_code=status.HTTP_200_OK,
)
def get_kurma_display_payload(
    dt_iso: Optional[str] = Query(default=None, description="ISO datetime string, defaults to UTC now"),
    ayanamsa: str = Query(default="lahiri"),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> Dict[str, Any]:
    """Returns pre-formatted 2D arrays ready for single-call Office.js range.values assignment."""
    dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00")) if dt_iso else datetime.now(timezone.utc)
    service = ExcelExportService(wrapper)
    state = service._kurma_engine.evaluate_state(dt, ayanamsa)

    summary_2d: List[List[Any]] = []
    for s in state.sectors:
        summary_2d.append([
            s.direction.value.capitalize(),
            ", ".join(s.nakshatras),
            ", ".join(s.traditional_regions),
            ", ".join(s.transiting_malefics) or "None",
            ", ".join(s.transiting_benefics) or "None",
            "AFFLICTED" if s.is_afflicted else "BENIGN",
            str(s.severity),
            s.risk_summary,
        ])

    return {
        "evaluated_at": state.evaluated_at.isoformat(),
        "summary": state.summary,
        "highest_risk_directions": [d.value for d in state.highest_risk_directions],
        "summary_range": "A6:H14",
        "summary_values": summary_2d,
    }
