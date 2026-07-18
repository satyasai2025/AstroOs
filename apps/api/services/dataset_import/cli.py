"""
AstroOS — Dataset Import CLI

Standalone command-line interface for validating and importing datasets.

Usage:
    python -m apps.api.services.dataset_import.cli validate <file> [options]
    python -m apps.api.services.dataset_import.cli import <file> <dataset-id> [options]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from apps.api.services.dataset_import.adapters.csv_adapter import CsvAdapter
from apps.api.services.dataset_import.adapters.excel_adapter import ExcelAdapter
from apps.api.services.dataset_import.adapters.json_adapter import JsonAdapter
from apps.api.services.dataset_import.validator import (
    ValidationLevel,
    Validator,
    latitude_in_range,
    longitude_in_range,
    required_field_not_none,
    field_not_empty,
    enum_value,
)


def _detect_adapter(file_path: str):
    """Detect the appropriate adapter from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    adapters = {
        ".csv": CsvAdapter,
        ".xlsx": ExcelAdapter,
        ".xls": ExcelAdapter,
        ".json": JsonAdapter,
        ".jsonl": JsonAdapter,
    }
    adapter_cls = adapters.get(ext)
    if adapter_cls is None:
        print(f"Error: Unsupported file extension '{ext}'", file=sys.stderr)
        print("Supported: .csv, .xlsx, .xls, .json, .jsonl", file=sys.stderr)
        sys.exit(1)
    return adapter_cls()


