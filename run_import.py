"""
Run the AstroDatabank import pipeline and produce the Import Validation Report.

Usage: python run_import.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from apps.api.services.dataset_import.framework import ImportConfig, ImportPipeline
from apps.api.services.dataset_import.adapters.astrodatabank_adapter import AstroDatabankAdapter
from apps.api.services.dataset_import.validator import (
    Severity, ValidationLevel, ValidationRule,
    latitude_in_range, longitude_in_range, required_field_not_none,
)


def main():
    adapter = AstroDatabankAdapter()
    source_file = r"C:\Users\rkmau\Downloads\AstroDatabank.xlsx"

    if not os.path.exists(source_file):
        print(f"ERROR: {source_file} not found")
        sys.exit(1)

    output_dir = os.path.join(os.path.dirname(__file__), "datasets", "rs", "cohort", "ASTRO-RS-COHORT-v0.1.0")

    config = ImportConfig(
        dataset_id="ASTRO-RS-COHORT-v0.1.0",
        source_file=source_file,
        output_dir=output_dir,
        column_mappings=adapter.get_column_mappings(),
        validation_rules=[
            required_field_not_none("birth_latitude"),
            required_field_not_none("birth_longitude"),
            latitude_in_range(),
            longitude_in_range(),
        ],
        normalization_rules=adapter.get_normalization_rules(),
        dedup_key_fields=adapter.get_dedup_key_fields(),
        export_format="CSV",
        source_metadata=adapter.get_source_metadata(source_file),
    )

    pipeline = ImportPipeline(adapter, config)
    report = pipeline.run()

    # Print report summary
    print("=" * 60)
    print("  IMPORT VALIDATION REPORT")
    print("=" * 60)
    print(f"  Dataset ID:           {report.dataset_id}")
    print(f"  Total records read:   {report.total_records:,}")
    print(f"  Records imported:     {report.records_imported:,}")
    print(f"  Records accepted:     {report.records_accepted:,}")
    print(f"  Validation failures:  {report.validation_failures:,}")
    print(f"  Normalization actions:{len(report.normalization_actions):,}")
    print(f"  Missing mandatory:    {report.missing_mandatory_fields}")
    print()
    if report.duplicate_detection:
        dd = report.duplicate_detection
        print(f"  DUPLICATE DETECTION")
        print(f"    Total:       {dd.total_records:,}")
        print(f"    Unique:      {dd.unique_records:,}")
        print(f"    Removed:     {dd.duplicates_removed:,}")
        print(f"    Duplicate%:  {dd.duplicate_pct:.1f}%")
    print()
    if report.quality_assessment:
        qa = report.quality_assessment
        print(f"  QUALITY ASSESSMENT")
        print(f"    Score:       {qa['quality_score']:.2f}")
        print(f"    Tier:        {qa['quality_tier']}")
        print(f"    Completeness:{qa['completeness_pct']:.1f}%")
        for dim, score in qa.get("dimension_scores", {}).items():
            print(f"    {dim:15s} {score:.2f}")
    print()
    if report.export_results:
        er = report.export_results[0]
        print(f"  EXPORT")
        print(f"    Format:      {er.format}")
        print(f"    Path:        {er.output_path}")
        print(f"    Records:     {er.record_count:,}")
        print(f"    Size:        {er.file_size_bytes:,} bytes")
        print(f"    Checksum:    {er.checksum_sha256[:16]}...")
        print(f"    Metadata:    {er.metadata_path}")
    print()
    if report.errors:
        print(f"  ERRORS:")
        for e in report.errors:
            print(f"    {e}")
    print("=" * 60)

    # Write report to JSON
    report_path = os.path.join(output_dir, f"{report.dataset_id}_import_validation_report.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    print(f"\nFull report written to: {report_path}")


if __name__ == "__main__":
    main()
