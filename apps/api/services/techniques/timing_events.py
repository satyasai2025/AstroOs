"""
AstroOS — Timing & Event Intelligence Techniques (Sastric & Empirical Rigor)

Implements classical predictive timing principles with strict methodology scoping:
  1. Double Transit Marriage Window (K.N. Rao Modern Empirical Research Methodology)
  2. Sade Sati 3-Phase Saturn Cycle (Phaladeepika Ch. 26, with empirical mitigation modifiers)
  3. Ashtama Shani (Strictly 8th House from Natal Moon / Chandra Lagna)
  4. Career & Karma Elevation Timing (3-Tier Model: Natal Promise -> Dasha Activation -> Gochara Trigger)
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, ConditionGroup, Conclusion, RuleDefinition
from apps.api.domain.technique import (
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
)
from apps.api.services.rule_registry import get_rule, register_rule
from apps.api.services.technique_registry import get_technique, register_technique

_SOURCE_KN_RAO = "K.N. Rao: 'Planets and Children' / 'Timing Events Through Vimshottari and Transits' (Modern Empirical Research Methodology)"
_SOURCE_PHALA = "Phaladeepika, Ch. 26 (Gochara Phala) & Brihat Parashara Hora Shastra, Ch. 45"
_SOURCE_BPHS_KARMA = "Brihat Parashara Hora Shastra, Ch. 19 (Judgement of 10th House / Rajya Bhava)"


def init_timing_techniques() -> None:
    # ── 1. Double Transit Marriage Timing ─────────────────────────────────────
    if get_technique("double_transit_marriage", 1) is None:
        # Rule 1: Dasha Activation (Prerequisite Framework)
        if get_rule("TRN-DOUBLE-MARR-DASH") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TRN-DOUBLE-MARR-DASH",
                    rule_version="1.0",
                    rule_name="Dasha Activation for Matrimony",
                    source_text="Vimshottari Dasha must establish the timing window via Venus (natural karaka), 7th lord, or Jupiter.",
                    priority=9,
                    category="event_timing",
                    conditions=(
                        ConditionGroup(
                            operator="OR",
                            conditions=(
                                Condition("dasha.current_mahadasha", "in", ("venus", "jupiter"), "Current Mahadasha is Venus or Jupiter"),
                                Condition("dasha.antardasha_lord", "in", ("venus", "jupiter"), "Current Antardasha is Venus or Jupiter"),
                            ),
                        ),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"timing.dasha_matrimony_active": "true"},
                        description="Dasha period permits matrimonial crystallization.",
                    ),
                    explanation="Under the Dwi-Gochara framework, transits cannot act in a vacuum without Dasha sanction.",
                    tags=("timing", "dasha", "marriage"),
                )
            )

        # Rule 2: Double Transit Gochara Alignment (Empirical Trigger)
        if get_rule("TRN-DOUBLE-MARR-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TRN-DOUBLE-MARR-001",
                    rule_version="1.0",
                    rule_name="Saturn-Jupiter Double Transit Convergence",
                    source_text="Saturn (1/3/7/10 aspect/transit) and Jupiter (1/5/7/9 aspect/transit) simultaneously influence natal Venus in transit.",
                    priority=8,
                    category="event_timing",
                    conditions=(
                        Condition("transit.jupiter.house_from_venus", "in", (1, 5, 7, 9), "Transit Jupiter aspects/transits natal Venus (1, 5, 7, 9)"),
                        Condition("transit.saturn.house_from_venus", "in", (1, 3, 7, 10), "Transit Saturn aspects/transits natal Venus (1, 3, 7, 10)"),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"timing.double_transit_marriage_trigger": "active"},
                        description="Saturn and Jupiter jointly sanction the matrimonial timing window.",
                    ),
                    explanation="According to K.N. Rao's empirical research methodology, Saturn confirms karmic maturation while Jupiter bestows benefic blessing.",
                    tags=("timing", "marriage", "double_transit"),
                )
            )

        register_technique(
            TechniqueDefinition(
                technique_id="double_transit_marriage",
                name="Double Transit Marriage Window (K.N. Rao Methodology)",
                version=1,
                description="Evaluates the empirical Double Transit (Dwi-Gochara) timing window formulated by K.N. Rao, where Saturn and Jupiter jointly aspect natal Venus during an active Dasha period.",
                tradition="K.N. Rao Modern Research / Dwi-Gochara",
                objective="marriage_timing",
                source_references=(_SOURCE_KN_RAO,),
                required_inputs=(
                    "dasha.current_mahadasha",
                    "transit.jupiter.house_from_venus",
                    "transit.saturn.house_from_venus",
                ),
                dependencies=("D1", "transit", "dasha"),
                rule_refs=(
                    TechniqueRuleRef("TRN-DOUBLE-MARR-DASH", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                    TechniqueRuleRef("TRN-DOUBLE-MARR-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                ),
                provenance=ProvenanceStatus.SOURCE_DERIVED,
                status="research",
            )
        )

    # ── 2. Sade Sati Saturn Cycle ─────────────────────────────────────────────
    if get_technique("sade_sati_cycle", 1) is None:
        if get_rule("TRN-SADE-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TRN-SADE-001",
                    rule_version="1.0",
                    rule_name="Saturn Sade Sati Active Phase (12th, 1st, 2nd from Moon)",
                    source_text="Saturn transits the 12th, 1st (Janma), or 2nd house from natal Moon (Chandra Lagna).",
                    priority=8,
                    category="event_timing",
                    conditions=(
                        ConditionGroup(
                            operator="OR",
                            conditions=(
                                Condition("transit.saturn.sade_sati", "==", True, "Saturn is in Sade Sati"),
                                Condition("transit.saturn.house", "in", (12, 1, 2), "Saturn transiting 12th, 1st, or 2nd from natal Moon"),
                            ),
                        ),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"transit.sade_sati_influence": "active"},
                        description="Saturn's 7.5-year cycle of karmic restructuring from Moon is active.",
                    ),
                    explanation="Phaladeepika Ch. 26 notes that Saturn transiting the Janma Rashi and its adjacent signs produces mental tension, discipline, and endurance challenges.",
                    tags=("timing", "saturn", "sade_sati"),
                )
            )

        # Optional empirical factor (NOT a generic classical cancellation guarantee)
        if get_rule("TRN-SADE-MIT-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TRN-SADE-MIT-001",
                    rule_version="1.0",
                    rule_name="Saturn Dignified in Transit Sign (Empirical Modifying Factor)",
                    source_text="Saturn transiting through Libra (exaltation), Capricorn, or Aquarius (own signs) provides constructive fortitude (Optional empirical modifier).",
                    priority=4,
                    category="event_timing",
                    conditions=(
                        Condition("transit.saturn.rashi", "in", ("libra", "capricorn", "aquarius"), "Saturn in Libra, Capricorn, or Aquarius"),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"transit.sade_sati_empirical_modifier": "constructive"},
                        description="Dignified sign placement aids constructive endurance during Sade Sati.",
                    ),
                    explanation="Note: Classical Gochara texts do not grant automatic cancellation purely by sign placement; this is an empirical supporting modifier.",
                    tags=("timing", "saturn", "empirical_modifier"),
                )
            )

        register_technique(
            TechniqueDefinition(
                technique_id="sade_sati_cycle",
                name="Sade Sati Karmic Cycle",
                version=1,
                description="Evaluates the active 7.5-year cycle of Saturn transiting the 12th, 1st, and 2nd houses from natal Moon (Chandra Lagna), with optional empirical dignity modifiers.",
                tradition="Parashari",
                objective="event_timing",
                source_references=(_SOURCE_PHALA,),
                required_inputs=("transit.saturn.house", "transit.saturn.rashi"),
                dependencies=("D1", "transit"),
                rule_refs=(
                    TechniqueRuleRef("TRN-SADE-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                    TechniqueRuleRef("TRN-SADE-MIT-001", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
                ),
                provenance=ProvenanceStatus.SOURCE_DERIVED,
                status="research",
            )
        )

    # ── 3. Ashtama Shani (Strictly 8th House from Natal Moon) ─────────────────
    if get_technique("ashtama_shani_transit", 1) is None:
        if get_rule("TRN-ASHT-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TRN-ASHT-001",
                    rule_version="1.0",
                    rule_name="Ashtama Shani Transit (8th from Natal Moon)",
                    source_text="Saturn transits the 8th house strictly from the natal Moon (Chandra Lagna), NOT from Ascendant.",
                    priority=8,
                    category="event_timing",
                    conditions=(
                        ConditionGroup(
                            operator="OR",
                            conditions=(
                                Condition("transit.saturn.ashtama_shani", "==", True, "Ashtama Shani is active from Moon"),
                                Condition("transit.saturn.house", "==", 8, "Saturn is in 8th house from natal Moon"),
                            ),
                        ),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"transit.ashtama_shani_active": "true"},
                        description="Saturn occupies the 8th house strictly counted from the natal Moon sign.",
                    ),
                    explanation="Phaladeepika Ch. 26 Sloka 20: Saturn in the 8th house from the Moon brings sudden disruptions, health scrutiny, and deep karmic restructuring.",
                    tags=("timing", "saturn", "ashtama_shani"),
                )
            )

        register_technique(
            TechniqueDefinition(
                technique_id="ashtama_shani_transit",
                name="Ashtama Shani Transit (8th from Moon)",
                version=1,
                description="Identifies the classical 2.5-year transit of Saturn through the 8th house strictly counted from natal Moon (Chandra Lagna).",
                tradition="Parashari",
                objective="event_timing",
                source_references=(_SOURCE_PHALA,),
                required_inputs=("transit.saturn.house",),
                dependencies=("D1", "transit"),
                rule_refs=(
                    TechniqueRuleRef("TRN-ASHT-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                ),
                provenance=ProvenanceStatus.SOURCE_DERIVED,
                status="research",
            )
        )

    # ── 4. Career Elevation: 3-Tier Model (Promise -> Dasha -> Gochara) ───────
    if get_technique("career_elevation_timing", 1) is None:
        # Tier 1: Natal Promise (10th house / 10th lord)
        if get_rule("TIM-CAR-PROMISE-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TIM-CAR-PROMISE-001",
                    rule_version="1.0",
                    rule_name="Natal Career Promise (10th Lord in Kendra/Trikona)",
                    source_text="Natal chart establishes strong professional capability through 10th lord placed in an angle (1, 4, 7, 10) or trine (5, 9) or gains house (11).",
                    priority=9,
                    category="career_timing",
                    conditions=(
                        Condition("house.10.lord_house", "in", (1, 4, 5, 7, 9, 10, 11), "10th lord in Kendra, Trikona, or 11th house"),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"natal.career_promise_strong": "true"},
                        description="Natal promise for career growth and professional status is established.",
                    ),
                    explanation="Classical Jyotish foundational dictum: without a strong natal promise in the Rashi chart, transits and dasha cannot deliver high elevation.",
                    tags=("career", "natal_promise"),
                )
            )

        # Tier 2: Dasha Period Activation
        if get_rule("TIM-CAR-DASH-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TIM-CAR-DASH-001",
                    rule_version="1.0",
                    rule_name="Executive Dasha Lord Activation",
                    source_text="Current Mahadasha is ruled by an executive/growth planet (Sun, Mars, Jupiter, Mercury, or 10th lord).",
                    priority=8,
                    category="career_timing",
                    conditions=(
                        Condition("dasha.current_mahadasha", "in", ("sun", "mars", "jupiter", "mercury", "saturn"), "Dasha lord is an executive or career planet"),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"timing.career_dasha_active": "true"},
                        description="Active Dasha period is primed for professional action.",
                    ),
                    explanation="Vimshottari Dasha opens the temporal gate for career manifestation.",
                    tags=("career", "dasha"),
                )
            )

        # Tier 3: Gochara Transit Trigger
        if get_rule("TIM-CAR-GOCHARA-001") is None:
            register_rule(
                RuleDefinition(
                    rule_id="TIM-CAR-GOCHARA-001",
                    rule_version="1.0",
                    rule_name="Jupiter Gochara in Auspicious Houses from Moon",
                    source_text="Jupiter transits in 1st, 5th, 9th, 10th, or 11th house from natal Moon.",
                    priority=7,
                    category="career_timing",
                    conditions=(
                        Condition("transit.jupiter.house", "in", (1, 5, 9, 10, 11), "Jupiter in 1, 5, 9, 10, 11 from Moon"),
                    ),
                    conclusion=Conclusion(
                        derived_facts={"timing.jupiter_career_trigger": "active"},
                        description="Benefic transit of Jupiter triggers career expansion.",
                    ),
                    explanation="Jupiterian gochara provides the external catalyst when natal promise and dasha are aligned.",
                    tags=("career", "jupiter", "transit"),
                )
            )

        register_technique(
            TechniqueDefinition(
                technique_id="career_elevation_timing",
                name="Career Elevation & Karma Timing (3-Tier Model)",
                version=1,
                description="Candidate timing window only (not a guaranteed career prediction). Evaluates professional rise using the complete classical hierarchy: Natal Promise (10th lord placement) -> Dasha Activation -> Jupiter Transit Trigger.",
                tradition="Parashari",
                objective="career",
                source_references=(_SOURCE_BPHS_KARMA, _SOURCE_PHALA),
                required_inputs=(
                    "house.10.lord_house",
                    "dasha.current_mahadasha",
                    "transit.jupiter.house",
                ),
                dependencies=("D1", "transit", "dasha"),
                rule_refs=(
                    TechniqueRuleRef("TIM-CAR-PROMISE-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                    TechniqueRuleRef("TIM-CAR-DASH-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                    TechniqueRuleRef("TIM-CAR-GOCHARA-001", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
                ),
                provenance=ProvenanceStatus.SOURCE_DERIVED,
                status="research",
            )
        )


init_timing_techniques()