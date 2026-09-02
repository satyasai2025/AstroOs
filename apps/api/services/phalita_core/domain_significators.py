"""
AstroOS — Complete 12-Bhava Life Domain Registry & Significator Matrix
======================================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md
Compiled from Brihat Parashara Hora Shastra (BPHS) & Jha's 77 Canonical Docs.

Defines the complete, unalterable 12-Bhava mapping for predictive intelligence:
- Primary Bhava (House)
- Supporting / Derivative Bhavas (Bhaavas from all Bhaavas)
- Designated Divisional Chart (Varga)
- Naisargika Karakas (Natural Significators)
- Gating priority weights across MoE experts
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class DomainSignificatorConfig:
    """Configuration for a specific life domain in the predictive framework."""
    domain_key: str
    display_name: str
    primary_house: int
    supporting_houses: Tuple[int, ...]
    opposing_dusthana_houses: Tuple[int, ...]
    designated_varga: int            # e.g., 9 for D9, 10 for D10, 7 for D7, 4 for D4
    secondary_vargas: Tuple[int, ...] # Supporting divisional charts
    naisargika_karakas: Tuple[str, ...] # Natural planets ruling this domain
    is_favorable_event: bool          # True for career/marriage/wealth/children; False for accident/disease
    router_logits: Dict[str, float]   # Base gating weights across MoE experts


# Complete 12-Bhava Canonical Domain Registry
DOMAIN_SIGNIFICATOR_REGISTRY: Dict[str, DomainSignificatorConfig] = {
    # 1. Tanu Bhava (Self, Vitality, Health)
    "health": DomainSignificatorConfig(
        domain_key="health",
        display_name="Vitality & Physical Health",
        primary_house=1,
        supporting_houses=(5, 9, 8, 10),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=1,
        secondary_vargas=(3, 30),
        naisargika_karakas=("sun", "mars"),
        is_favorable_event=True,
        router_logits={"structural": 1.4, "divisional": 1.0, "temporal": 2.2, "upagraha": 2.2},
    ),

    # 2. Dhana Bhava (Accumulated Wealth, Liquid Assets, Family)
    "wealth": DomainSignificatorConfig(
        domain_key="wealth",
        display_name="Accumulated Wealth & Treasury",
        primary_house=2,
        supporting_houses=(11, 5, 9, 1, 4),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=2,
        secondary_vargas=(9, 10),
        naisargika_karakas=("jupiter", "venus", "mercury"),
        is_favorable_event=True,
        router_logits={"structural": 1.5, "divisional": 1.6, "temporal": 2.1, "upagraha": 1.0},
    ),

    # 3. Sahaja Bhava (Siblings, Courage, Short Journeys, Initiatives)
    "siblings": DomainSignificatorConfig(
        domain_key="siblings",
        display_name="Siblings, Valour & Initiatives",
        primary_house=3,
        supporting_houses=(11, 6, 1, 9),
        opposing_dusthana_houses=(8, 12),
        designated_varga=3,
        secondary_vargas=(9,),
        naisargika_karakas=("mars",),
        is_favorable_event=True,
        router_logits={"structural": 1.3, "divisional": 1.4, "temporal": 2.0, "upagraha": 1.1},
    ),

    # 4. Sukha Bhava (Real Estate, Property, Vehicles, Mother, Mental Peace)
    "property": DomainSignificatorConfig(
        domain_key="property",
        display_name="Property, Vehicles & Real Estate",
        primary_house=4,
        supporting_houses=(1, 2, 10, 11, 9),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=4,
        secondary_vargas=(9, 10),
        naisargika_karakas=("mars", "venus", "moon"),
        is_favorable_event=True,
        router_logits={"structural": 1.4, "divisional": 1.8, "temporal": 2.1, "upagraha": 1.2},
    ),

    # 5. Putra Bhava (Children, Progeny, Intellect, Speculative Inflow)
    "children": DomainSignificatorConfig(
        domain_key="children",
        display_name="Children, Progeny & Intellect",
        primary_house=5,
        supporting_houses=(1, 2, 9, 11),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=7,
        secondary_vargas=(9,),
        naisargika_karakas=("jupiter",),
        is_favorable_event=True,
        router_logits={"structural": 1.3, "divisional": 2.0, "temporal": 2.1, "upagraha": 1.4},
    ),

    # 6. Ari/Ripu Bhava (Litigation, Debts, Overcoming Adversaries, Competition)
    "legal": DomainSignificatorConfig(
        domain_key="legal",
        display_name="Legal Disputes, Debts & Overcoming Enemies",
        primary_house=6,
        supporting_houses=(8, 12, 3, 10, 11),
        opposing_dusthana_houses=(8, 12),
        designated_varga=30,
        secondary_vargas=(9, 10),
        naisargika_karakas=("mars", "saturn"),
        is_favorable_event=False,  # Adverse trigger unless upachaya lordship is exalted
        router_logits={"structural": 1.2, "divisional": 1.2, "temporal": 2.2, "upagraha": 2.4},
    ),

    # 7. Kalatra Bhava (Marriage, Spouse, Alliance, Public Trade)
    "marriage": DomainSignificatorConfig(
        domain_key="marriage",
        display_name="Marriage, Spouse & Sacred Union",
        primary_house=7,
        supporting_houses=(2, 11, 5, 8, 9),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=9,
        secondary_vargas=(1, 7),
        naisargika_karakas=("venus", "jupiter"),
        is_favorable_event=True,
        router_logits={"structural": 1.2, "divisional": 1.5, "temporal": 2.3, "upagraha": 1.8},
    ),

    # 8. Randhra Bhava (Surgeries, Accidents, Sudden Transformation, Longevity Crises)
    "accident": DomainSignificatorConfig(
        domain_key="accident",
        display_name="Surgeries, Sudden Crises & Longevity",
        primary_house=8,
        supporting_houses=(6, 12, 2, 7),
        opposing_dusthana_houses=(1, 5, 9),
        designated_varga=30,
        secondary_vargas=(3,),
        naisargika_karakas=("saturn", "rahu", "ketu", "mars"),
        is_favorable_event=False,
        router_logits={"structural": 1.1, "divisional": 1.0, "temporal": 2.3, "upagraha": 2.5},
    ),

    # 9. Dharma Bhava (Father, Higher Wisdom, Guru, Fortune, Long Journeys)
    "father": DomainSignificatorConfig(
        domain_key="father",
        display_name="Father, Dharma & Higher Fortune",
        primary_house=9,
        supporting_houses=(1, 5, 10, 11, 2),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=12,
        secondary_vargas=(9,),
        naisargika_karakas=("sun", "jupiter"),
        is_favorable_event=True,
        router_logits={"structural": 1.4, "divisional": 1.7, "temporal": 2.1, "upagraha": 1.1},
    ),

    # 10. Karma Bhava (Career, Profession, Status, Public Power & Authority)
    "career": DomainSignificatorConfig(
        domain_key="career",
        display_name="Career, Status & Authority",
        primary_house=10,
        supporting_houses=(1, 2, 5, 9, 11),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=10,
        secondary_vargas=(9, 2),
        naisargika_karakas=("sun", "mercury", "jupiter", "saturn"),
        is_favorable_event=True,
        router_logits={"structural": 1.4, "divisional": 2.1, "temporal": 2.0, "upagraha": 1.1},
    ),

    # 11. Labha Bhava (Financial Gains, Social Eminence, Fulfillment of Aspirations)
    "gains": DomainSignificatorConfig(
        domain_key="gains",
        display_name="Financial Gains & High Fulfillment",
        primary_house=11,
        supporting_houses=(2, 5, 9, 10, 1),
        opposing_dusthana_houses=(6, 8, 12),
        designated_varga=10,
        secondary_vargas=(2, 9),
        naisargika_karakas=("jupiter", "mercury"),
        is_favorable_event=True,
        router_logits={"structural": 1.4, "divisional": 1.8, "temporal": 2.2, "upagraha": 1.0},
    ),

    # 12. Vyaya Bhava (Foreign Travel, Relocation, Solitude & Moksha)
    "foreign": DomainSignificatorConfig(
        domain_key="foreign",
        display_name="Foreign Travel, Relocation & Liberation",
        primary_house=12,
        supporting_houses=(9, 3, 8, 4),
        opposing_dusthana_houses=(2, 4),
        designated_varga=12,
        secondary_vargas=(9, 4),
        naisargika_karakas=("saturn", "rahu", "ketu", "jupiter"),
        is_favorable_event=True,
        router_logits={"structural": 1.3, "divisional": 1.6, "temporal": 2.2, "upagraha": 1.6},
    ),
}


def get_domain_config(domain: str) -> DomainSignificatorConfig:
    """Retrieve canonical domain configuration with case-insensitive fallback."""
    key = domain.strip().lower()
    if key in DOMAIN_SIGNIFICATOR_REGISTRY:
        return DOMAIN_SIGNIFICATOR_REGISTRY[key]
    
    # Fuzzy alias resolution
    aliases = {
        "job": "career",
        "profession": "career",
        "business": "career",
        "wedding": "marriage",
        "relationship": "marriage",
        "illness": "health",
        "disease": "health",
        "injury": "accident",
        "surgery": "accident",
        "crisis": "accident",
        "house": "property",
        "real_estate": "property",
        "vehicle": "property",
        "car": "property",
        "kid": "children",
        "child": "children",
        "progeny": "children",
        "court": "legal",
        "dispute": "legal",
        "enemies": "legal",
        "money": "wealth",
        "finance": "wealth",
        "profits": "gains",
        "income": "gains",
        "abroad": "foreign",
        "relocation": "foreign",
        "spirituality": "foreign",
        "dharma": "father",
    }
    resolved = aliases.get(key, "career")
    return DOMAIN_SIGNIFICATOR_REGISTRY[resolved]


def get_all_domains() -> List[str]:
    """Returns all 12 registered domain keys in canonical order."""
    return list(DOMAIN_SIGNIFICATOR_REGISTRY.keys())
