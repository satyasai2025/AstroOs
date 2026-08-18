"""
AstroOS — Guru Research Engine

Custom Research Layer evaluating planetary positions against proprietary/teacher
degree-slice partitions across all 12 rashis. Extensible rule engine supporting
dynamic addition of custom rashi rules, aspect modifiers, and special yogas.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from apps.api.domain.guru_rules import (
    GuruZoneType,
    GuruZoneRule,
    GuruSignPartition,
    PlanetGuruEvaluation,
    GuruChartEvaluation,
)
from packages.shared.dignity import compute_dignity_value


# ---------------------------------------------------------------------------
# Initial Degree Partition Rules (from Teacher's Research Table)
# ---------------------------------------------------------------------------

DEFAULT_GURU_RASHI_PARTITIONS: Dict[str, List[GuruZoneRule]] = {
    "aries": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=10.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="sun",
            description="0-10° Sun Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=10.0,
            end_deg=12.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="mars",
            description="11-12° Mars Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=12.0,
            end_deg=20.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="saturn",
            description="13-20° Saturn Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=20.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="mars",
            description="21-30° Mars Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "taurus": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=3.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="moon",
            description="0-3° Moon Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=3.0,
            end_deg=20.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="moon",
            description="4-20° Moon Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=20.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="venus",
            description="21-30° Venus Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "gemini": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="mercury",
            description="0-30° Mercury Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "cancer": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=5.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="jupiter",
            description="0-5° Jupiter Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=5.0,
            end_deg=28.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="mars",
            description="6-28° Mars Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=28.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="moon",
            description="29-30° Moon Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "leo": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=20.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="sun",
            description="0-20° Sun Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=20.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="sun",
            description="20-30° Sun Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "virgo": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=15.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="mercury",
            description="0-15° Mercury Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=15.0,
            end_deg=20.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="mercury",
            description="16-20° Mercury Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=15.0,
            end_deg=27.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="venus",
            description="16-27° Venus Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=27.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="mercury",
            description="28-30° Mercury Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "libra": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=10.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="sun",
            description="0-10° Sun Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=10.0,
            end_deg=12.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="venus",
            description="11-12° Venus Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=12.0,
            end_deg=20.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="saturn",
            description="13-20° Saturn Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=20.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="venus",
            description="21-30° Venus Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "scorpio": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=3.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="moon",
            description="0-3° Moon Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=3.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="mars",
            description="4-30° Mars Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "sagittarius": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=10.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="jupiter",
            description="0-10° Jupiter Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=10.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="jupiter",
            description="11-30° Jupiter Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "capricorn": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=5.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="jupiter",
            description="0-5° Jupiter Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=5.0,
            end_deg=28.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="mars",
            description="6-28° Mars Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=28.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="saturn",
            description="29-30° Saturn Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "aquarius": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=20.0,
            zone_type=GuruZoneType.MOOLATRIKONA,
            ruling_planet="saturn",
            description="0-20° Saturn Moolatrikona Zone",
            strength_weight=8.0,
        ),
        GuruZoneRule(
            start_deg=20.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="saturn",
            description="21-30° Saturn Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
    "pisces": [
        GuruZoneRule(
            start_deg=0.0,
            end_deg=15.0,
            zone_type=GuruZoneType.DEBILITATION,
            ruling_planet="mercury",
            description="0-15° Mercury Debilitation Zone",
            strength_weight=1.0,
        ),
        GuruZoneRule(
            start_deg=15.0,
            end_deg=27.0,
            zone_type=GuruZoneType.EXALTATION,
            ruling_planet="venus",
            description="16-27° Venus Exaltation Zone",
            strength_weight=10.0,
        ),
        GuruZoneRule(
            start_deg=27.0,
            end_deg=30.0,
            zone_type=GuruZoneType.OWN_SIGN,
            ruling_planet="jupiter",
            description="28-30° Jupiter Own Sign Zone",
            strength_weight=7.0,
        ),
    ],
}


_DIGNITY_MAPPING = {
    "exalted": GuruZoneType.EXALTATION,
    "debilitated": GuruZoneType.DEBILITATION,
    "moolatrikona": GuruZoneType.MOOLATRIKONA,
    "own": GuruZoneType.OWN_SIGN,
    "friendly": GuruZoneType.FRIENDLY,
    "enemy": GuruZoneType.ENEMY,
    "neutral": GuruZoneType.NEUTRAL,
}


class GuruResearchEngine:
    """
    Service for evaluating charts and planetary positions against
    custom Guru Research Layer partitions.
    """

    def __init__(self, custom_partitions: Optional[Dict[str, List[GuruZoneRule]]] = None):
        if custom_partitions is not None:
            self._partitions: Dict[str, List[GuruZoneRule]] = {
                k: list(v) for k, v in custom_partitions.items()
            }
        else:
            self._partitions: Dict[str, List[GuruZoneRule]] = {
                k: list(v) for k, v in DEFAULT_GURU_RASHI_PARTITIONS.items()
            }
        self._custom_modifiers: List[Any] = []

    def register_zone_rule(self, rashi: str, rule: GuruZoneRule, prepend: bool = True) -> None:
        """Add or override a zone rule for a specific rashi."""
        rashi_clean = rashi.lower().strip()
        if rashi_clean not in self._partitions:
            self._partitions[rashi_clean] = []
        if prepend:
            self._partitions[rashi_clean].insert(0, rule)
        else:
            self._partitions[rashi_clean].append(rule)

    def get_all_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get serializable representation of all registered partition rules."""
        result: Dict[str, List[Dict[str, Any]]] = {}
        for rashi, rules in self._partitions.items():
            result[rashi] = [
                {
                    "start_deg": r.start_deg,
                    "end_deg": r.end_deg,
                    "zone_type": r.zone_type.value,
                    "ruling_planet": r.ruling_planet,
                    "description": r.description,
                    "strength_weight": r.strength_weight,
                }
                for r in rules
            ]
        return result

    def find_matching_zone(
        self, planet: str, rashi: str, degree: float
    ) -> Optional[GuruZoneRule]:
        """
        Find the matching Guru research zone rule for a planet in a sign at a given degree.
        If multiple rules match (e.g. Virgo 16-27° Venus vs 16-20° Mercury),
        prioritizes the rule matching the current planet, and then the narrower degree span.
        """
        rashi_clean = rashi.lower().strip()
        planet_clean = planet.lower().strip()
        rules = self._partitions.get(rashi_clean, [])

        matching_rules: List[GuruZoneRule] = []
        for rule in rules:
            if rule.start_deg <= degree <= rule.end_deg:
                matching_rules.append(rule)

        if not matching_rules:
            return None

        # Sort matching rules: prefer ruler match first, then narrower span (end_deg - start_deg)
        def _sort_key(r: GuruZoneRule):
            ruler_match_priority = 0 if r.ruling_planet.lower() == planet_clean else 1
            span = r.end_deg - r.start_deg
            return (ruler_match_priority, span)

        sorted_rules = sorted(matching_rules, key=_sort_key)
        return sorted_rules[0]

    def evaluate_planet(
        self, planet: str, rashi: str, degree: float
    ) -> PlanetGuruEvaluation:
        """
        Evaluates a single planet against both classical Parashari rules and the Guru Research Layer.
        """
        planet_clean = planet.lower().strip()
        rashi_clean = rashi.lower().strip()

        classical_dignity = compute_dignity_value(planet_clean, rashi_clean, degree)
        zone_rule = self.find_matching_zone(planet_clean, rashi_clean, degree)

        if zone_rule:
            zone_name = zone_rule.description
            zone_type = zone_rule.zone_type
            zone_lord = zone_rule.ruling_planet
            zone_range = f"{zone_rule.start_deg:.1f}° - {zone_rule.end_deg:.1f}°"
            is_ruler_match = (zone_lord.lower() == planet_clean)
            
            classical_mapped = _DIGNITY_MAPPING.get(classical_dignity.lower()) if classical_dignity else None
            is_agreement = (
                is_ruler_match and classical_mapped is not None and classical_mapped == zone_type
            )
            notes = (
                f"Planet sits in {zone_name} (Lord: {zone_lord.capitalize()}). "
                + ("Direct ruler match. " if is_ruler_match else f"Guest graha in {zone_lord}'s zone. ")
                + ("Aligns with classical dignity." if is_agreement else f"Classical dignity is '{classical_dignity}'.")
            )
        else:
            zone_name = "General / Unpartitioned Zone"
            zone_type = GuruZoneType.NEUTRAL
            zone_lord = "rashi_lord"
            zone_range = "0.0° - 30.0°"
            is_ruler_match = False
            is_agreement = True
            notes = f"No custom partition defined. Classical dignity: '{classical_dignity}'."

        return PlanetGuruEvaluation(
            planet=planet_clean,
            rashi=rashi_clean,
            degree_in_rashi=degree,
            classical_dignity=classical_dignity,
            guru_zone_name=zone_name,
            guru_zone_type=zone_type,
            guru_zone_lord=zone_lord,
            guru_zone_range=zone_range,
            is_ruler_match=is_ruler_match,
            is_dignity_agreement=is_agreement,
            notes=notes,
        )

    def evaluate_chart(
        self, planetary_positions: List[Dict[str, Any]]
    ) -> GuruChartEvaluation:
        """
        Evaluates an entire chart's planetary positions.
        Input list expects dicts with keys: 'planet', 'rashi', 'degree_in_rashi' (or 'rashi_degree').
        """
        evaluations: List[PlanetGuruEvaluation] = []
        agreements = 0
        deviations = 0
        insights: List[str] = []

        for p in planetary_positions:
            planet = p.get("planet") or p.get("name", "")
            rashi = p.get("rashi") or p.get("sign", "")
            degree = float(p.get("degree_in_rashi") or p.get("rashi_degree") or p.get("degree", 0.0))

            if not planet or not rashi:
                continue

            evaluation = self.evaluate_planet(planet, rashi, degree)
            evaluations.append(evaluation)

            if evaluation.is_dignity_agreement:
                agreements += 1
            else:
                deviations += 1

            if evaluation.is_ruler_match:
                insights.append(
                    f"{evaluation.planet.capitalize()} is in its dedicated {evaluation.guru_zone_name} in {evaluation.rashi.capitalize()}."
                )

        return GuruChartEvaluation(
            evaluations=evaluations,
            agreements_count=agreements,
            deviations_count=deviations,
            summary_insights=insights,
        )
