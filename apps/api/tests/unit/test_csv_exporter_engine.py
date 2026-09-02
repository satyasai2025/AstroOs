"""
Unit tests for CSV Exporter Engine implementing Section 10 schemas.
"""

from datetime import datetime, timezone
import pytest
from apps.api.services.csv_exporter_engine import (
    CSVExporterEngine,
    LONG_DEBUG_HEADER,
    WIDE_ML_HEADER,
)


def test_wide_ml_csv_generation():
    engine = CSVExporterEngine()
    records = [
        {
            "birth_datetime_utc": datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc),
            "latitude": 28.6139,
            "longitude": 77.2090,
            "gold_return_10min": 0.0012,
            "gold_return_1hr": 0.0045,
        },
        {
            "birth_datetime_utc": datetime(1950, 9, 17, 11, 0, 0, tzinfo=timezone.utc),
            "latitude": 23.0225,
            "longitude": 72.5714,
            "gold_return_10min": -0.0020,
            "gold_return_1hr": -0.0080,
        },
    ]

    csv_str = engine.export_wide_ml_csv(records)
    lines = csv_str.strip().split("\n")
    
    # 1. Check header matches exact specification
    header = lines[0].strip().split(",")
    assert header == WIDE_ML_HEADER
    
    # 2. Check canonical wealth houses present and others omitted per Jha Sec 10.2
    assert "H2_Total" in header
    assert "H8_Total" in header
    assert "H11_Total" in header
    assert "H12_Total" in header
    assert "H1_Total" not in header
    assert "H5_Total" not in header
    
    # 3. Check target columns present
    assert "Gold_Return_10min" in header
    assert "Gold_Return_1hr" in header
    
    # 4. Check 2 rows exported
    assert len(lines) == 3


def test_long_debug_csv_generation():
    engine = CSVExporterEngine()
    records = [
        {
            "birth_datetime_utc": datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc),
            "latitude": 28.6139,
            "longitude": 77.2090,
        }
    ]

    csv_str = engine.export_long_debug_csv(records)
    lines = csv_str.strip().split("\n")
    
    # 1. Check header
    header = lines[0].strip().split(",")
    assert header == LONG_DEBUG_HEADER
    
    # 2. Contains multiple rule lines
    assert len(lines) > 10
