"""
Unit tests for TPhalitCore Engine implementing Vinay Jha's exact UDT schema.
"""

from datetime import datetime, timezone
import pytest
from apps.api.domain.tphalit_core import ChartLevelEnum, TPhalitFeatureVector
from apps.api.services.tphalit_core_engine import TPhalitCoreEngine


def test_tphalit_core_extraction():
    engine = TPhalitCoreEngine()
    # Test chart: Raj (1971-06-29 23:27:40 UTC)
    birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    lat, lon = 28.6139, 77.2090

    fv = engine.extract_features(
        birth_datetime_utc=birth_dt,
        latitude=lat,
        longitude=lon,
        topic_id=1,  # Jataka
        chart_level=ChartLevelEnum.ANNUAL,
        varga_id=1,  # D1
    )

    assert isinstance(fv, TPhalitFeatureVector)
    
    # 1. Check TPhalitContext metadata (Section 6.1)
    assert fv.Metadata.TopicID == 1
    assert fv.Metadata.ChartLevel == 1
    assert fv.Metadata.VargaID == 1
    assert fv.Metadata.VargaWeight == 3.5  # D1 weight in Shodashavarga
    assert fv.Metadata.TimeJD > 2440000.0

    # 2. Check BlockTotals (Section 6.6)
    assert "PlanetBlock" in fv.BlockTotals
    assert "BhavaBlock" in fv.BlockTotals
    assert "AspectBlock" in fv.BlockTotals
    assert "YogaBlock" in fv.BlockTotals
    assert "VargaBlock" in fv.BlockTotals
    assert "TemporalBlock" in fv.BlockTotals

    # 3. Check AtomicFeatures
    assert "D1_Sun_FinalSigned" in fv.AtomicFeatures
    assert "D1_Jupiter_FinalSigned" in fv.AtomicFeatures
    assert "D1_H1_FinalScore" in fv.AtomicFeatures
    assert "D1_H12_FinalScore" in fv.AtomicFeatures

    # Values must be within signed range [-1.0, +1.0]
    for k, v in fv.AtomicFeatures.items():
        if "FinalSigned" in k or "FinalScore" in k:
            assert -1.0 <= v <= 1.0, f"Feature {k} with value {v} out of [-1.0, +1.0] range"
