"""
AstroOS — Entity Linking Service (Knowledge Graph Bridge)

Maps chart entities (planets, houses, signs) to Knowledge Graph entities
by name, alias, and relationship proximity. Pure deterministic matching
using the in-memory OntologyRegistry — no external services, no LLM calls.

Usage:
    linker = EntityLinker(knowledge_graph_engine)
    results = linker.link_chart_data({"planets": [{"name": "Sun", "sign": "Aries"}], ...})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine

# ── Sanskrit / alternate aliases for planetary bodies ─────────────────────────

PLANET_ALIASES: dict[str, list[str]] = {
    "sun": ["surya", "rav", "aditya", "bhanu", "divakara", "savitr"],
    "moon": ["chandra", "soma", "indu", "vidhu", "shashank"],
    "mars": ["mangala", "kuja", "bhauma", "angaraka", "rudhira"],
    "mercury": ["budha", "saumya", "raja-putra"],
    "jupiter": ["brihaspati", "guru", "deva-guru", "angiras"],
    "venus": ["shukra", "bhargava", "daitya-guru", "ushanasi"],
    "saturn": ["shani", "shanaishchara", "mandu", "chayyaputra"],
    "rahu": ["rahuvu", "dragon-head", "svarbhanu"],
    "ketu": ["ketuvu", "dragon-tail", "dhvaja"],
}

RASHI_ALIASES: dict[str, list[str]] = {
    "aries": ["mesha", "bharani-rashi"],
    "taurus": ["vrishabha", "vrisha"],
    "gemini": ["mithuna", "mrij"],
    "cancer": ["karka", "karkataka", "kataka"],
    "leo": ["simha", "singha"],
    "virgo": ["kanya", "kanja"],
    "libra": ["tula", "thula"],
    "scorpio": ["vrischika", "vrishchika"],
    "sagittarius": ["dhanush", "dhanu", "dhanurdhara"],
    "capricorn": ["makara", "makar"],
    "aquarius": ["kumbha", "kumbh"],
    "pisces": ["meena", "mina"],
}

# Mapping of chart-side house representations to KG entity IDs.
HOUSE_ALIASES: dict[str, list[str]] = {
    "1": ["first", "1st", "lagna", "ascendant", "tanu-bhava"],
    "2": ["second", "2nd", "dhana", "dhanu-bhava"],
    "3": ["third", "3rd", "sahaja", "vikrama"],
    "4": ["fourth", "4th", "sukha", "moksha", "bandhu"],
    "5": ["fifth", "5th", "putra", "vidya"],
    "6": ["sixth", "6th", "ari", "ripu", "shatru"],
    "7": ["seventh", "7th", "yuvati", "kalatra", "jaya"],
    "8": ["eighth", "8th", "randhra", "ayu", "mrutyu"],
    "9": ["ninth", "9th", "bhagya", "dharma", "guru"],
    "10": ["tenth", "10th", "karma", "madhya", "ajna"],
    "11": ["eleventh", "11th", "labha", "aya"],
    "12": ["twelfth", "12th", "vyaya", "kshaya"],
}


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class LinkedEntity:
    """A single chart entity matched to a Knowledge Graph entity."""
    source_name: str               # The raw name from chart data (e.g. "Sun")
    source_type: str               # "planet", "house", "sign"
    entity_id: str                 # KG entity id (e.g. "GRAHA-SUN")
    entity_label: str              # KG entity label (e.g. "Sun")
    entity_type: str               # KG entity type (e.g. "Graha")
    confidence: float              # 0.0–1.0
    match_method: str              # "exact", "alias", "fuzzy", "proximity"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkResult:
    """Result of linking a full chart dataset to the Knowledge Graph."""
    linked_entities: list[LinkedEntity] = field(default_factory=list)
    proximity_relationships: list[dict[str, Any]] = field(default_factory=list)
    unlinked: list[dict[str, Any]] = field(default_factory=list)
    total_matched: int = 0
    total_unmatched: int = 0


# ── Entity Linker ──────────────────────────────────────────────────────────────


class EntityLinker:
    """
    Matches chart-level entities (planets, houses, signs) to knowledge graph
    entities. Uses three strategies in order:
      1. Direct name / alias lookup
      2. Fuzzy — case-insensitive, partial matching
      3. Proximity — relationships between already-linked entities
    """

    def __init__(self, engine: KnowledgeGraphEngine) -> None:
        self._engine = engine

        # Build name index from the registry itself (all entity names)
        self._name_index: dict[str, str] = {}     # lowercase name → entity_id
        self._alias_index: dict[str, str] = {}    # lowercase alias → entity_id
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Index all registry entities by name and by hardcoded aliases."""
        # Entities from the registry
        for entity in self._engine._registry.all_entities():
            key = entity.name.lower()
            self._name_index[key] = entity.entity_id
            # Also index by the raw entity_id key (e.g. "graha-sun")
            self._name_index[entity.entity_id.lower()] = entity.entity_id

        # Planet aliases
        for canonical_name, aliases in PLANET_ALIASES.items():
            eid = f"GRAHA-{canonical_name.upper()}"
            if self._engine._registry.get_entity(eid):
                for alias in aliases:
                    self._alias_index[alias.lower()] = eid

        # Rashi aliases
        for canonical_name, aliases in RASHI_ALIASES.items():
            eid = f"RASHI-{canonical_name.upper()}"
            if self._engine._registry.get_entity(eid):
                for alias in aliases:
                    self._alias_index[alias.lower()] = eid

        # House aliases
        for number_str, aliases in HOUSE_ALIASES.items():
            eid = f"BHAVA-{number_str}"
            if self._engine._registry.get_entity(eid):
                for alias in aliases:
                    self._alias_index[alias.lower()] = eid

    def _lookup_name(self, raw_name: str) -> tuple[str | None, str, float]:
        """
        Attempt to match a raw entity name to a KG entity_id.
        Returns (entity_id | None, match_method, confidence).
        """
        cleaned = raw_name.strip().lower()

        # 1. Direct name index match (exact)
        if cleaned in self._name_index:
            return self._name_index[cleaned], "exact", 1.0

        # 2. Alias index match
        if cleaned in self._alias_index:
            return self._alias_index[cleaned], "alias", 0.95

        # 3. Try stripping common prefixes
        for prefix in ("planet ", "house ", "sign ", "rashi ", "graha "):
            stripped = cleaned.removeprefix(prefix)
            if stripped in self._name_index:
                return self._name_index[stripped], "fuzzy", 0.9
            if stripped in self._alias_index:
                return self._alias_index[stripped], "fuzzy", 0.9

        # 4. Check if it looks like a house number
        if cleaned.isdigit() or cleaned.lstrip("#").isdigit():
            num = cleaned.lstrip("#")
            eid = f"BHAVA-{num}"
            if self._engine._registry.get_entity(eid):
                return eid, "fuzzy", 0.9

        return None, "none", 0.0

    def link_chart_planet(
        self, planet: dict[str, Any]
    ) -> list[LinkedEntity]:
        """
        Link a single chart planet entry to KG entities.
        The planet dict can contain: name, sign, house, nakshatra, etc.
        """
        results: list[LinkedEntity] = []
        planet_name = planet.get("name", "")

        # Link the planet itself
        if planet_name:
            eid, method, conf = self._lookup_name(planet_name)
            if eid:
                entity = self._engine._registry.get_entity(eid)
                results.append(LinkedEntity(
                    source_name=planet_name,
                    source_type="planet",
                    entity_id=eid,
                    entity_label=entity.name if entity else planet_name,
                    entity_type=entity.entity_type if entity else "Graha",
                    confidence=conf,
                    match_method=method,
                    metadata={"planet_name": planet_name},
                ))

        # Link the sign the planet is in
        sign_name = planet.get("sign", "")
        if sign_name:
            eid, method, conf = self._lookup_name(sign_name)
            if eid:
                entity = self._engine._registry.get_entity(eid)
                results.append(LinkedEntity(
                    source_name=sign_name,
                    source_type="sign",
                    entity_id=eid,
                    entity_label=entity.name if entity else sign_name,
                    entity_type=entity.entity_type if entity else "Rashi",
                    confidence=conf,
                    match_method=method,
                    metadata={"planet_name": planet_name, "context": "planet_in_sign"},
                ))

        # Link the house the planet is in
        house_val = planet.get("house")
        if house_val is not None:
            house_str = str(house_val)
            eid, method, conf = self._lookup_name(house_str)
            if eid:
                entity = self._engine._registry.get_entity(eid)
                results.append(LinkedEntity(
                    source_name=f"House {house_str}",
                    source_type="house",
                    entity_id=eid,
                    entity_label=entity.name if entity else f"House {house_str}",
                    entity_type=entity.entity_type if entity else "Bhava",
                    confidence=conf,
                    match_method=method,
                    metadata={"planet_name": planet_name, "house_number": house_str, "context": "planet_in_house"},
                ))

        return results

    def link_chart_data(self, chart_data: dict[str, Any]) -> LinkResult:
        """
        Link all entities in a chart dataset to the Knowledge Graph.

        Expected chart_data format:
        {
            "planets": [{"name": "...", "sign": "...", "house": 1}, ...],
            "houses": {1: {"sign": "..."}, ...},
            "ascendant": {"sign": "..."},
            "signs": [...]
        }
        """
        result = LinkResult()
        all_linked: list[LinkedEntity] = []

        # -- Link planets --
        for planet in chart_data.get("planets", []):
            linked = self.link_chart_planet(planet)
            all_linked.extend(linked)
            if not linked:
                result.unlinked.append({"type": "planet", "raw": planet})

        # -- Link houses --
        houses = chart_data.get("houses", {})
        if isinstance(houses, dict):
            for house_num, house_info in houses.items():
                sign = None
                if isinstance(house_info, dict):
                    sign = house_info.get("sign", "")
                elif isinstance(house_info, str):
                    sign = house_info

                if sign:
                    eid, method, conf = self._lookup_name(sign)
                    if eid:
                        entity = self._engine._registry.get_entity(eid)
                        all_linked.append(LinkedEntity(
                            source_name=str(sign),
                            source_type="house",
                            entity_id=eid,
                            entity_label=entity.name if entity else str(sign),
                            entity_type=entity.entity_type if entity else "Rashi",
                            confidence=conf,
                            match_method=method,
                            metadata={"house_number": str(house_num), "context": "house_sign"},
                        ))

        # -- Link ascendant --
        asc = chart_data.get("ascendant", {})
        if isinstance(asc, dict):
            asc_sign = asc.get("sign", "")
        elif isinstance(asc, str):
            asc_sign = asc
        else:
            asc_sign = ""
        if asc_sign:
            eid, method, conf = self._lookup_name(asc_sign)
            if eid:
                entity = self._engine._registry.get_entity(eid)
                all_linked.append(LinkedEntity(
                    source_name=asc_sign,
                    source_type="sign",
                    entity_id=eid,
                    entity_label=entity.name if entity else asc_sign,
                    entity_type=entity.entity_type if entity else "Rashi",
                    confidence=conf,
                    match_method=method,
                    metadata={"context": "ascendant"},
                ))

        # -- Link explicit sign references --
        for sign_ref in chart_data.get("signs", []):
            if isinstance(sign_ref, str):
                eid, method, conf = self._lookup_name(sign_ref)
                if eid:
                    entity = self._engine._registry.get_entity(eid)
                    all_linked.append(LinkedEntity(
                        source_name=sign_ref,
                        source_type="sign",
                        entity_id=eid,
                        entity_label=entity.name if entity else sign_ref,
                        entity_type=entity.entity_type if entity else "Rashi",
                        confidence=conf,
                        match_method=method,
                        metadata={"context": "explicit_sign"},
                    ))

        # De-duplicate by entity_id
        seen: set[str] = set()
        for le in all_linked:
            if le.entity_id not in seen:
                result.linked_entities.append(le)
                seen.add(le.entity_id)

        # -- Build proximity relationships --
        linked_ids = {le.entity_id for le in result.linked_entities}
        for le in result.linked_entities:
            rels = self._engine._registry.relationships_for(le.entity_id)
            for rel in rels:
                counterpart = rel.object_id if rel.subject_id == le.entity_id else rel.subject_id
                if counterpart in linked_ids:
                    result.proximity_relationships.append({
                        "source_id": rel.subject_id,
                        "relationship_type": rel.relationship_type,
                        "target_id": rel.object_id,
                        "metadata": dict(rel.metadata),
                        "via": le.entity_id,
                    })

        result.total_matched = len(result.linked_entities)
        result.total_unmatched = len(result.unlinked)
        return result

    def suggest_related_entities(
        self, entity_id: str, max_depth: int = 1
    ) -> list[dict[str, Any]]:
        """
        Return entities related to the given entity_id via registry
        relationships, limited to the given graph depth.
        """
        visited: set[str] = {entity_id}
        suggestions: list[dict[str, Any]] = []
        current_ring: list[str] = [entity_id]

        for _depth in range(max_depth):
            next_ring: list[str] = []
            for eid in current_ring:
                for rel in self._engine._registry.relationships_for(eid):
                    counterpart = rel.object_id if rel.subject_id == eid else rel.subject_id
                    if counterpart not in visited:
                        visited.add(counterpart)
                        entity = self._engine._registry.get_entity(counterpart)
                        if entity:
                            suggestions.append({
                                "entity_id": counterpart,
                                "entity_label": entity.name,
                                "entity_type": entity.entity_type,
                                "relationship": rel.relationship_type,
                                "via": eid,
                                "distance": _depth + 1,
                            })
                            next_ring.append(counterpart)
            current_ring = next_ring
            if not current_ring:
                break

        return suggestions
