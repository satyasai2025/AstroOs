"""
AstroOS — Unit tests for Composite Feature Detector
"""

from datetime import date

import pytest

from apps.api.domain.facts import Fact
from apps.api.services.composite_feature_detector import (
    CompositeFeatureDetector,
    DEFAULT_COMPOSITE_TEMPLATES,
)


def test_composite_feature_detector_dasha_maraka():
    facts = [
        Fact("dasha.current_lord", "venus", "dasha_engine"),
        Fact("maraka.lord.venus", True, "badhaka_maraka_engine"),
        Fact("maraka.lord.jupiter", False, "badhaka_maraka_engine"),
    ]
    detector = CompositeFeatureDetector()
    results = detector.detect_for_facts(
        facts,
        research_case_id="RC-001",
        event_type="litigation",
        event_date=date(2024, 5, 10),
    )

    assert len(results) == 1
    comp = results[0]
    assert comp.composite_name == "dasha_maraka_activation"
    assert comp.research_case_id == "RC-001"
    assert comp.event_type == "litigation"
    assert len(comp.components) == 2
    assert comp.components[0].key == "dasha.current_lord"
    assert comp.components[0].value == "venus"
    assert comp.components[1].key == "maraka.lord.venus"
    assert comp.components[1].value is True


def test_composite_feature_detector_yogakaraka():
    facts = [
        Fact("dasha.current_lord", "saturn", "dasha_engine"),
        Fact("functional.saturn.yogakaraka", True, "functional_lordship_engine"),
    ]
    detector = CompositeFeatureDetector()
    results = detector.detect_for_facts(
        facts,
        research_case_id="RC-002",
        event_type="promotion",
        event_date=date(2024, 6, 1),
    )

    assert len(results) == 1
    assert results[0].composite_name == "dasha_yogakaraka_activation"

    # Convert to extracted features
    extracted = detector.to_extracted_features(results)
    assert len(extracted) == 1
    assert extracted[0].feature_name == "composite_dasha_yogakaraka_activation"
    assert extracted[0].feature_category == "composite"
    assert extracted[0].feature_value is True


def test_composite_feature_detector_varga_confluence():
    facts = [
        Fact("dasha.current_lord", "mars", "dasha_engine"),
        Fact("varga.mars.D9.house", 10, "divisional_engine"),
    ]
    detector = CompositeFeatureDetector()
    results = detector.detect_for_facts(
        facts,
        research_case_id="RC-003",
        event_type="job_change",
        event_date=date(2024, 7, 15),
    )

    assert len(results) == 1
    assert results[0].composite_name == "dasha_varga_kendra_confluence"
