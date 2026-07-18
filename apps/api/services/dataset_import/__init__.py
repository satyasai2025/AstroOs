"""
AstroOS — Dataset Import Framework

Generic, extensible pipeline for importing external datasets into the
AstroOS canonical dataset format.

Pipeline: Source Adapter → Schema Mapping → Validation → Normalization →
          Deduplication → Quality Assessment → Export

The CohortExcelAdapter is the first supported adapter for birth chart imports.
"""

from apps.api.services.dataset_import.framework import ImportPipeline

__all__ = ["ImportPipeline"]
