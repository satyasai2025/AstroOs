"""
AstroOS — Exporter

Exports normalized, validated records to AstroOS canonical dataset formats
(CSV, JSON, JSONL). Also generates metadata and quality report files.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExportResult:
    """Result of an export operation."""
    dataset_id: str
    output_path: str
    format: str
    record_count: int
    file_size_bytes: int
    checksum_sha256: str
    metadata_path: str
    quality_path: Optional[str] = None


class Exporter:
    """Exports records to AstroOS canonical formats."""

    def export_csv(
        self,
        records: List[Dict[str, Any]],
        dataset_id: str,
        output_dir: str,
        fields: Optional[List[str]] = None,
    ) -> ExportResult:
        """Export records to CSV format."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{dataset_id}_CSV.csv")

        if not records:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                f.write("")
            return ExportResult(
                dataset_id=dataset_id, output_path=output_path,
                format="CSV", record_count=0, file_size_bytes=0,
                checksum_sha256="", metadata_path="",
            )

        fieldnames = fields or list(records[0].keys())

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in records:
                row = {}
                for k, v in record.items():
                    if isinstance(v, (list, dict)):
                        row[k] = json.dumps(v)
                    else:
                        row[k] = v
                writer.writerow(row)

        file_size = os.path.getsize(output_path)
        checksum = self._compute_checksum(output_path)

        return ExportResult(
            dataset_id=dataset_id,
            output_path=output_path,
            format="CSV",
            record_count=len(records),
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            metadata_path="",
        )

    def export_json(
        self,
        records: List[Dict[str, Any]],
        dataset_id: str,
        output_dir: str,
    ) -> ExportResult:
        """Export records to JSON format."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{dataset_id}_JSON.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)

        file_size = os.path.getsize(output_path)
        checksum = self._compute_checksum(output_path)

        return ExportResult(
            dataset_id=dataset_id,
            output_path=output_path,
            format="JSON",
            record_count=len(records),
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            metadata_path="",
        )

    def export_jsonl(
        self,
        records: List[Dict[str, Any]],
        dataset_id: str,
        output_dir: str,
    ) -> ExportResult:
        """Export records to JSONL format."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{dataset_id}_JSONL.jsonl")

        with open(output_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, default=str) + "\n")

        file_size = os.path.getsize(output_path)
        checksum = self._compute_checksum(output_path)

        return ExportResult(
            dataset_id=dataset_id,
            output_path=output_path,
            format="JSONL",
            record_count=len(records),
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            metadata_path="",
        )

    def generate_metadata(
        self,
        dataset_id: str,
        output_dir: str,
        source_metadata: Dict[str, Any],
        record_count: int,
        field_count: int,
        quality_assessment: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate _metadata.json for the dataset. Returns path."""
        os.makedirs(output_dir, exist_ok=True)
        metadata_path = os.path.join(output_dir, f"{dataset_id}_CSV_metadata.json")

        metadata = {
            "dataset_id": dataset_id,
            "name": source_metadata.get("name", dataset_id),
            "description": source_metadata.get("description", ""),
            "category": source_metadata.get("category", "Research"),
            "category_code": source_metadata.get("category_code", "RS"),
            "type": source_metadata.get("type", "Cohort"),
            "type_code": source_metadata.get("type_code", "COHORT"),
            "version": source_metadata.get("version", "0.1.0"),
            "dataset_version": dataset_id,
            "provenance_tier": source_metadata.get("provenance_tier", "Derived"),
            "source_description": source_metadata.get("source_description", ""),
            "source_uris": source_metadata.get("source_uris", []),
            "collection_method": source_metadata.get("collection_method", "api_extract"),
            "curator": source_metadata.get("curator", "AstroOS Research Data Office"),
            "quality_score": quality_assessment.get("quality_score", 0.0) if quality_assessment else 0.0,
            "quality_tier": quality_assessment.get("quality_tier", "F") if quality_assessment else "F",
            "dimension_scores": quality_assessment.get("dimension_scores", {}) if quality_assessment else {},
            "validation_status": "Validated",
            "known_limitations": source_metadata.get("known_limitations", []),
            "known_biases": source_metadata.get("known_biases", []),
            "completeness_pct": quality_assessment.get("completeness_pct", 0.0) if quality_assessment else 0.0,
            "missing_fields": quality_assessment.get("missing_fields", []) if quality_assessment else [],
            "duplicate_count": quality_assessment.get("duplicate_count", 0) if quality_assessment else 0,
            "duplicate_pct": quality_assessment.get("duplicate_pct", 0.0) if quality_assessment else 0.0,
            "license_id": source_metadata.get("license_id", "CC-BY-4.0"),
            "license_name": source_metadata.get("license_name", "Creative Commons Attribution 4.0"),
            "privacy_tier": source_metadata.get("privacy_tier", "Public"),
            "confidence_tier": source_metadata.get("confidence_tier", "Estimated"),
            "contains_pii": source_metadata.get("contains_pii", False),
            "format": "CSV",
            "record_count": record_count,
            "field_count": field_count,
            "lifecycle_stage": "Candidacy",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "maintainer": "AstroOS Research Data Office",
            "changelog_ref": f"{dataset_id}_changelog.md",
        }

        if quality_assessment:
            metadata["quality_score"] = quality_assessment.get("quality_score", 0.0)
            metadata["quality_tier"] = quality_assessment.get("quality_tier", "F")

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)

        return metadata_path

    def _compute_checksum(self, file_path: str) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
