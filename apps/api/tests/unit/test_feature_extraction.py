"""
AstroOS — Unit tests for FeatureExtractionService
"""

import json
from datetime import date
from unittest.mock import MagicMock

from apps.api.domain.facts import Fact
from apps.api.models.research_case import EventSnapshotModel
from apps.api.services.feature_extraction import FeatureExtractionService, summarize


# ── _deserialize_facts: persistence boundary ─────────────────────────────────

def test_deserialize_facts_returns_fact_objects():
    """_deserialize_facts is the only place that touches facts_json string."""
    facts_payload = [
        {"key": "maraka.lord.venus", "value": True, "source": "badhaka_maraka_engine"},
        {"key": "transit.jupiter.gati", "value": "vakra", "source": "transit_engine"},
    ]
    snapshot = EventSnapshotModel(facts_json=json.dumps(facts_payload))
    facts = FeatureExtractionService._deserialize_facts(snapshot)

    assert facts is not None
    assert len(facts) == 2
    assert all(isinstance(f, Fact) for f in facts)
    assert facts[0].key == "maraka.lord.venus"
    assert facts[0].value is True
    assert facts[0].source == "badhaka_maraka_engine"
    assert facts[1].key == "transit.jupiter.gati"
    assert facts[1].value == "vakra"


def test_deserialize_facts_returns_none_when_null():
    snapshot = EventSnapshotModel(facts_json=None)
    assert FeatureExtractionService._deserialize_facts(snapshot) is None


def test_deserialize_facts_returns_none_on_corrupt_json():
    snapshot = EventSnapshotModel(facts_json="NOT_VALID_JSON{{{")
    assert FeatureExtractionService._deserialize_facts(snapshot) is None


# ── _from_facts: pure domain, no DB objects ───────────────────────────────────

def test_from_facts_pure_domain_no_db():
    """_from_facts receives list[Fact] only — no snapshot, no JSON string."""
    facts = [
        Fact(key="functional.saturn.yogakaraka", value=True, source="functional_lordship_engine"),
        Fact(key="friendship.panchadha.sun.saturn", value="sama", source="friendship"),
        Fact(key="planet.sun.house", value=10, source="graha_engine"),
    ]
    features = FeatureExtractionService._from_facts(
        facts,
        research_case_id="RC-PURE",
        event_type="promotion",
        event_date=date(2024, 6, 1),
    )

    assert len(features) == 3
    feat_map = {f.feature_name: f for f in features}
    assert feat_map["functional.saturn.yogakaraka"].feature_category == "functional"
    assert feat_map["functional.saturn.yogakaraka"].feature_value is True
    assert feat_map["friendship.panchadha.sun.saturn"].feature_category == "friendship"
    assert feat_map["friendship.panchadha.sun.saturn"].feature_value == "sama"
    assert feat_map["planet.sun.house"].feature_category == "planet"
    assert feat_map["planet.sun.house"].feature_value == 10


# ── _from_snapshot: orchestration ────────────────────────────────────────────

def test_from_snapshot_routes_through_facts_not_raw_json():
    """Verify _from_snapshot uses _deserialize_facts → _from_facts path;
    the feature_name values must be dotted fact keys, never json string blobs."""
    service = FeatureExtractionService(session=MagicMock())

    facts_payload = [
        {"key": "planet.sun.house", "value": 10, "source": "graha_engine"},
        {"key": "maraka.lord.venus", "value": True, "source": "badhaka_maraka_engine"},
        {"key": "badhaka.house", "value": 11, "source": "badhaka_maraka_engine"},
        {"key": "functional.saturn.yogakaraka", "value": True, "source": "functional_lordship_engine"},
        {"key": "transit.jupiter.gati", "value": "vakra", "source": "transit_engine"},
        {"key": "friendship.panchadha.sun.saturn", "value": "sama", "source": "friendship"},
    ]
    snapshot = EventSnapshotModel(facts_json=json.dumps(facts_payload))

    features = service._from_snapshot(
        research_case_id="RC-001",
        event_type="promotion",
        event_date=date(2024, 6, 1),
        snapshot=snapshot,
    )

    assert len(features) == 6
    # All feature_name values must be canonical dotted fact keys (no raw JSON)
    for feat in features:
        assert "." in feat.feature_name, f"expected dotted key, got: {feat.feature_name!r}"

    feat_map = {f.feature_name: f for f in features}
    assert feat_map["maraka.lord.venus"].feature_category == "maraka"
    assert feat_map["maraka.lord.venus"].feature_value is True
    assert feat_map["functional.saturn.yogakaraka"].feature_category == "functional"
    assert feat_map["transit.jupiter.gati"].feature_value == "vakra"
    assert feat_map["friendship.panchadha.sun.saturn"].feature_value == "sama"

    summary = summarize(features)
    assert summary["maraka"] == 1
    assert summary["functional"] == 1
    assert summary["transit"] == 1
    assert summary["friendship"] == 1


def test_from_snapshot_legacy_fallback_when_facts_json_is_null():
    service = FeatureExtractionService(session=MagicMock())

    snapshot = EventSnapshotModel(
        facts_json=None,
        mahadasha="Jupiter",
        antardasha="Saturn",
        pratyantar=None,
        active_yogas=json.dumps(["Gajakesari"]),
        transit_features=json.dumps({"Jupiter_cancer": True}),
        shadbala_values=json.dumps({"Jupiter": 7.5}),
        varga_activations=json.dumps({"D9_Jupiter": "strong"}),
        nakshatra_activations=json.dumps(["Jupiter_punarvasu"]),
        house_lord_statuses=json.dumps({"10": "exalted"}),
    )

    features = service._from_snapshot(
        research_case_id="RC-LEGACY",
        event_type="marriage",
        event_date=date(2020, 1, 1),
        snapshot=snapshot,
    )

    assert len(features) > 0
    categories = {f.feature_category for f in features}
    assert "dasha" in categories
    assert "yoga" in categories
    assert "transit" in categories
    assert "shadbala" in categories
    assert "varga" in categories
    assert "nakshatra" in categories
    assert "house" in categories
