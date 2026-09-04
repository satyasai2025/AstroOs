"""
AstroOS — Technique Resolver
============================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Steps 1 to 8)
Resolves which astrological systems, techniques, vargas, karakas, and house frameworks
are applicable for any given domain or predictive query.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.phalita_core.domain_significators import (
    DOMAIN_SIGNIFICATOR_REGISTRY,
    DomainSignificatorConfig,
    get_domain_config,
)


@dataclass(frozen=True)
class ResolvedTechniquePlan:
    domain: str
    sanskrit_bhava_name: str
    primary_bhava: int
    supporting_bhavas: Tuple[int, ...]
    dusthana_bhavas: Tuple[int, ...]
    designated_vargas: Tuple[int, ...]             # e.g., (1, 9, 10)
    primary_varga: int                             # e.g., 10 for career, 9 for marriage
    naisargika_karakas: Tuple[str, ...]            # Natural karakas e.g., ("Sun", "Saturn")
    relevant_chara_karaka_roles: Tuple[str, ...]   # e.g., ("AK", "AmK") for career, ("DK", "AK") for marriage
    transit_evaluation_houses: Tuple[int, ...]     # Houses where transit triggers are scanned
    sav_threshold: int                             # Default: 28 bindus
    bav_threshold: int                             # Default: 4 bindus
    shastric_rule_category: str                    # e.g., "RAJAYOGA_STATUS", "DHARMA_MARRIAGE"
    technique_execution_order: Tuple[str, ...]     # 5-step sequence


class TechniqueResolver:
    """
    Directs the Shastric Rule Engine by generating domain-tailored technique execution plans.
    """

    DOMAIN_CHARA_MAPPINGS: Dict[str, Tuple[str, ...]] = {
        "health": ("AK", "GK"),
        "wealth": ("AmK", "DK", "AK"),
        "siblings": ("BK", "PK"),
        "property": ("MK", "BK"),
        "children": ("PK", "Jupiter"),
        "legal": ("GK", "Mars"),
        "marriage": ("DK", "AK"),
        "accident": ("GK", "AK"),
        "father": ("BK", "AK"),
        "career": ("AK", "AmK"),
        "gains": ("AmK", "PK"),
        "foreign": ("AK", "GK"),
        "general": ("AK", "AmK"),
    }

    RULE_CATEGORIES: Dict[str, str] = {
        "health": "AYUR_HEALTH_LONGEVITY",
        "wealth": "DHANA_PROSPERITY",
        "siblings": "BHRATRI_COURAGE",
        "property": "BANDHU_PROPERTY_VEHICLE",
        "children": "PUTRA_PROGENY_INTELLECT",
        "legal": "SHATRU_LITIGATION_DEBT",
        "marriage": "KALATRA_MARRIAGE_UNION",
        "accident": "RANDHRA_CRISIS_TRAUMA",
        "father": "DHARMA_FATHER_GURU",
        "career": "KARMA_RAJAYOGA_STATUS",
        "gains": "LABHA_AMBITION_INFLOW",
        "foreign": "VYAYA_FOREIGN_LIBERATION",
        "general": "GENERAL_NATIVITY_SYNTHESIS",
    }

    @classmethod
    def resolve_domain_plan(cls, domain: str) -> ResolvedTechniquePlan:
        """
        Builds complete resolution plan for a domain.
        """
        dom_clean = domain.lower()
        cfg: DomainSignificatorConfig = get_domain_config(dom_clean)

        chara_roles = cls.DOMAIN_CHARA_MAPPINGS.get(dom_clean, ("AK", "AmK"))
        rule_cat = cls.RULE_CATEGORIES.get(dom_clean, "GENERAL_NATIVITY_SYNTHESIS")

        # Execution sequence following Jha's framework
        seq = (
            "1_NATAL_BHAVACHALITA_PROMISE",
            "2_DIVISIONAL_VARGA_CONFIRMATION",
            "3_CHARA_KARAKA_KARAKAMSHA_ALIGNMENT",
            "4_TEMPORAL_DASHA_ACTIVATION",
            "5_GOCHARA_TRANSIT_TRIGGER",
        )

        all_vargas = (1, cfg.designated_varga) + cfg.secondary_vargas
        # Remove duplicates while preserving order
        seen = set()
        dedup_vargas = []
        for v in all_vargas:
            if v not in seen:
                seen.add(v)
                dedup_vargas.append(v)

        return ResolvedTechniquePlan(
            domain=dom_clean,
            sanskrit_bhava_name=cfg.display_name,
            primary_bhava=cfg.primary_house,
            supporting_bhavas=cfg.supporting_houses,
            dusthana_bhavas=cfg.opposing_dusthana_houses,
            designated_vargas=tuple(dedup_vargas),
            primary_varga=cfg.designated_varga,
            naisargika_karakas=cfg.naisargika_karakas,
            relevant_chara_karaka_roles=chara_roles,
            transit_evaluation_houses=(cfg.primary_house,) + cfg.supporting_houses,
            sav_threshold=28,
            bav_threshold=4,
            shastric_rule_category=rule_cat,
            technique_execution_order=seq,
        )

