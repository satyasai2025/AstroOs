"""
AstroOS — Yoga Strength Scoring (Phase 2, v2.1.0)

Computes a 0–100 numerical strength score for each detected yoga based on:
  1. Planetary dignity (exalted, own sign, debilitated, etc.)
  2. House placement (kendra, trikona, upachaya, dusthana)
  3. Benefic/malefic aspects on involved planets
  4. Conjunction quality (benefic/malefic companions)
  5. Combustion and retrograde status

The score is independent of the categorical strength ("full"/"partial"/"cancelled")
already returned by YogaResult — it provides a finer-grained, quantitative
measure useful for comparative research across charts.

Design rationale (CKO-ENG coordination):
  - Dignity weights mirror GrahaEngine._STRENGTH_WEIGHTS (Module 5) but
    scaled to a 0-100 range.
  - Aspect/conjunction modifiers use the standard Parashari drishti table.
  - The function is a pure computation — no side effects, no registry
    dependency — so evaluators can call it once the involved planets are known.
"""

from __future__ import annotations

from apps.api.domain.yoga import YogaResult
from apps.api.services.graha_engine import GrahaEngine, DUSTHANA_HOUSES, KENDRA_HOUSES, TRIKONA_HOUSES
from apps.api.services.yoga_predicates import (
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    YogaContext,
    get_planet,
    is_aspecting,
)

_graha_engine = GrahaEngine()

# Dignity contribution weights (0–25 scale per planet)
_DIGNITY_SCORES = {
    "exalted":     25,
    "moolatrikona": 22,
    "own":         20,
    "friendly":    15,
    "neutral":     10,
    "enemy":        5,
    "debilitated":  0,
}

# House placement contribution (0–15 scale)
_HOUSE_SCORES = {
    # Kendra (1/4/7/10) and Trikona (1/5/9) — highest for yoga placement
    1: 15, 4: 13, 7: 14, 10: 13,   # kendra
    5: 14, 9: 15,                    # trikona (1 is also kendra, handled above)
    # Upachaya (3/6/10/11) — growth houses
    3: 10, 6: 8, 11: 10,
    # Neutral houses (2/7 — 7 is also kendra)
    2: 9,
    # Dusthana (6/8/12) — inauspicious
    8: 4, 12: 3,
    # Maraka (2/7 — 2 handled above, 7 is kendra)
}

# Aspect modifiers per planet (positive = benefic aspect adds, negative = malefic subtracts)
_ASPECT_BONUS_BENEFIC = 4    # per benefic aspect on an involved planet
_ASPECT_PENALTY_MALEFIC = -5  # per malefic aspect on an involved planet
_CONJUNCT_BONUS_BENEFIC = 3  # per benefic conjunct with an involved planet
_CONJUNCT_PENALTY_MALEFIC = -4  # per malefic conjunct with an involved planet
_COMBUST_PENALTY = -6
_RETROGRADE_MODIFIER = 2     # retrograde often strengthens (classical view)


def _dignity_score(planet: str, rashi: str, rashi_degree: float) -> int:
    """Dignity-based score for one planet (0–25)."""
    dignity = _graha_engine.compute_dignity(planet, rashi, rashi_degree)
    if dignity is None:
        return 10  # neutral default for Rahu/Ketu
    return _DIGNITY_SCORES.get(dignity.value, 10)


def _house_score(house_number: int) -> int:
    """House placement score for one planet (0–15)."""
    return _HOUSE_SCORES.get(house_number, 8)  # default neutral


def _aspect_conjunction_modifier(
    ctx: YogaContext, planet: str, involved_set: set[str]
) -> int:
    """
    Compute the net modifier from benefic/malefic aspects and conjunctions
    on a single involved planet (from planets NOT in the involved set).
    """
    modifier = 0
    for other_name in ctx.planets_by_name:
        if other_name == planet or other_name in involved_set:
            continue
        # Check if other aspects this planet
        if is_aspecting(ctx, other_name, planet):
            if other_name in NATURAL_BENEFICS:
                modifier += _ASPECT_BONUS_BENEFIC
            elif other_name in NATURAL_MALEFICS:
                modifier += _ASPECT_PENALTY_MALEFIC
        # Check conjunction (same house)
        other_pos = ctx.planets_by_name.get(other_name)
        planet_pos = ctx.planets_by_name.get(planet)
        if other_pos and planet_pos and other_pos.house_number == planet_pos.house_number:
            if other_name in NATURAL_BENEFICS:
                modifier += _CONJUNCT_BONUS_BENEFIC
            elif other_name in NATURAL_MALEFICS:
                modifier += _CONJUNCT_PENALTY_MALEFIC
    return modifier


def compute_yoga_strength_score(
    ctx: YogaContext,
    result: YogaResult,
) -> int:
    """
    Compute a 0–100 strength score for a yoga that is present (is_present=True).

    The score is the average per-planet contribution, each planet's contribution
    being: dignity(0-25) + house(0-15) + aspects/modifiers + combustion/retro.

    If the yoga is not present, returns 0.

    Algorithm:
      For each involved planet:
        base = dignity_score + house_score
        base += aspect_conjunction_modifier
        base += combustion_penalty (if combust)
        base += retrograde_modifier (if retrograde)
        clamp to [0, 40]

      total = average of all per-planet scores, normalized to 0–100.
      Max possible per-planet = 25 + 15 + lots_of_benefic_aspects = ~40
      So 40 per planet is the practical ceiling, normalized to 100.
    """
    if not result.is_present:
        return 0

    if not result.involved_planets:
        return 0

    involved_set = set(result.involved_planets)
    per_planet_scores: list[int] = []

    for planet in result.involved_planets:
        pos = ctx.planets_by_name.get(planet)
        if pos is None:
            continue

        score = _dignity_score(planet, pos.rashi, pos.rashi_degree)
        score += _house_score(pos.house_number)
        score += _aspect_conjunction_modifier(ctx, planet, involved_set)

        if pos.is_combust:
            score += _COMBUST_PENALTY
        if pos.is_retrograde:
            score += _RETROGRADE_MODIFIER

        # Clamp per-planet score to [0, 40]
        score = max(0, min(40, score))
        per_planet_scores.append(score)

    if not per_planet_scores:
        return 0

    # Average and normalize: max practical per-planet is 40 → maps to 100
    avg = sum(per_planet_scores) / len(per_planet_scores)
    normalized = round((avg / 40.0) * 100)
    return max(0, min(100, normalized))


def compute_strength_score_for_all(
    ctx: YogaContext,
    results: list[YogaResult],
) -> list[YogaResult]:
    """
    Convenience: re-score a batch of YogaResults with numerical strength.
    Returns new YogaResult instances with strength_score populated.
    Uses dataclasses.replace() to preserve frozen immutability.
    """
    from dataclasses import replace
    scored: list[YogaResult] = []
    for r in results:
        score = compute_yoga_strength_score(ctx, r) if r.is_present else 0
        scored.append(replace(r, strength_score=score))
    return scored
