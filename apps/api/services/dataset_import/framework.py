"""
AstroOS — Import Pipeline

Orchestrates the full import pipeline:
  Source → Schema Mapping → Validation → Normalization →
  Deduplication → Quality Assessment → Export

The pipeline is generic and adapter-driven. Source-specific logic
lives entirely in the SourceAdapter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from apps.api.services.dataset_import.adapter_base import (
    ColumnMapping,
    RawRecord,
    SourceAdapter,
)
from apps.api.services.dataset_import.deduplicator import (
    DeduplicationReport,
    Deduplicator,
)
from apps.api.services.dataset_import.exporter import Exporter, ExportResult
from apps.api.services.dataset_import.normalizer import NormalizationAction, Normalizer
from apps.api.services.dataset_import.quality_scorer import QualityAssessment, QualityScorer
from apps.api.services.dataset_import.schema_mapper import SchemaMapper
from apps.api.services.dataset_import.validator import (
    Severity,
    ValidationLevel,
    ValidationResult,
    Validator,
)


@dataclass
class ImportConfig:
    """Configuration for an import run."""
    dataset_id: str
    source_file: str
    output_dir: str
    column_mappings: List[ColumnMapping]
    validation_rules: Optional[List] = None
    normalization_rules: Optional[List] = None
    dedup_key_fields: Optional[List[str]] = None
    export_format: str = "CSV"  # CSV, JSON, JSONL
    source_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ImportValidationReport:
    """Complete validation report for an import run."""
    dataset_id: str
    total_records: int = 0
    records_imported: int = 0
    records_accepted: int = 0
    validation_failures: int = 0
    normalization_actions: List = field(default_factory=list)
    duplicate_detection: Optional[DeduplicationReport] = None
    missing_mandatory_fields: List[str] = field(default_factory=list)
    quality_assessment: Optional[Dict[str, Any]] = None
    validation_result_l1: Optional[ValidationResult] = None
    validation_result_l2: Optional[ValidationResult] = None
    export_results: List[ExportResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "total_records": self.total_records,
            "records_imported": self.records_imported,
            "records_accepted": self.records_accepted,
            "validation_failures": self.validation_failures,
            "normalization_actions_count": len(self.normalization_actions),
            "duplicate_detection": {
                "total": self.duplicate_detection.total_records if self.duplicate_detection else 0,
                "unique": self.duplicate_detection.unique_records if self.duplicate_detection else 0,
                "removed": self.duplicate_detection.duplicates_removed if self.duplicate_detection else 0,
                "duplicate_pct": self.duplicate_detection.duplicate_pct if self.duplicate_detection else 0.0,
            } if self.duplicate_detection else None,
            "missing_mandatory_fields": self.missing_mandatory_fields,
            "quality": self.quality_assessment,
            "export_results": [
                {
                    "format": r.format,
                    "records": r.record_count,
                    "size": r.file_size_bytes,
                    "checksum": r.checksum_sha256,
                }
                for r in self.export_results
            ],
            "l1_validation": {
                "passed": self.validation_result_l1.passed if self.validation_result_l1 else 0,
                "failed": self.validation_result_l1.failed if self.validation_result_l1 else 0,
            } if self.validation_result_l1 else None,
            "l2_validation": {
                "passed": self.validation_result_l2.passed if self.validation_result_l2 else 0,
                "failed": self.validation_result_l2.failed if self.validation_result_l2 else 0,
            } if self.validation_result_l2 else None,
            "errors": self.errors,
        }


class ImportPipeline:
    """Orchestrates the full import pipeline.

    Usage:
        pipeline = ImportPipeline(adapter, config)
        report = pipeline.run()
    """

    def __init__(self, adapter: SourceAdapter, config: ImportConfig):
        self._adapter = adapter
        self._config = config

    def run(self) -> ImportValidationReport:
        """Execute the full import pipeline."""
        report = ImportValidationReport(dataset_id=self._config.dataset_id)

        try:
            # Step 1: Read source
            raw_records = list(self._adapter.read(self._config.source_file))
            report.total_records = len(raw_records)

            # Step 2: Schema mapping (per-record resilient)
            mapper = SchemaMapper(self._config.column_mappings)
            mapped_records = []
            mapping_errors = 0
            for r in raw_records:
                try:
                    mapped = mapper.map_record(r.data)
                    mapped_records.append(mapped)
                except (ValueError, KeyError):
                    mapping_errors += 1

            # Step 3: Validation
            validator = Validator()
            if self._config.validation_rules:
                for rule in self._config.validation_rules:
                    validator.add_rule(rule)

            l1_result = validator.validate_batch(mapped_records, ValidationLevel.L1)
            report.validation_result_l1 = l1_result
            report.validation_failures = l1_result.failed

            l2_result = validator.validate_batch(mapped_records, ValidationLevel.L2)
            report.validation_result_l2 = l2_result

            # Step 4: Normalization
            normalizer = Normalizer(self._config.normalization_rules or [])
            normalized_records, norm_actions = normalizer.normalize_batch(mapped_records)
            report.normalization_actions = norm_actions

            # Step 5: Deduplication
            if self._config.dedup_key_fields:
                dedup = Deduplicator(self._config.dedup_key_fields)
                unique_records, dedup_report = dedup.deduplicate(normalized_records)
                report.duplicate_detection = dedup_report
            else:
                unique_records = normalized_records

            report.records_accepted = len(unique_records)

            # Step 6: Quality assessment
            scorer = QualityScorer()
            all_fields = list(unique_records[0].keys()) if unique_records else []
            required_fields = mapper.get_required_fields()

            validation_pass_rate = 1.0 - (l1_result.failed / max(l1_result.total, 1))

            quality = scorer.score(
                records=unique_records,
                required_fields=required_fields,
                all_fields=all_fields,
                validation_pass_rate=validation_pass_rate,
            )
            report.quality_assessment = quality.to_dict()

            # Step 7: Export
            exporter = Exporter()
            if self._config.export_format.upper() == "CSV":
                result = exporter.export_csv(
                    unique_records, self._config.dataset_id, self._config.output_dir
                )
            elif self._config.export_format.upper() == "JSON":
                result = exporter.export_json(
                    unique_records, self._config.dataset_id, self._config.output_dir
                )
            elif self._config.export_format.upper() == "JSONL":
                result = exporter.export_jsonl(
                    unique_records, self._config.dataset_id, self._config.output_dir
                )
            else:
                raise ValueError(f"Unsupported format: {self._config.export_format}")

            report.export_results.append(result)

            # Generate metadata
            source_meta = self._adapter.get_source_metadata(self._config.source_file)
            if self._config.source_metadata:
                source_meta.update(self._config.source_metadata)

            metadata_path = exporter.generate_metadata(
                self._config.dataset_id,
                self._config.output_dir,
                source_meta,
                len(unique_records),
                len(all_fields),
                report.quality_assessment,
            )
            report.export_results[0].metadata_path = metadata_path

            report.records_imported = len(unique_records)
            report.missing_mandatory_fields = quality.missing_fields

        except Exception as e:
            report.errors.append(str(e))
            import traceback
            report.errors.append(traceback.format_exc())

        return report
