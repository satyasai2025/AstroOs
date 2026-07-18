"""
AstroOS — Cohort Excel Adapter

Adapter for importing birth chart cohort data from Excel files.
Extends the generic Excel adapter with cohort-specific
column mappings, metadata, and normalization rules.

This adapter maps a 15-column flat Excel file to the
AstroOS RS-COHORT record schema.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

from apps.api.services.dataset_import.adapters.excel_adapter import ExcelAdapter
from apps.api.services.dataset_import.adapter_base import ColumnMapping, RawRecord
from apps.api.services.dataset_import.normalizer import (
    NormalizationAction,
    assemble_datetime,
    normalize_coordinates,
    trim_strings,
)


class CohortExcelAdapter(ExcelAdapter):
    """Adapter for importing birth chart cohort data from Excel files."""

    DATASET_ID = "ASTRO-RS-COHORT-v0.1.0"
    DATASET_NAME = "RS-COHORT Birth Chart Cohort"
    SHEET_NAME = "Cohort Data"

    def __init__(self):
        super().__init__(sheet_name=self.SHEET_NAME)

    def get_adapter_name(self) -> str:
        return "CohortExcel"

    def get_column_mappings(self) -> List[ColumnMapping]:
        """Return the column mappings from source columns to AstroOS fields."""
        return [
            ColumnMapping(
                source_column="fname",
                target_field="subject_first_name",
                required=True,
                transformer="string_trim",
            ),
            ColumnMapping(
                source_column="lname",
                target_field="subject_last_name",
                required=True,
                transformer="string_trim",
            ),
            ColumnMapping(
                source_column="gender",
                target_field="subject_gender",
                required=True,
                transformer="string_trim",
            ),
            ColumnMapping(
                source_column="place",
                target_field="birth_place",
                transformer="string_trim",
            ),
            ColumnMapping(
                source_column="country",
                target_field="birth_country",
                transformer="string_trim",
            ),
            ColumnMapping(
                source_column="lat",
                target_field="birth_latitude",
                required=True,
            ),
            ColumnMapping(
                source_column="lng",
                target_field="birth_longitude",
                required=True,
            ),
            ColumnMapping(
                source_column="day",
                target_field="birth_day",
                required=True,
            ),
            ColumnMapping(
                source_column="month",
                target_field="birth_month",
                required=True,
            ),
            ColumnMapping(
                source_column="year",
                target_field="birth_year",
                required=True,
            ),
            ColumnMapping(
                source_column="hour",
                target_field="birth_hour",
                default_value=0,
            ),
            ColumnMapping(
                source_column="min",
                target_field="birth_minute",
                default_value=0,
            ),
            ColumnMapping(
                source_column="calType",
                target_field="calendar_type",
            ),
            ColumnMapping(
                source_column="jdUt",
                target_field="julian_day_ut",
            ),
            ColumnMapping(
                source_column="rr",
                target_field="birth_time_precision",
            ),
        ]

    def get_source_metadata(self, file_path: str) -> Dict[str, Any]:
        base_meta = super().get_source_metadata(file_path)
        base_meta.update({
            "name": "RS-COHORT Birth Chart Cohort",
            "description": "Birth chart records with 15 fields per record, imported from a curated dataset.",
            "category": "Research",
            "category_code": "RS",
            "type": "Cohort",
            "type_code": "COHORT",
            "version": "0.1.0",
            "provenance_tier": "Derived",
            "source_description": "Curated birth chart dataset (imported via dataset import framework)",
            "source_uris": [],
            "collection_method": "api_extract",
            "curator": "AstroOS Research Data Office",
            "license_id": "CC-BY-4.0",
            "license_name": "Creative Commons Attribution 4.0",
            "privacy_tier": "Public",
            "confidence_tier": "Estimated",
            "contains_pii": False,
            "known_limitations": [
                "Calendar type field may not be uniformly applied",
                "Some birth times have low precision (hour only)",
                "Gender field values may need normalization",
            ],
            "known_biases": [
                "Western-centric birth locations",
                "Potential survivorship bias (only public figures)",
            ],
        })
        return base_meta

    def get_normalization_rules(self) -> list:
        """Return normalization rules for cohort data."""
        return [
            assemble_datetime(
                date_fields=("birth_day", "birth_month", "birth_year"),
                time_fields=("birth_hour", "birth_minute"),
                target_field="birth_datetime_utc",
            ),
            normalize_coordinates(precision=6),
            trim_strings(["subject_first_name", "subject_last_name", "subject_gender", "birth_place", "birth_country"]),
        ]

    def get_dedup_key_fields(self) -> List[str]:
        """Fields used for deduplication."""
        return ["subject_first_name", "subject_last_name", "birth_latitude", "birth_longitude", "birth_year", "birth_month", "birth_day"]