def _build_standard_validator() -> Validator:
    """Build a Validator with standard rules for birth chart data."""
    v = Validator()
    # Required fields
    for field in ["birth_latitude", "birth_longitude", "birth_day", "birth_month", "birth_year"]:
        v.add_rule(required_field_not_none(field))
    # Range checks
    v.add_rule(latitude_in_range())
    v.add_rule(longitude_in_range())
    # Not empty
    v.add_rule(field_not_empty("subject_first_name"))
    # Enum values
    v.add_rule(enum_value("subject_gender", {"M", "F", "male", "female", "other"}))
    return v


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a dataset file and print the report."""
    file_path = args.file
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    # Detect adapter
    adapter = _detect_adapter(file_path)

    # Read records
    try:
        records = list(adapter.read(file_path))
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    print(f"File: {file_path}")
    print(f"Adapter: {adapter.get_adapter_name()}")
    print(f"Records read: {len(records)}")
    print()

    if not records:
        print("No records to validate.")
        return 0

    # Get column definitions
    cols = adapter.get_column_definitions(file_path)
    print(f"Columns detected: {len(cols)}")
    for c in cols:
        print(f"  {c.name:25s} {c.data_type:8s} nullable={c.nullable}")
    print()

    # Run validation
    validator = Validator()
    if args.rules == "standard":
        validator = _build_standard_validator()
    elif args.rules == "none":
        validator = Validator()
    # Add any custom rules from the --schema flag (simplified here)

    # Convert RawRecords to dicts for validation
    record_dicts = [r.data for r in records]

    l1_result = validator.validate_batch(record_dicts, ValidationLevel.L1)
    l2_result = validator.validate_batch(record_dicts, ValidationLevel.L2)

    print(f"L1 (Schema) Validation: {l1_result.passed} passed, {l1_result.failed} failed")
    if l1_result.violations:
        print("  Violations:")
        for v in l1_result.violations[:10]:  # show first 10
            print(f"    [{v.severity.value}] Row {v.record_index}: {v.message}")
        if len(l1_result.violations) > 10:
            print(f"    ... and {len(l1_result.violations) - 10} more")

    print(f"L2 (Quality) Validation: {l2_result.passed} passed, {l2_result.failed} failed")
    if l2_result.violations:
        print("  Violations:")
        for v in l2_result.violations[:5]:
            print(f"    [{v.severity.value}] Row {v.record_index}: {v.message}")

    # Summary
    total_checks = l1_result.total + l2_result.total
    total_passed = l1_result.passed + l2_result.passed
    total_failed = l1_result.failed + l2_result.failed
    success_rate = (total_passed / total_checks * 100) if total_checks > 0 else 0

    print()
    print(f"Total checks: {total_checks}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success rate: {success_rate:.1f}%")

    if args.verbose:
        print()
        print("Raw Records (first 3):")
        for r in records[:3]:
            print(f"  [{r.source_index}] {json.dumps(r.data, default=str)[:120]}...")

    return 0 if total_failed == 0 else 1


def cmd_import(args: argparse.Namespace) -> int:
    """Import a dataset file through the full pipeline."""
    from apps.api.services.dataset_import.framework import ImportConfig, ImportPipeline

    file_path = args.file
    dataset_id = args.dataset_id
    output_dir = args.output_dir or os.path.join("datasets", "rs", "cohort", dataset_id)

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    adapter = _detect_adapter(file_path)
    os.makedirs(output_dir, exist_ok=True)

    # Build a default config for birth chart data
    from apps.api.services.dataset_import.adapters.cohort_excel_adapter import CohortExcelAdapter

    # Use CohortExcelAdapter's mappings as a template
    template = CohortExcelAdapter()

    config = ImportConfig(
        dataset_id=dataset_id,
        source_file=file_path,
        output_dir=output_dir,
        column_mappings=template.get_column_mappings(),
        validation_rules=[
            required_field_not_none("birth_latitude"),
            required_field_not_none("birth_longitude"),
            latitude_in_range(),
            longitude_in_range(),
        ],
        normalization_rules=template.get_normalization_rules(),
        dedup_key_fields=template.get_dedup_key_fields(),
        export_format=args.export_format or "CSV",
        source_metadata=template.get_source_metadata(file_path),
    )

    print(f"Importing: {file_path}")
    print(f"Dataset ID: {dataset_id}")
    print(f"Output: {output_dir}")
    print(f"Adapter: {adapter.get_adapter_name()}")
    print()

    pipeline = ImportPipeline(adapter, config)
    report = pipeline.run()

    print(f"Total records: {report.total_records}")
    print(f"Imported: {report.records_imported}")
    print(f"Validation failures: {report.validation_failures}")
    if report.duplicate_detection:
        print(f"Duplicates removed: {report.duplicate_detection.duplicates_removed}")
    if report.quality_assessment:
        qa = report.quality_assessment
        print(f"Quality score: {qa.get('quality_score', 'N/A')}")
        print(f"Quality tier: {qa.get('quality_tier', 'N/A')}")
    if report.export_results:
        for er in report.export_results:
            print(f"Exported: {er.output_path} ({er.file_size_bytes} bytes)")
    if report.errors:
        print(f"Errors: {report.errors}", file=sys.stderr)
        return 1

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AstroOS Dataset Import CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m apps.api.services.dataset_import.cli validate data.csv
  python -m apps.api.services.dataset_import.cli validate data.xlsx --verbose
  python -m apps.api.services.dataset_import.cli import data.csv ASTRO-RS-COHORT-v2.0.0
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a dataset file")
    validate_parser.add_argument("file", help="Path to the dataset file")
    validate_parser.add_argument("--schema", default=None, help="Path to JSON Schema file")
    validate_parser.add_argument("--rules", choices=["standard", "none", "all"], default="standard",
                                 help="Validation rule set")
    validate_parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import a dataset through the full pipeline")
    import_parser.add_argument("file", help="Path to the source file")
    import_parser.add_argument("dataset_id", help="Output dataset ID (e.g., ASTRO-RS-COHORT-v2.0.0)")
    import_parser.add_argument("--output-dir", help="Output directory (default: datasets/rs/cohort/<dataset_id>)")
    import_parser.add_argument("--export-format", choices=["CSV", "JSON", "JSONL"], default="CSV",
                               help="Export format")

    args = parser.parse_args(argv)

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "import":
        return cmd_import(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
