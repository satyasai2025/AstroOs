"""
AstroOS — Priority 9: Custom Technique & AstroDSL Rule Registry Service

Provides lifecycle management, validation, persistence, import/export, and
registry lookups for user-authored AstroDSL custom techniques and Yogas.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from apps.api.domain.astro_dsl import CustomRuleDefinition, parse_astro_dsl
from apps.api.services.astro_dsl_evaluator import AstroDSLEvaluator, CustomRuleEvaluationResult


class CustomTechniqueRegistry:
    """In-memory and JSON-backed registry for AstroDSL custom techniques."""

    _instance: Optional[CustomTechniqueRegistry] = None

    def __init__(self):
        self._rules: Dict[str, CustomRuleDefinition] = {}

    @classmethod
    def get_instance(cls) -> CustomTechniqueRegistry:
        if cls._instance is None:
            cls._instance = CustomTechniqueRegistry()
            cls._instance._seed_default_rules()
        return cls._instance

    def _seed_default_rules(self):
        """Seed sample standard custom rules."""
        gajakesari = CustomRuleDefinition(
            rule_id="custom-gajakesari-01",
            name="Custom Gajakesari Yoga (AstroDSL)",
            description="Jupiter in Kendra from Moon/Lagna and non-combust",
            dsl_source='PLANET("Jupiter").house IN KENDRA_HOUSES AND PLANET("Jupiter").is_combust == FALSE',
            category="custom_yoga",
            tags=["jupiter", "moon", "kendra", "wealth"],
            author="AstroOS Standard",
            version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        rujaka = CustomRuleDefinition(
            rule_id="custom-ruchaka-01",
            name="Custom Ruchaka Yoga (Mars Kendra/Exalted)",
            description="Mars in Kendra house in Aries, Scorpio, or Capricorn",
            dsl_source='PLANET("Mars").house IN KENDRA_HOUSES AND PLANET("Mars").rashi IN ["Aries", "Scorpio", "Capricorn"]',
            category="custom_yoga",
            tags=["mars", "kendra", "panch_mahapurusha"],
            author="AstroOS Standard",
            version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._rules[gajakesari.rule_id] = gajakesari
        self._rules[rujaka.rule_id] = rujaka

    def list_rules(self, category: Optional[str] = None) -> List[CustomRuleDefinition]:
        rules = list(self._rules.values())
        if category:
            return [r for r in rules if r.category == category]
        return rules

    def get_rule(self, rule_id: str) -> Optional[CustomRuleDefinition]:
        return self._rules.get(rule_id)

    def register_rule(self, dsl_source: str, name: str, description: str, category: str = "custom_yoga", tags: Optional[List[str]] = None) -> CustomRuleDefinition:
        # Validate syntax first
        parse_astro_dsl(dsl_source)

        rule_id = f"custom-rule-{uuid.uuid4().hex[:8]}"
        rule = CustomRuleDefinition(
            rule_id=rule_id,
            name=name,
            description=description,
            dsl_source=dsl_source,
            category=category,
            tags=tags or [],
            author="User",
            version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._rules[rule_id] = rule
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def export_bundle(self, rule_ids: Optional[List[str]] = None) -> str:
        """Export specified or all custom rules as a JSON bundle string."""
        rules_to_export = []
        target_ids = rule_ids or list(self._rules.keys())
        for rid in target_ids:
            if rid in self._rules:
                r = self._rules[rid]
                rules_to_export.append({
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "description": r.description,
                    "dsl_source": r.dsl_source,
                    "category": r.category,
                    "tags": r.tags,
                    "author": r.author,
                    "version": r.version,
                    "created_at": r.created_at,
                })
        bundle = {
            "format": "AstroOS_AstroDSL_Bundle",
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "rules": rules_to_export,
        }
        return json.dumps(bundle, indent=2)

    def import_bundle(self, bundle_json: str) -> List[CustomRuleDefinition]:
        """Import custom rules from a JSON bundle string."""
        data = json.loads(bundle_json)
        imported: List[CustomRuleDefinition] = []
        rules_list = data.get("rules", [])
        for r_dict in rules_list:
            dsl_source = r_dict["dsl_source"]
            parse_astro_dsl(dsl_source)  # validate syntax

            rule_id = r_dict.get("rule_id") or f"custom-rule-{uuid.uuid4().hex[:8]}"
            rule = CustomRuleDefinition(
                rule_id=rule_id,
                name=r_dict.get("name", "Imported Rule"),
                description=r_dict.get("description", ""),
                dsl_source=dsl_source,
                category=r_dict.get("category", "custom_yoga"),
                tags=r_dict.get("tags", []),
                author=r_dict.get("author", "imported"),
                version=r_dict.get("version", "1.0.0"),
                created_at=r_dict.get("created_at") or datetime.now(timezone.utc).isoformat(),
            )
            self._rules[rule_id] = rule
            imported.append(rule)
        return imported
