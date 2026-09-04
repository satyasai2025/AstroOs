"""
AstroOS — Event Timing Foundation: Migrated Techniques

Migrates the (now-removed) Event Timing Foundation's 42-technique catalogue
(formerly services/event_timing_registry.py + event_timing_rules.py) onto the
canonical Technique/Rule architecture (domain/technique.py, domain/rules.py,
RuleEngine, TechniqueEngine). That module was dead scaffolding — nothing ever
called it (no router, no service, no test) — but the catalogue itself records
real, citeable astrological methodology names/descriptions worth keeping.

CLASSIFICATION (42 total). Every original entry had `status == RESEARCH`
(TimingStatus.RESEARCH was the only value ever passed to the old registry's
`_t()` helper) — nothing here is promoted to VALIDATED merely because it
existed in the old registry. All migrated techniques keep
`provenance=ProvenanceStatus.UNTESTED`, `status="research"`.

  MIGRATED — valid, has real evaluable rule(s) (7 techniques, 8 rules):
    saturn_jupiter_transit, sade_sati, mahadasha_timing, antardasha_timing,
    retrograde_saturn, retrograde_jupiter, sun_progression_navamsha.
    Rule-level provenance is SOURCE_DERIVED where the old rule cited a real
    existing mechanism (MarriageTimingEngine, TransitEngine, Vimsottari
    tradition, Gochara, DivisionalEngine) — the technique-level provenance
    stays UNTESTED regardless, since nothing was empirically validated.

  MIGRATED — incomplete/untested, catalogue entry only, zero rules ever
  authored for it (29 techniques): introduction_to_event_timing,
  dasha_transit_time_period, mahadasha_antardasha_event_rules,
  planetary_roles, year_timing, month_timing, month_day_timing,
  snapshot_marriage_timing, career_change, promotion, career_interruption,
  property_purchase, property_sale, gochar_event_trigger, sun_transit,
  moon_transit, childbirth_transit_techniques, financial_gains,
  accidents_sudden_events, foreign_travel, visa_immigration,
  major_opportunities, fortune_bhagyoday, divorce_relationship_break,
  vehicle_purchase, guru_spiritual_growth, dasha_transit_childbirth,
  retrograde_mercury, rahu_ketu_arudha_lagna.
  Migrated as TechniqueDefinition with empty rule_refs — a genuine,
  real-methodology catalogue entry, just not yet operationalized. NOT
  invented here: no rule is authored where the old registry had none.

    NOTE: `introduction_to_event_timing` and `planetary_roles` are
    conceptual/methodological entries (how dasha+transit combine; how to
    assign karaka roles) rather than independently triggerable techniques —
    included for catalogue completeness but will likely never gain rule_refs
    of their own.

  NOT MIGRATED — duplicate/obsolete (1): saturn_jupiter_marriage_transit
  (rule TRN-SJ-M01) is condition-for-condition identical to
  saturn_jupiter_transit's TRN-SJ-001 (same feature, same operator, same
  values, same event_type "marriage") — superseded by it, not a distinct
  technique.

  NOT MIGRATED — invalid/dead scaffolding (5): techniques whose required
  calculation engine does not exist in AstroOS today, so no rule could ever
  be authored for them without fabricating data —
  chandra_kala_nadi_marriage, chandra_kala_nadi_childbirth (Chandra Kala Nadi
  engine), kalatra_sphuta, putra_sphuta (Sphuta engine), integrated_timing
  (depends on both). Migrating these would create phantom techniques that can
  only ever report INSUFFICIENT_DATA with no path to ever resolving it.

RULE MIGRATION NOTES — fact-key remapping from the old ad hoc feature-map
paths (event_timing_features.py, also removed) to canonical FactBuilder
facts:
  - transit.{planet}_house_from_venus -> transit.{planet}.house_from_venus
    (now emitted by FactBuilder itself; the one genuinely unique computation
    the old feature extractor had — see fact_builder.py's _build_transit_facts).
  - transit.is_sade_sati -> transit.saturn.sade_sati (already emitted).
  - dasha.mahadasha_lord -> dasha.current_mahadasha (already emitted).
  - dasha.antardasha_lord -> dasha.antardasha_lord (now emitted: FactBuilder's
    _build_dasha_facts looks up the matched Mahadasha's sub_periods for the
    one bracketing the target date; only present when the DashaTree was
    computed to max_depth >= 2, so a shallow tree still honestly yields
    INSUFFICIENT_DATA rather than a fabricated antardasha).
  - transit.{saturn,jupiter}_retrograde -> transit.{planet}.retrograde (now
    emitted: TransitEngine's per-planet result already carried is_retrograde;
    FactBuilder just wasn't surfacing it as a Fact).
  - varga.available -> varga.sun.D9.rashi (FactBuilder emits per-planet,
    per-varga facts, not a single boolean; existence of the Sun's D9 rashi
    fact is the concrete substitute for "is D9 available").

`is_true`/`is_false`/`exists`/`negate` (the old event_timing_rules.py
operator vocabulary) needed no RuleEngine changes: `==`/`!=` already express
is_true/is_false against real Python bools, and TechniqueEngine's own
missing-fact pre-check (services/technique_engine.py: `_missing_facts`)
already turns a referenced-but-absent fact into INSUFFICIENT_DATA before
RuleEngine ever runs — a cleaner existence check than the old ad hoc
operator gave. `negate` had zero real usage in the old registry (grepped:
no `_rule(...)` call ever set it True) and is otherwise redundant with the
paired inverse operators (`==`/`!=`, `in`/`not_in`) already in RuleEngine.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.domain.technique import (
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
    TimingResolution,
)
from apps.api.services.rule_registry import get_rule, register_rule
from apps.api.services.technique_registry import register_technique

_SPEC = "Event Timing Research Foundation spec"


def _register(rule: RuleDefinition) -> None:
    """Idempotent register: fixtures/tests may import more than once."""
    if get_rule(rule.rule_id) is None:
        register_rule(rule)


# ── Migrated rules (7 techniques, 8 evaluable rules) ──────────────────────────

_register(RuleDefinition(
    rule_id="TRN-SJ-001",
    rule_version="1.0",
    rule_name="Jupiter Activates Natal Venus",
    source_text="Jupiter transits 1/5/7/9 from natal Venus (trine/opposition activation).",
    priority=5,
    category="event_timing",
    conditions=(
        Condition("transit.jupiter.house_from_venus", "in", (1, 5, 7, 9),
                  "Jupiter transits 1/5/7/9 from natal Venus"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.saturn_jupiter_transit.jupiter_activation": "indicated"},
        description="Jupiter activation window for marriage-adjacent significators.",
    ),
    explanation="Jupiter transiting a trine/opposition house from natal Venus is the documented MarriageTimingEngine activation window.",
    tags=("transit", "jupiter", "marriage"),
))

_register(RuleDefinition(
    rule_id="TRN-SJ-002",
    rule_version="1.0",
    rule_name="Saturn Obstructs Natal Venus",
    source_text="Saturn transits 1/3/7/10 from natal Venus (delay/obstruction).",
    priority=5,
    category="event_timing",
    conditions=(
        Condition("transit.saturn.house_from_venus", "in", (1, 3, 7, 10),
                  "Saturn transits 1/3/7/10 from natal Venus"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.saturn_jupiter_transit.saturn_obstruction": "indicated"},
        description="Saturn delay/obstruction window.",
    ),
    explanation="Saturn transiting these houses from natal Venus is the documented MarriageTimingEngine obstruction window.",
    tags=("transit", "saturn", "marriage"),
))

_register(RuleDefinition(
    rule_id="TRN-SADES-001",
    rule_version="1.0",
    rule_name="Sade Sati Active",
    source_text="Saturn transits 12/1/2 house from natal Moon (Sade Sati).",
    priority=5,
    category="event_timing",
    conditions=(
        Condition("transit.saturn.sade_sati", "==", True, "Sade Sati is active"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.sade_sati.active": "indicated"},
        description="Marks the ~7.5-year Saturn window (12-1-2 from Moon).",
    ),
    explanation="Sade Sati, as already computed by TransitEngine.",
    tags=("transit", "saturn", "sade_sati"),
))

_register(RuleDefinition(
    rule_id="DSH-TIM-001",
    rule_version="1.0",
    rule_name="Active Mahadasha Present",
    source_text="An active Mahadasha brackets the event window.",
    priority=3,
    category="event_timing",
    conditions=(
        Condition("dasha.current_mahadasha", "!=", None, "An active Mahadasha is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.mahadasha_timing.bracketed": "indicated"},
        description="Broadest event-era bracket from the level-1 dasha lord.",
    ),
    explanation="Vimsottari Dasha tradition: the Mahadasha (level-1) lord brackets the broadest event era.",
    tags=("dasha", "mahadasha"),
))

_register(RuleDefinition(
    rule_id="DSH-TIM-002",
    rule_version="1.0",
    rule_name="Active Antardasha Present",
    source_text="An active Antardasha narrows the event window.",
    priority=3,
    category="event_timing",
    conditions=(
        # FactBuilder emits dasha.antardasha_lord only when the DashaTree was
        # computed to max_depth >= 2 (sub_periods populated) — a shallow tree
        # correctly leaves this rule reporting INSUFFICIENT_DATA rather than
        # fabricating an antardasha.
        Condition("dasha.antardasha_lord", "!=", None, "An active Antardasha is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.antardasha_timing.narrowed": "indicated"},
        description="Narrows within the Mahadasha using the level-2 lord.",
    ),
    explanation="Vimsottari Dasha tradition: the Antardasha (level-2) lord narrows within the Mahadasha.",
    tags=("dasha", "antardasha"),
))

_register(RuleDefinition(
    rule_id="TRN-RET-001",
    rule_version="1.0",
    rule_name="Saturn Retrograde at Event Moment",
    source_text="Saturn is retrograde at the event moment.",
    priority=2,
    category="event_timing",
    conditions=(
        Condition("transit.saturn.retrograde", "==", True, "Saturn is retrograde at the event moment"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.retrograde_saturn.active": "indicated"},
        description="Delay/obstruction modifier on Saturn's activating transits.",
    ),
    explanation="Gochara: Saturn retrograde at the transit moment modulates its activating/benefic transits.",
    tags=("transit", "saturn", "retrograde"),
))

_register(RuleDefinition(
    rule_id="TRN-RET-002",
    rule_version="1.0",
    rule_name="Jupiter Retrograde at Event Moment",
    source_text="Jupiter is retrograde at the event moment.",
    priority=2,
    category="event_timing",
    conditions=(
        Condition("transit.jupiter.retrograde", "==", True, "Jupiter is retrograde at the event moment"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.retrograde_jupiter.active": "indicated"},
        description="Modulation of Jupiter's activating/benefic transits.",
    ),
    explanation="Gochara: Jupiter retrograde at the transit moment modulates its activating/benefic transits.",
    tags=("transit", "jupiter", "retrograde"),
))

_register(RuleDefinition(
    rule_id="VAR-001",
    rule_version="1.0",
    rule_name="Navamsha (D9) Available",
    source_text="Navamsha (D9) varga computation is available.",
    priority=1,
    category="event_timing",
    conditions=(
        Condition("varga.sun.D9.rashi", "!=", None, "Navamsha (D9) varga is available"),
    ),
    conclusion=Conclusion(
        derived_facts={"event_timing.sun_progression_navamsha.varga_available": "indicated"},
        description="Precondition only — does not itself assess the Sun's progression.",
    ),
    explanation="DivisionalEngine: the D9 varga must be computed before Sun-progression-in-Navamsha can be assessed.",
    tags=("varga", "navamsha", "precondition"),
))


# ── Migrated technique definitions ────────────────────────────────────────────


def _migrated(
    technique_id: str,
    name: str,
    category: str,
    event_types: tuple[str, ...],
    timing_resolution: TimingResolution,
    description: str,
    source_reference: str,
    rule_refs: tuple[TechniqueRuleRef, ...] = (),
) -> TechniqueDefinition:
    return TechniqueDefinition(
        technique_id=technique_id,
        name=name,
        version=1,
        description=description,
        tradition="",
        objective=category,
        source_references=(source_reference,) if source_reference else (),
        dependencies=("dasha", "transit"),
        rule_refs=rule_refs,
        provenance=ProvenanceStatus.UNTESTED,
        status="research",
        event_types=event_types,
        timing_resolution=timing_resolution,
    )


def _ref(rule_id: str, role: RuleRole, source_reference: str) -> TechniqueRuleRef:
    return TechniqueRuleRef(
        rule_id=rule_id,
        rule_version="1.0",
        role=role,
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        source_reference=source_reference,
    )


ALL_EVENTS: tuple[str, ...] = (
    "marriage", "childbirth", "career_change", "promotion", "career_interruption",
    "property_purchase", "property_sale", "financial_gain", "accident",
    "foreign_travel", "visa_immigration", "major_opportunity", "bhagyoday",
    "divorce", "relationship_break", "vehicle_purchase", "guru_meeting",
    "spiritual_growth", "sadesati_event",
)

# ── 7 migrated with real rule_refs ────────────────────────────────────────────

register_technique(_migrated(
    "saturn_jupiter_transit", "Saturn + Jupiter Transit", "transit",
    ("marriage", "career_change", "promotion", "property_purchase", "spiritual_growth"),
    TimingResolution.MONTH,
    "Jupiter activating a significator while Saturn delays/obstructs — the classic marriage-window scanner (see MarriageTimingEngine).",
    "MarriageTimingEngine; Event Timing Research spec (§6.22)",
    rule_refs=(
        _ref("TRN-SJ-001", RuleRole.PRIMARY, "MarriageTimingEngine"),
        _ref("TRN-SJ-002", RuleRole.CONTRADICTING, "MarriageTimingEngine"),
    ),
))
register_technique(_migrated(
    "sade_sati", "Sade Sati", "major_events",
    ("sadesati_event", "career_interruption"), TimingResolution.YEAR,
    "Mark the ~7.5-year Saturn window (12-1-2 from Moon) and its phases.",
    "Gochara; " + _SPEC + " (§6.36)",
    rule_refs=(_ref("TRN-SADES-001", RuleRole.PRIMARY, "TransitEngine"),),
))
register_technique(_migrated(
    "mahadasha_timing", "Mahadasha Timing", "foundation",
    ALL_EVENTS, TimingResolution.YEAR,
    "Use the Mahadasha (level-1) lord to bracket the broadest event era.",
    "Vimsottari tradition; " + _SPEC + " (§6.3)",
    rule_refs=(_ref("DSH-TIM-001", RuleRole.PRIMARY, "Vimsottari Dasha tradition"),),
))
register_technique(_migrated(
    "antardasha_timing", "Antardasha Timing", "foundation",
    ALL_EVENTS, TimingResolution.YEAR,
    "Narrow within the Mahadasha using the Antardasha (level-2) lord.",
    "Vimsottari tradition; " + _SPEC + " (§6.4)",
    rule_refs=(_ref("DSH-TIM-002", RuleRole.SUPPORTING, "Vimsottari Dasha tradition"),),
))
register_technique(_migrated(
    "retrograde_saturn", "Retrograde Saturn", "advanced_transit",
    ALL_EVENTS, TimingResolution.YEAR,
    "Weigh Saturn retrograde state at the transit moment as a delay/obstruction modifier.",
    "",
    rule_refs=(_ref("TRN-RET-001", RuleRole.SUPPORTING, "Gochara"),),
))
register_technique(_migrated(
    "retrograde_jupiter", "Retrograde Jupiter", "advanced_transit",
    ALL_EVENTS, TimingResolution.YEAR,
    "Weigh Jupiter retrograde state as a modulation of its activating/benefic transits.",
    "",
    rule_refs=(_ref("TRN-RET-002", RuleRole.SUPPORTING, "Gochara"),),
))
register_technique(_migrated(
    "sun_progression_navamsha", "Sun Progression in Navamsha", "advanced_transit",
    ("spiritual_growth", "bhagyoday", "career_change"), TimingResolution.YEAR,
    "Progression of the Sun through the natal Navamsha (D9) as a maturation timing layer.",
    "",
    rule_refs=(_ref("VAR-001", RuleRole.PRIMARY, "DivisionalEngine"),),
))

# ── 27 migrated as catalogue-only (no rules ever existed for these) ──────────

register_technique(_migrated(
    "introduction_to_event_timing", "Introduction to Event Timing", "foundation",
    ALL_EVENTS, TimingResolution.EVENT_WINDOW,
    "Conceptual foundation: how dasha + transit + bhava readings combine to time events.",
    _SPEC + " (§6.1)",
))
register_technique(_migrated(
    "dasha_transit_time_period", "Dasha + Transit Time-Period Principle", "foundation",
    ALL_EVENTS, TimingResolution.YEAR,
    "Principle that an active dasha period plus a matching transit activation together delimit an event window.",
    "Parashara; " + _SPEC + " (§6.2)",
))
register_technique(_migrated(
    "mahadasha_antardasha_event_rules", "Mahadasha-Antardasha Event Rules", "foundation",
    ALL_EVENTS, TimingResolution.YEAR,
    "Combine Mahadasha + Antardasha lords against the event's significator houses/lords.",
    "Parashara; " + _SPEC + " (§6.5)",
))
register_technique(_migrated(
    "planetary_roles", "Planetary Roles", "foundation",
    ALL_EVENTS, TimingResolution.EVENT_WINDOW,
    "Assign each graha's karaka role (e.g. Venus/lord of 7th for marriage) to identify which house/lord a technique should weigh.",
    "Karakatwa; " + _SPEC + " (§6.6)",
))
register_technique(_migrated(
    "year_timing", "Year Timing", "granular_timing",
    ALL_EVENTS, TimingResolution.YEAR,
    "Constrain a window to a specific year via finer dasha levels and annual transits.", "",
))
register_technique(_migrated(
    "month_timing", "Month Timing", "granular_timing",
    ALL_EVENTS, TimingResolution.MONTH,
    "Constrain a window to a month via Pratyantar level and monthly gochara.", "",
))
register_technique(_migrated(
    "month_day_timing", "Month + Day Timing", "granular_timing",
    ALL_EVENTS, TimingResolution.DAY,
    "Attempt month (and rarely day) precision requiring strong multi-rule support.", "",
))
register_technique(_migrated(
    "snapshot_marriage_timing", "Snapshot Marriage Timing", "marriage",
    ("marriage",), TimingResolution.MONTH,
    "Score the natal marriage promise (7th house/lord, Venus) then bracket by active dasha.", "",
))
register_technique(_migrated(
    "career_change", "Career Change", "career",
    ("career_change",), TimingResolution.YEAR,
    "Time career change via 10th house/lord + dasha and Saturn/Jupiter/Rahu transits.", "",
))
register_technique(_migrated(
    "promotion", "Promotion", "career",
    ("promotion",), TimingResolution.YEAR,
    "Time promotion via 10th house/lord strength and benefic transits.", "",
))
register_technique(_migrated(
    "career_interruption", "Career Break/Interruption", "career",
    ("career_interruption",), TimingResolution.YEAR,
    "Identify windows of career break/opposition via 6th/8th/12th contacts and Saturn.", "",
))
register_technique(_migrated(
    "property_purchase", "Property Purchase", "property_finance",
    ("property_purchase",), TimingResolution.YEAR,
    "Time property purchase via 4th house/lord and Jupiter/Saturn transits.", "",
))
register_technique(_migrated(
    "property_sale", "Property Sale", "property_finance",
    ("property_sale", "financial_gain"), TimingResolution.YEAR,
    "Time property sale / financial release via 4th + 11th contacts and benefic transits.", "",
))
register_technique(_migrated(
    "gochar_event_trigger", "Gochar Event Trigger", "transit",
    ALL_EVENTS, TimingResolution.MONTH,
    "Use the transiting grahas' house-from-Moon at the target moment as event triggers.",
    "Gochara; " + _SPEC + " (§6.21)",
))
register_technique(_migrated(
    "sun_transit", "Sun Transit", "transit",
    ALL_EVENTS, TimingResolution.MONTH,
    "Use the Sun's annual house-from-Moon to tag seasons of activity per sign.", "",
))
register_technique(_migrated(
    "moon_transit", "Moon Transit", "transit",
    ALL_EVENTS, TimingResolution.DAY,
    "Use the Moon's day-to-day house-from-Moon for very short windows (avg 2.25 days per sign).", "",
))
register_technique(_migrated(
    "childbirth_transit_techniques", "Childbirth Transit Techniques", "transit",
    ("childbirth",), TimingResolution.MONTH,
    "Jupiter/Moon/sign transits activating the 5th-house childbirth promise.", "",
))
register_technique(_migrated(
    "financial_gains", "Financial Gains", "major_events",
    ("financial_gain",), TimingResolution.YEAR,
    "Time financial gain via 2nd + 11th house/lords and benefics.", "",
))
register_technique(_migrated(
    "accidents_sudden_events", "Accidents / Sudden Events", "major_events",
    ("accident",), TimingResolution.YEAR,
    "Identify sudden-event windows via Mars/Saturn/Rahu/Rahu-Ketu contacts with malefic houses.", "",
))
register_technique(_migrated(
    "foreign_travel", "Foreign Travel", "major_events",
    ("foreign_travel",), TimingResolution.YEAR,
    "Time foreign travel via 12th/3rd houses and significator transits.", "",
))
register_technique(_migrated(
    "visa_immigration", "Visa / Immigration", "major_events",
    ("visa_immigration", "foreign_travel"), TimingResolution.YEAR,
    "Time visa/immigration events via 12th house + Moon/Nodal contacts.", "",
))
register_technique(_migrated(
    "major_opportunities", "Major Opportunities", "major_events",
    ("major_opportunity",), TimingResolution.YEAR,
    "Bracket opportunity windows via 10th/11th activation and benefic dasha.", "",
))
register_technique(_migrated(
    "fortune_bhagyoday", "Fortune / Bhagyoday", "major_events",
    ("bhagyoday", "major_opportunity", "spiritual_growth"), TimingResolution.YEAR,
    "Time fortune rise via Arudha Lagna / 9th house and Jupiter activation.",
    "Jaimini; " + _SPEC + " (§6.32)",
))
register_technique(_migrated(
    "divorce_relationship_break", "Divorce / Relationship Break", "major_events",
    ("divorce", "relationship_break"), TimingResolution.YEAR,
    "Time relationship breakdown via 7th house malefic contacts and Saturn/Rahu.", "",
))
register_technique(_migrated(
    "vehicle_purchase", "Vehicle Purchase", "major_events",
    ("vehicle_purchase",), TimingResolution.YEAR,
    "Time vehicle purchase via 4th/9th houses and mobility significators (Mars, Venus).", "",
))
register_technique(_migrated(
    "guru_spiritual_growth", "Guru / Spiritual Growth", "major_events",
    ("guru_meeting", "spiritual_growth"), TimingResolution.YEAR,
    "Time guru-contact / spiritual turn via 9th house, Jupiter, and Ketu.", "",
))
register_technique(_migrated(
    "dasha_transit_childbirth", "Dasha + Transit Childbirth", "childbirth",
    ("childbirth",), TimingResolution.YEAR,
    "Activate the 5th house/lord via active dasha plus supportive transits.",
    "Parashara; " + _SPEC + " (§6.15)",
))
register_technique(_migrated(
    "retrograde_mercury", "Retrograde Mercury", "advanced_transit",
    ALL_EVENTS, TimingResolution.MONTH,
    "Weigh Mercury retrograde at the event moment for communication/transaction timings.", "",
))
register_technique(_migrated(
    "rahu_ketu_arudha_lagna", "Rahu/Ketu over Arudha Lagna", "advanced_transit",
    ("major_opportunity", "bhagyoday", "career_change"), TimingResolution.YEAR,
    "Relations of the Nodes with the Arudha Lagna as opportunity/upheaval triggers.",
    "Jaimini; " + _SPEC + " (§6.41)",
))

# ── NOT migrated ──────────────────────────────────────────────────────────────
#
# Duplicate/obsolete: saturn_jupiter_marriage_transit (rule TRN-SJ-M01) — its
# single condition (transit.jupiter_house_from_venus in (1,5,7,9), marriage)
# is identical to saturn_jupiter_transit's TRN-SJ-001. Superseded, not migrated.
#
# Invalid/dead scaffolding (required engine does not exist in AstroOS):
#   chandra_kala_nadi_marriage, chandra_kala_nadi_childbirth  — Chandra Kala
#     Nadi engine not implemented.
#   kalatra_sphuta, putra_sphuta                              — Sphuta engine
#     not implemented.
#   integrated_timing                                          — depends on
#     both Sphuta and Nadi engines.
