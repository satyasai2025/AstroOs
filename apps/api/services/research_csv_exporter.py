"""
AstroOS — Research CSV/JSON Exporter with Knowledge Citations

Exports research snapshot data as CSV or JSON where each snapshot row/data
includes linked knowledge citations. Pure formatting layer — no calculations.

Usage:
    exporter = CsvResearchExporter()
    csv_result = exporter.export_snapshots(snapshots, citations)
    json_result = JsonResearchExporter().export_snapshots(snapshots, citations)
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.domain.export_domain import ExportFormat, ExportResult
from apps.api.domain.knowledge import KnowledgeSearchResult
from apps.api.domain.research import AstrologicalSnapshot


def _snapshot_to_flat_rows(
    snapshot: AstrologicalSnapshot,
    citations: Optional[tuple[KnowledgeSearchResult, ...]] = None,
) -> list[dict[str, Any]]:
    """
    Convert one AstrologicalSnapshot into one or more flat dict rows
    suitable for CSV serialisation.

    Each row represents one data point (planet position, yoga, etc.)
    so rows can cite specific knowledge sources per data point.

    Returns a list of rows (typically 1 for a summary row, one per planet
    for detailed export).
    """
    rows: list[dict[str, Any]] = []
    base = {
        "snapshot_id": str(snapshot.id),
        "project_id": str(snapshot.project_id),
        "chart_id": str(snapshot.chart_id),
        "label": snapshot.label or "",
        "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else "",
        "snapshot_version": snapshot.snapshot_version,
    }

    # ── Citation references ──────────────────────────────────────────────
    citation_refs: list[str] = []
    citation_sources: list[str] = []
    if citations:
        for c in citations:
            ref = c.book_title or c.entity_type
            citation_refs.append(f"{ref} ({c.relevance:.1f})")
            citation_sources.append(f"{ref}: {c.snippet[:200]}")

    base["citation_references"] = "; ".join(citation_refs) if citation_refs else ""
    base["citation_details"] = "; ".join(citation_sources) if citation_sources else ""

    # ── Chart-level summary row ──────────────────────────────────────────
    if snapshot.chart_ref:
        base["ayanamsa"] = snapshot.chart_ref.ayanamsa_system or ""
        base["house_system"] = snapshot.chart_ref.house_system or ""
    rows.append(dict(base))

    # ── Per-planet rows ──────────────────────────────────────────────────
    if snapshot.chart_ref and snapshot.chart_ref.planets:
        for p in snapshot.chart_ref.planets:
            row = dict(base)
            row["data_type"] = "planet"
            row["name"] = p.planet
            row["rashi"] = p.rashi
            row["house_number"] = p.house_number
            row["longitude_deg"] = float(p.sidereal_longitude) if p.sidereal_longitude else ""
            row["is_retrograde"] = "yes" if p.is_retrograde else "no"
            row["dignity"] = p.dignity.value if p.dignity else ""
            rows.append(row)

    # ── Per-yoga rows ────────────────────────────────────────────────────
    if snapshot.yogas:
        for y in snapshot.yogas:
            row = dict(base)
            row["data_type"] = "yoga"
            row["name"] = y.name
            row["yoga_id"] = y.yoga_id
            row["is_present"] = "yes" if y.is_present else "no"
            row["strength"] = y.strength.value if y.strength else ""
            row["category"] = y.category
            rows.append(row)

    return rows


class CsvResearchExporter:
    """Exports research snapshot data as CSV with knowledge citations."""

    @staticmethod
    def export_snapshots(
        snapshots: tuple[AstrologicalSnapshot, ...],
        citations: Optional[dict[uuid.UUID, tuple[KnowledgeSearchResult, ...]]] = None,
        project_title: str = "research_export",
    ) -> ExportResult:
        """
        Export snapshots to CSV with citations embedded per row.

        Args:
            snapshots: The snapshots to export.
            citations: Optional mapping of snapshot_id -> knowledge citations.
            project_title: Used in the filename.

        Returns:
            ExportResult with CSV content.
        """
        output = io.StringIO()
        writer = None

        for snapshot in snapshots:
            snap_citations = citations.get(snapshot.id) if citations else None
            rows = _snapshot_to_flat_rows(snapshot, snap_citations)
            for row in rows:
                if writer is None:
                    writer = csv.DictWriter(output, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

        content = output.getvalue()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"{project_title}_export_{date_str}.csv"

        return ExportResult(
            format=ExportFormat.CSV,
            content=content,
            filename=filename,
            mime_type="text/csv",
            size_bytes=len(content.encode("utf-8")),
        )

    @staticmethod
    def export_snapshot_summary(
        snapshots: tuple[AstrologicalSnapshot, ...],
        citations: Optional[dict[uuid.UUID, tuple[KnowledgeSearchResult, ...]]] = None,
        project_title: str = "research_export",
    ) -> ExportResult:
        """
        Export a summary view (one row per snapshot, no per-planet/yoga detail).
        """
        output = io.StringIO()
        writer = None

        for snapshot in snapshots:
            snap_citations = citations.get(snapshot.id) if citations else None
            base = {
                "snapshot_id": str(snapshot.id),
                "chart_id": str(snapshot.chart_id),
                "label": snapshot.label or "",
                "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else "",
            }

            # Citation references
            citation_refs: list[str] = []
            if snap_citations:
                for c in snap_citations:
                    citation_refs.append(f"{c.book_title or c.entity_type} ({c.relevance:.1f})")
            base["citation_references"] = "; ".join(citation_refs) if citation_refs else ""

            # Counts
            base["yoga_count"] = len(snapshot.yogas) if snapshot.yogas else 0
            base["planet_count"] = len(snapshot.chart_ref.planets) if snapshot.chart_ref and snapshot.chart_ref.planets else 0

            if writer is None:
                writer = csv.DictWriter(output, fieldnames=list(base.keys()))
                writer.writeheader()
            writer.writerow(base)

        content = output.getvalue()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"{project_title}_summary_{date_str}.csv"

        return ExportResult(
            format=ExportFormat.CSV,
            content=content,
            filename=filename,
            mime_type="text/csv",
            size_bytes=len(content.encode("utf-8")),
        )


class JsonResearchExporter:
    """Exports research snapshot data as structured JSON with knowledge citations."""

    @staticmethod
    def export_snapshots(
        snapshots: tuple[AstrologicalSnapshot, ...],
        citations: Optional[dict[uuid.UUID, tuple[KnowledgeSearchResult, ...]]] = None,
        project_title: str = "research_export",
    ) -> ExportResult:
        """Export snapshots as JSON with nested citations."""
        doc: dict[str, Any] = {
            "export_type": "research_snapshots",
            "project_title": project_title,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "snapshots": [],
        }

        for snapshot in snapshots:
            snap_citations = citations.get(snapshot.id) if citations else None
            entry = {
                "snapshot_id": str(snapshot.id),
                "chart_id": str(snapshot.chart_id),
                "label": snapshot.label,
                "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else None,
                "snapshot_version": snapshot.snapshot_version,
                "citations": [
                    {
                        "source": c.book_title or c.entity_type,
                        "reference": str(c.entity_id),
                        "text": c.snippet,
                        "relevance": c.relevance,
                        "tradition": c.tradition,
                    }
                    for c in (snap_citations or [])
                ],
            }

            # Include chart summary if available
            if snapshot.chart_ref:
                entry["chart"] = {
                    "ayanamsa": snapshot.chart_ref.ayanamsa_system,
                    "house_system": snapshot.chart_ref.house_system,
                    "planets": [
                        {
                            "name": p.planet,
                            "rashi": p.rashi,
                            "house": p.house_number,
                            "longitude": float(p.sidereal_longitude) if p.sidereal_longitude else None,
                            "retrograde": p.is_retrograde,
                            "dignity": p.dignity.value if p.dignity else None,
                        }
                        for p in (snapshot.chart_ref.planets or [])
                    ],
                }

            # Include yoga summary
            if snapshot.yogas:
                entry["yogas"] = [
                    {
                        "yoga_id": y.yoga_id,
                        "name": y.name,
                        "is_present": y.is_present,
                        "strength": y.strength.value if y.strength else None,
                        "category": y.category,
                    }
                    for y in snapshot.yogas
                ]

            doc["snapshots"].append(entry)

        content = json.dumps(doc, indent=2, default=str)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"{project_title}_export_{date_str}.json"

        return ExportResult(
            format=ExportFormat.JSON,
            content=content,
            filename=filename,
            mime_type="application/json",
            size_bytes=len(content.encode("utf-8")),
        )
