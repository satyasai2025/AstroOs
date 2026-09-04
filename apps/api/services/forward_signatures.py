"""
Forward Event-Prediction Engine — Phase 1 Signature Definitions
================================================================

This module defines the three Phase 1 event signatures for the ForwardScanner:
    - marriage_venus_jupiter
    - job_change_sun_saturn
    - financial_gain_jupiter_venus

Each signature is a frozen dataclass of type EventSignatureDef, reusing the
Condition shape from domain/rules.py and providing:
    - a classical source (BPHS, Phaladeepika, etc.)
    - guarded forecast wording (soft, uncertain language per RFC §8)
    - required and optional conditions (fact_keys to match in the orchestrator's
      evidence trace)

The signatures are pure data; they contain no engine logic and are evaluated
by the SignatureMatcher used inside ForwardScanner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from apps.api.domain.rules import Condition


@dataclass(frozen=True)
class EventSignatureDef:
    """Immutable signature definition used by ForwardScanner."""

    signature_id: str
    event_type: str
    classical_source: str
    guarded_forecast_wording: str
    required_conditions: Tuple[Condition, ...]
    optional_conditions: Tuple[Condition, ...] = field(default_factory=tuple)
    weight: int = 100
    version: str = "1.0"


# ----------------------------------------------------------------------
# Signature definitions (Phase 1 vertical: marriage, job_change, financial_gain)
# ----------------------------------------------------------------------


MARRIAGE_VENUS_JUPITER = EventSignatureDef(
    signature_id="marriage_venus_jupiter",
    event_type="marriage",
    classical_source="BPHS Ch. 19, sl. 9-12; Phaladeepika 5.13",
    guarded_forecast_wording="Indicates a favorable window for marriage; "
    "not a guarantee or exact timing.",
    required_conditions=(
        # Venus mahadasha or antardasha active
        Condition("dasha_lord", "in", ["Venus"]),
        Condition("dasha_sub_period", "in", ["Venus"]),
        # Jupiter aspecting 7th house or lord (simplified as fact from orchestrator)
        Condition("jupiter_aspects_7th", "==", True),
    ),
    optional_conditions=(
        Condition("venus_in_7th", "==", True),
        Condition("jupiter_gochara_on_7th", "==", True),
    ),
)


JOB_CHANGE_SUN_SATURN = EventSignatureDef(
    signature_id="job_change_sun_saturn",
    event_type="job_change",
    classical_source="BPHS Ch. 10, sl. 5-8; Saravali Ch. 9",
    guarded_forecast_wording="Suggests a period of potential career change or "
    "job-related disruption; outcomes depend on overall chart strength.",
    required_conditions=(
        Condition("tenth_lord_active", "==", True),
        Condition("saturn_transits_tenth_or_sixth", "==", True),
        Condition("rahuketu_axis_tenth", "==", True),
    ),
    optional_conditions=(
        Condition("sun_mahadasha", "==", True),
        Condition("saturn_aspects_tenth", "==", True),
    ),
)


FINANCIAL_GAIN_JUPITER_VENUS = EventSignatureDef(
    signature_id="financial_gain_jupiter_venus",
    event_type="financial_gain",
    classical_source="BPHS Ch. 13, sl. 1-4; Phaladeepika 6.1-3",
    guarded_forecast_wording="Points to a window of potential financial gain; "
    "actual results depend on natal promises and planetary dignity.",
    required_conditions=(
        Condition("second_or_eleventh_lord_active", "==", True),
        Condition("jupiter_in_second_or_eleventh", "==", True),
        Condition("venus_in_second_or_eleventh", "==", True),
    ),
    optional_conditions=(
        Condition("jupiter_gochara_on_second_or_eleventh", "==", True),
        Condition("venus_aspects_second_or_eleventh", "==", True),
    ),
)


RELOCATION_RAHU_MOON = EventSignatureDef(
    signature_id="relocation_rahu_moon",
    event_type="relocation",
    classical_source="BPHS Ch. 12, sl. 15-18; Saravali Ch. 14",
    guarded_forecast_wording="Indicates potential for long-distance relocation, change of residence, or foreign journey.",
    required_conditions=(
        Condition("ninth_or_twelfth_lord_active", "==", True),
        Condition("rahu_or_moon_active", "==", True),
    ),
    optional_conditions=(
        Condition("fourth_lord_afflicted_or_moving", "==", True),
        Condition("jupiter_transits_ninth_or_twelfth", "==", True),
    ),
)


HEALTH_VULNERABILITY_MARAKA = EventSignatureDef(
    signature_id="health_vulnerability_maraka",
    event_type="health",
    classical_source="BPHS Ch. 44 (Maraka chapters); Phaladeepika Ch. 14",
    guarded_forecast_wording="Suggests periods of vitality sensitivity or need for preventive health care; not a fatalistic assessment.",
    required_conditions=(
        Condition("sixth_or_eighth_lord_active", "==", True),
        Condition("maraka_lord_active", "==", True),
    ),
    optional_conditions=(
        Condition("saturn_aspects_lagna_or_sun", "==", True),
        Condition("rahu_in_eighth", "==", True),
    ),
)


PROGENY_JUPITER_FIFTH = EventSignatureDef(
    signature_id="progeny_jupiter_fifth",
    event_type="progeny",
    classical_source="BPHS Ch. 11, sl. 1-6; Jaimini Upadesha Sutras 1.4",
    guarded_forecast_wording="Points to a favorable timeframe for progeny, childbirth, or conception blessings.",
    required_conditions=(
        Condition("fifth_lord_active", "==", True),
        Condition("jupiter_dasha_or_aspect", "==", True),
    ),
    optional_conditions=(
        Condition("jupiter_transits_fifth_or_lagna", "==", True),
        Condition("d7_saptamsha_benefic", "==", True),
    ),
)


PROPERTY_MARS_FOURTH = EventSignatureDef(
    signature_id="property_mars_fourth",
    event_type="property",
    classical_source="BPHS Ch. 12, sl. 1-5; Phaladeepika Ch. 6",
    guarded_forecast_wording="Indicates auspicious windows for real estate acquisition, property deed, or vehicle purchase.",
    required_conditions=(
        Condition("fourth_lord_active", "==", True),
        Condition("mars_or_venus_active", "==", True),
    ),
    optional_conditions=(
        Condition("jupiter_aspects_fourth", "==", True),
        Condition("d4_chaturthamsha_strong", "==", True),
    ),
)


# Registry of signatures for easy lookup by signature_id or event_type
SIGNATURE_REGISTRY: dict[str, EventSignatureDef] = {
    MARRIAGE_VENUS_JUPITER.signature_id: MARRIAGE_VENUS_JUPITER,
    JOB_CHANGE_SUN_SATURN.signature_id: JOB_CHANGE_SUN_SATURN,
    FINANCIAL_GAIN_JUPITER_VENUS.signature_id: FINANCIAL_GAIN_JUPITER_VENUS,
    RELOCATION_RAHU_MOON.signature_id: RELOCATION_RAHU_MOON,
    HEALTH_VULNERABILITY_MARAKA.signature_id: HEALTH_VULNERABILITY_MARAKA,
    PROGENY_JUPITER_FIFTH.signature_id: PROGENY_JUPITER_FIFTH,
    PROPERTY_MARS_FOURTH.signature_id: PROPERTY_MARS_FOURTH,
    # Also support lookup by event_type
    "marriage": MARRIAGE_VENUS_JUPITER,
    "job_change": JOB_CHANGE_SUN_SATURN,
    "financial_gain": FINANCIAL_GAIN_JUPITER_VENUS,
    "relocation": RELOCATION_RAHU_MOON,
    "health": HEALTH_VULNERABILITY_MARAKA,
    "progeny": PROGENY_JUPITER_FIFTH,
    "property": PROPERTY_MARS_FOURTH,
}


def get_signature(signature_id: str) -> EventSignatureDef:
    """Retrieve a signature by its ID or event_type, raising KeyError if not found."""
    return SIGNATURE_REGISTRY[signature_id]


def list_signatures() -> Tuple[EventSignatureDef, ...]:
    """Return all unique defined signatures."""
    unique_sigs = {s.signature_id: s for s in SIGNATURE_REGISTRY.values()}
    return tuple(unique_sigs.values())