"""
AstroOS — Dataset Import Framework

Generic, extensible pipeline for importing external datasets into the
AstroOS canonical dataset format.

Pipeline: Source Adapter → Schema Mapping → Validation → Normalization →
          Deduplication → Quality Assessment → Export

AstroDatabank.xlsx is the first supported adapter.
"""

from apps.api.services.dataset_import.framework import ImportPipeline

__all__ = ["ImportPipeline"]
