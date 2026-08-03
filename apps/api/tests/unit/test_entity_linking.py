"""
Unit tests for Entity Linking Service (Knowledge Graph Bridge).

Rewritten 2026-07-31 for the current EntityLinker API. The linker now builds a
name/alias index from the engine's registry (`_registry.all_entities()`) and
`link_chart_data()` returns a `LinkResult` of `LinkedEntity` objects — the older
dict-list interface (`get_nodes_by_label`, `confidence_score`, `match_type`)
no longer exists.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

from apps.api.services.entity_linking import EntityLinker


def _entity(eid: str, name: str, etype: str) -> SimpleNamespace:
    return SimpleNamespace(entity_id=eid, name=name, entity_type=etype)


class TestEntityLinker:
    def setup_method(self):
        self.entities = [
            _entity("SUN", "Sun", "Graha"),
            _entity("MOON", "Moon", "Graha"),
            _entity("MARS", "Mars", "Graha"),
            _entity("ARIES", "Aries", "Rashi"),
            _entity("TAURUS", "Taurus", "Rashi"),
        ]
        # EntityLinker reads the engine's private `_registry` (an OntologyRegistry)
        # to build its name/alias index — a spec'd Mock would raise on `_registry`.
        self.mock_kg_engine = Mock()
        self.mock_kg_engine._registry = Mock()
        self.mock_kg_engine._registry.all_entities = Mock(return_value=self.entities)
        self.mock_kg_engine._registry.relationships_for = Mock(return_value=[])
        # Truthy for any id (so the alias index is populated); the real entity
        # for known ids (so labels/types resolve).
        self.mock_kg_engine._registry.get_entity = Mock(
            side_effect=lambda eid: next(
                (e for e in self.entities if e.entity_id == eid), MagicMock()
            )
        )
        self.linker = EntityLinker(self.mock_kg_engine)

    def test_exact_name_match(self):
        """Exact name lookup returns the registry entity with full confidence."""
        result = self.linker.link_chart_data({"planets": [{"name": "Sun"}]})
        assert len(result.linked_entities) == 1
        le = result.linked_entities[0]
        assert le.entity_id == "SUN"
        assert le.entity_label == "Sun"
        assert le.confidence == 1.0
        assert le.match_method == "exact"

    def test_alias_match(self):
        """Sanskrit alias resolves to the canonical graha id at alias confidence."""
        result = self.linker.link_chart_data({"planets": [{"name": "Surya"}]})
        assert len(result.linked_entities) == 1
        le = result.linked_entities[0]
        assert le.entity_id == "GRAHA-SUN"
        assert le.confidence == 0.95
        assert le.match_method == "alias"

        # Sign alias alongside a planet: both resolve.
        result = self.linker.link_chart_data({"planets": [{"name": "Mars", "sign": "Mesha"}]})
        linked = {le.source_name: le for le in result.linked_entities}
        assert "Mars" in linked and "Mesha" in linked
        assert linked["Mesha"].entity_id == "RASHI-ARIES"
        assert linked["Mesha"].confidence == 0.95

    def test_no_matches(self):
        """Unknown names land in `unlinked`, not fabricated matches."""
        result = self.linker.link_chart_data({"planets": [{"name": "NonExistentPlanet"}]})
        assert result.linked_entities == []
        assert len(result.unlinked) == 1

    def test_multiple_entities(self):
        """Planets + explicit signs all resolve, de-duplicated by entity_id."""
        chart = {
            "planets": [{"name": "Sun"}, {"name": "Moon"}, {"name": "Mars"}],
            "signs": ["Aries", "Taurus"],
        }
        result = self.linker.link_chart_data(chart)
        ids = {le.entity_id for le in result.linked_entities}
        assert {"SUN", "MOON", "MARS", "ARIES", "TAURUS"} <= ids
        for le in result.linked_entities:
            assert le.confidence >= 0.8

    def test_confidence_scoring(self):
        """Exact = 1.0, alias = 0.95."""
        result = self.linker.link_chart_data({"planets": [{"name": "Sun"}]})
        assert result.linked_entities[0].confidence == 1.0

        result = self.linker.link_chart_data({"planets": [{"name": "Surya"}]})
        assert result.linked_entities[0].confidence == 0.95
        assert result.linked_entities[0].match_method == "alias"

    def test_empty_chart_data(self):
        """An empty chart yields an empty (not erroring) result."""
        result = self.linker.link_chart_data({})
        assert result.linked_entities == []
        assert result.total_matched == 0

    def test_missing_entity_types_default_to_graha(self):
        result = self.linker.link_chart_data({"planets": [{"name": "Sun"}]})
        assert result.linked_entities[0].entity_type == "Graha"

    def test_proximity_relationships(self):
        """A registry relationship between two linked entities is surfaced."""
        rel = SimpleNamespace(
            subject_id="SUN", object_id="MOON", relationship_type="aspects", metadata={}
        )
        self.mock_kg_engine._registry.relationships_for = Mock(return_value=[rel])
        result = self.linker.link_chart_data({"planets": [{"name": "Sun"}, {"name": "Moon"}]})
        assert any(p["relationship_type"] == "aspects" for p in result.proximity_relationships)
