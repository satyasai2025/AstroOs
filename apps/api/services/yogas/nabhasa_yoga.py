"""
AstroOS — Nabhasa Yogas (BPHS-NY-001 through 018)

Architecturally distinct from every other yoga in the catalog (Design
Audit §3/§4): these examine the aggregate distribution of ALL planets
across sign modalities or sign positions at once, not a relationship
between 2-3 named planets/houses.

Phase 1 (v2.0.0) — Ashraya sub-category (3 yogas):
  BPHS-NY-001 Rajju Yoga   — all 7 classical grahas in movable signs
  BPHS-NY-002 Musala Yoga  — all 7 classical grahas in fixed signs
  BPHS-NY-003 Nala Yoga    — all 7 classical grahas in dual signs

Phase 2 (v2.1.0 "Vistara") — Sankhya, Akriti, Dala sub-categories (15 yogas):

  Sankhya (count-based — how many signs span the planetary distribution):
  BPHS-NY-004 Kedara Nabhasa — each of the 7 grahas in a different sign
  BPHS-NY-005 Pasha Nabhasa  — all 7 grahas within 5 consecutive signs
  BPHS-NY-006 Dama Nabhasa   — all 7 grahas within 6 consecutive signs
  BPHS-NY-007 Dhvaja Nabhasa — all 7 grahas within 4 consecutive signs
  BPHS-NY-008 Gola Nabhasa   — all 7 grahas within 2 adjacent signs
  BPHS-NY-009 Yuga Nabhasa   — planets split between a sign and its 7th

  Akriti (shape-based — the visual pattern of planetary distribution):
  BPHS-NY-010 Hala Nabhasa   — all 7 grahas in 6 consecutive signs
  BPHS-NY-011 Vajra Nabhasa  — all grahas in lagna sign or its 7th only
  BPHS-NY-012 Yava Nabhasa   — planets in 2 pairs of opposite signs
  BPHS-NY-013 Kamala Nabhasa — all planets in kendra houses from lagna
  BPHS-NY-014 Vapi Nabhasa   — all 7 grahas within 3 consecutive signs
  BPHS-NY-015 Dhanu Nabhasa  — planets spread across 10+ different signs

  Dala (benefic/malefic concentration):
  BPHS-NY-016 Malavya Dala — all natural benefics in kendra from lagna
  BPHS-NY-017 Sarala Dala  — all natural malefics in kendra from lagna
  BPHS-NY-018 Mukuta Dala  — all planets in kendra or trikona houses
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import (
    CLASSICAL_SEVEN,
    DUAL_SIGNS,
    FIXED_SIGNS,
    KENDRA_HOUSES,
    MOVABLE_SIGNS,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    TRIKONA_HOUSES,
    YogaContext,
    get_house,
    get_planet,
)
from apps.api.services.yoga_registry import register_yoga


def _make_ashraya_evaluator(yoga_id: str, name: str, sign_set: frozenset, modality_label: str):
    def evaluate(ctx: YogaContext) -> Optional[YogaResult]:
        trace: list[str] = []
        satisfied: list[str] = []
        missing: list[str] = []

        rashis_by_planet: dict[str, str] = {}
        for planet in CLASSICAL_SEVEN:
            position = get_planet(ctx, planet)
            if position is None:
                missing.append(f"{planet} not found in chart")
                trace.append(f"{planet} not found in chart — cannot evaluate")
                return YogaResult(
                    yoga_id=yoga_id, name=name, category="Nabhasa Yoga",
                    source_text="BPHS", rule_version="1.0", is_present=False,
                    strength=None, missing=tuple(missing), trace=tuple(trace),
                )
            rashis_by_planet[planet] = position.rashi

        trace.append(f"Step 1: rashis for all 7 classical grahas → {rashis_by_planet}")

        outside_modality = {p: r for p, r in rashis_by_planet.items() if r not in sign_set}
        trace.append(
            f"Step 2: grahas NOT in a {modality_label} sign → "
            f"{outside_modality if outside_modality else 'none'}"
        )

        is_present = len(outside_modality) == 0
        if is_present:
            satisfied.append(f"All 7 classical grahas are in {modality_label} signs")
        else:
            for planet, rashi in outside_modality.items():
                missing.append(f"{planet} is in {rashi}, not a {modality_label} sign")

        trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

        return YogaResult(
            yoga_id=yoga_id, name=name, category="Nabhasa Yoga",
            source_text="BPHS", rule_version="1.0", is_present=is_present,
            strength="full" if is_present else None,
            involved_planets=tuple(CLASSICAL_SEVEN),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        )
    return evaluate


register_yoga(
    yoga_id="BPHS-NY-001", name="Rajju Yoga", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="1.0", requires=("D1", "GrahaEngine"),
)(_make_ashraya_evaluator("BPHS-NY-001", "Rajju Yoga", frozenset(MOVABLE_SIGNS), "movable"))

register_yoga(
    yoga_id="BPHS-NY-002", name="Musala Yoga", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="1.0", requires=("D1", "GrahaEngine"),
)(_make_ashraya_evaluator("BPHS-NY-002", "Musala Yoga", frozenset(FIXED_SIGNS), "fixed"))

register_yoga(
    yoga_id="BPHS-NY-003", name="Nala Yoga", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="1.0", requires=("D1", "GrahaEngine"),
)(_make_ashraya_evaluator("BPHS-NY-003", "Nala Yoga", frozenset(DUAL_SIGNS), "dual"))


# ---------------------------------------------------------------------------
# Phase 2: Sankhya Nabhasa (count-based distribution)
# ---------------------------------------------------------------------------

def _get_planet_signs(ctx: YogaContext) -> dict[str, str]:
    """Get sign (rashi) placements for all 7 classical grahas."""
    signs: dict[str, str] = {}
    for planet in CLASSICAL_SEVEN:
        pos = get_planet(ctx, planet)
        if pos is not None:
            signs[planet] = pos.rashi
    return signs


def _sign_span(signs: list[str]) -> int:
    """
    Compute the minimum number of consecutive signs needed to contain all
    given signs. Returns the span (count of signs in the range).
    """
    if not signs:
        return 0
    _SIGN_ORDER = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    indices = sorted(set(_SIGN_ORDER.index(s) for s in signs))
    if len(indices) == 1:
        return 1
    # Check all possible wrap-around spans
    min_span = len(_SIGN_ORDER)
    for start_idx in indices:
        span = 1
        for next_idx in indices:
            if next_idx == start_idx:
                continue
            gap = (next_idx - start_idx) % 12
            if gap < span:
                continue  # already covered
            span = gap + 1
        min_span = min(min_span, span)
    return min_span


def _planets_spanning_n_signs(ctx: YogaContext, n: int) -> tuple[bool, list[str], list[str], str]:
    """
    Check if all 7 classical grahas span exactly n consecutive signs.
    Returns (is_present, satisfied, missing, label).
    """
    trace_info = ""
    signs_map = _get_planet_signs(ctx)
    if len(signs_map) < 7:
        return False, [], [f"Only {len(signs_map)}/7 classical grahas found"], "insufficient"

    all_signs = list(signs_map.values())
    span = _sign_span(all_signs)
    trace_info = f"signs={signs_map}, span={span}"

    is_present = span <= n
    if is_present:
        satisfied = [f"All 7 grahas span {span} signs (within {n})"]
        missing = []
    else:
        satisfied = []
        missing = [f"Grahas span {span} signs (exceeds {n})"]
    return is_present, satisfied, missing, trace_info


def _make_sankhya_evaluator(yoga_id: str, name: str, max_span: int, require_unique: bool = False):
    """Factory for Sankhya Nabhasa evaluators (sign-span check).

    Args:
        yoga_id: BPHS identifier.
        name: Human-readable name.
        max_span: Maximum allowed consecutive sign span.
        require_unique: If True, also require that ALL 7 planets are in different signs.
    """
    def evaluate(ctx: YogaContext) -> Optional[YogaResult]:
        trace: list[str] = []
        satisfied: list[str] = []
        missing: list[str] = []

        signs_map = _get_planet_signs(ctx)
        trace.append(f"Step 1: graha signs → {signs_map}")

        if len(signs_map) < 7:
            missing.append(f"Only {len(signs_map)}/7 classical grahas found")
            return YogaResult(
                yoga_id=yoga_id, name=name, category="Nabhasa Yoga",
                source_text="BPHS", rule_version="2.0", is_present=False,
                strength=None, missing=tuple(missing), trace=tuple(trace),
            )

        all_signs = list(signs_map.values())
        span = _sign_span(all_signs)
        unique_signs = len(set(all_signs))

        # For Kedara, require exactly 7 different signs (no two in the same)
        unique_ok = not require_unique or unique_signs == 7

        trace.append(f"Step 2: sign span = {span}, unique signs = {unique_signs}")

        is_present = span <= max_span and unique_ok
        if is_present:
            details = f"All 7 grahas span {span} signs with {unique_signs} unique (max span: {max_span})"
            satisfied.append(details)
            counter_examples = [
                f"Yoga would weaken if any planet moved outside the current {span}-sign cluster",
                f"If grahas were spread across {max_span + 1}+ signs, this yoga would not form",
            ]
        else:
            if span > max_span:
                missing.append(f"Grahas span {span} signs (max allowed: {max_span})")
            if require_unique and unique_signs < 7:
                missing.append(f"Only {unique_signs} unique signs found (need all 7 different)")
            counter_examples = []

        trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

        return YogaResult(
            yoga_id=yoga_id, name=name, category="Nabhasa Yoga",
            source_text="BPHS", rule_version="2.0", is_present=is_present,
            strength="full" if is_present else None,
            involved_planets=tuple(CLASSICAL_SEVEN),
            satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
            counter_examples=tuple(counter_examples),
        )
    return evaluate


# BPHS-NY-004: Kedara — all 7 in different signs (span = 7, require unique)
register_yoga(
    yoga_id="BPHS-NY-004", name="Kedara Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-004", "Kedara Nabhasa", 7, require_unique=True))

# BPHS-NY-005: Pasha — all 7 within 5 signs
register_yoga(
    yoga_id="BPHS-NY-005", name="Pasha Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-005", "Pasha Nabhasa", 5))

# BPHS-NY-006: Dama — all 7 within 6 signs
register_yoga(
    yoga_id="BPHS-NY-006", name="Dama Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-006", "Dama Nabhasa", 6))

# BPHS-NY-007: Dhvaja — all 7 within 4 signs
register_yoga(
    yoga_id="BPHS-NY-007", name="Dhvaja Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-007", "Dhvaja Nabhasa", 4))

# BPHS-NY-008: Gola — all 7 within 2 signs
register_yoga(
    yoga_id="BPHS-NY-008", name="Gola Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-008", "Gola Nabhasa", 2))

# BPHS-NY-009: Yuga — planets split between a sign and its 7th (opposite)
def _evaluate_yuga(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    _SIGN_ORDER = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    _OPPOSITE = {s: _SIGN_ORDER[(i + 6) % 12] for i, s in enumerate(_SIGN_ORDER)}

    signs_map = _get_planet_signs(ctx)
    trace.append(f"Step 1: graha signs → {signs_map}")

    if len(signs_map) < 7:
        missing.append(f"Only {len(signs_map)}/7 classical grahas found")
        return YogaResult(
            yoga_id="BPHS-NY-009", name="Yuga Nabhasa", category="Nabhasa Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=tuple(missing), trace=tuple(trace),
        )

    unique_signs = set(signs_map.values())
    trace.append(f"Step 2: unique signs → {unique_signs}")

    # Check all pairs of opposite signs
    for sign_a in unique_signs:
        sign_b = _OPPOSITE[sign_a]
        if sign_b not in unique_signs:
            continue
        remaining = unique_signs - {sign_a, sign_b}
        if not remaining:  # all planets in exactly 2 opposite signs
            satisfied.append(f"All grahas in {sign_a} and its opposite {sign_b}")
            trace.append(f"Step 3: rule satisfied — all in {sign_a}/{sign_b}")
            return YogaResult(
                yoga_id="BPHS-NY-009", name="Yuga Nabhasa", category="Nabhasa Yoga",
                source_text="BPHS", rule_version="2.0", is_present=True,
                strength="full",
                involved_planets=tuple(CLASSICAL_SEVEN),
                satisfied=tuple(satisfied), missing=(), trace=tuple(trace),
                counter_examples=(
                    f"If any graha moved to a third sign (not {sign_a} or {sign_b}), the yoga would break",
                ),
            )

    missing.append("Grahas are not split between two opposite signs")
    trace.append("Step 3: rule not satisfied")

    return YogaResult(
        yoga_id="BPHS-NY-009", name="Yuga Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=False,
        strength=None, involved_planets=tuple(CLASSICAL_SEVEN),
        satisfied=(), missing=tuple(missing), trace=tuple(trace),
    )


register_yoga(
    yoga_id="BPHS-NY-009", name="Yuga Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_evaluate_yuga)


# ---------------------------------------------------------------------------
# Phase 2: Akriti Nabhasa (shape-based distribution)
# ---------------------------------------------------------------------------

# BPHS-NY-010: Hala — all 7 in 6 consecutive signs (exactly half zodiac)
register_yoga(
    yoga_id="BPHS-NY-010", name="Hala Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-010", "Hala Nabhasa", 6))

# BPHS-NY-011: Vajra — all grahas in lagna sign or its 7th only
def _evaluate_vajra(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    _SIGN_ORDER = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    _OPPOSITE = {s: _SIGN_ORDER[(i + 6) % 12] for i, s in enumerate(_SIGN_ORDER)}

    lagna_rashi = get_house(ctx, 1).rashi
    opposite_sign = _OPPOSITE[lagna_rashi]
    trace.append(f"Step 1: lagna sign = {lagna_rashi}, 7th sign = {opposite_sign}")

    signs_map = _get_planet_signs(ctx)
    trace.append(f"Step 2: graha signs → {signs_map}")

    if len(signs_map) < 7:
        missing.append(f"Only {len(signs_map)}/7 classical grahas found")
        return YogaResult(
            yoga_id="BPHS-NY-011", name="Vajra Nabhasa", category="Nabhasa Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=tuple(missing), trace=tuple(trace),
        )

    allowed = {lagna_rashi, opposite_sign}
    outside = {p: s for p, s in signs_map.items() if s not in allowed}
    trace.append(f"Step 3: grahas outside {allowed} → {outside}")

    is_present = len(outside) == 0
    if is_present:
        satisfied.append(f"All grahas in {lagna_rashi} or {opposite_sign}")
    else:
        for p, s in outside.items():
            missing.append(f"{p} is in {s}, not in {lagna_rashi} or {opposite_sign}")

    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    counter_examples = []
    if is_present:
        counter_examples = [
            f"If any graha moved to a sign other than {lagna_rashi} or {opposite_sign}, the yoga would break",
        ]

    return YogaResult(
        yoga_id="BPHS-NY-011", name="Vajra Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(CLASSICAL_SEVEN),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-011", name="Vajra Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1", "HouseEngine"),
)(_evaluate_vajra)

# BPHS-NY-012: Yava — planets in 2 pairs of opposite signs
def _evaluate_yava(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []

    _SIGN_ORDER = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    _OPPOSITE = {s: _SIGN_ORDER[(i + 6) % 12] for i, s in enumerate(_SIGN_ORDER)}

    signs_map = _get_planet_signs(ctx)
    trace.append(f"Step 1: graha signs → {signs_map}")

    if len(signs_map) < 7:
        return YogaResult(
            yoga_id="BPHS-NY-012", name="Yava Nabhasa", category="Nabhasa Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=(f"Only {len(signs_map)}/7 classical grahas found",),
            trace=tuple(trace),
        )

    unique_signs = set(signs_map.values())
    trace.append(f"Step 2: unique signs → {unique_signs}")

    # Find all opposite-sign pairs present in the chart
    found_pairs: list[tuple[str, str]] = []
    checked: set[str] = set()
    for sign in unique_signs:
        if sign in checked:
            continue
        opp = _OPPOSITE[sign]
        if opp in unique_signs:
            found_pairs.append(tuple(sorted((sign, opp))))
            checked.add(sign)
            checked.add(opp)

    trace.append(f"Step 3: opposite-sign pairs → {found_pairs}")
    is_present = len(found_pairs) == 2 and len(unique_signs) == 4
    satisfied, missing = [], []
    if is_present:
        satisfied.append(f"Planets distributed across 2 pairs of opposite signs: {found_pairs}")
        counter_examples = [
            "If any planet moved to a 5th sign, the yoga would break",
        ]
    else:
        missing.append(f"Found {len(found_pairs)} opposite pairs with {len(unique_signs)} unique signs (need exactly 2 pairs / 4 signs)")
        counter_examples = []

    trace.append(f"Step 4: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-NY-012", name="Yava Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(CLASSICAL_SEVEN),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-012", name="Yava Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_evaluate_yava)


# BPHS-NY-013: Kamala — all planets in kendra houses from lagna
def _evaluate_kamala(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    signs_map = _get_planet_signs(ctx)
    trace.append(f"Step 1: graha signs → {signs_map}")

    if len(signs_map) < 7:
        return YogaResult(
            yoga_id="BPHS-NY-013", name="Kamala Nabhasa", category="Nabhasa Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=(f"Only {len(signs_map)}/7 classical grahas found",),
            trace=tuple(trace),
        )

    in_kendra = []
    not_in_kendra = []
    for planet in CLASSICAL_SEVEN:
        pos = get_planet(ctx, planet)
        if pos is not None:
            if pos.house_number in KENDRA_HOUSES:
                in_kendra.append(planet)
            else:
                not_in_kendra.append(planet)

    trace.append(f"Step 2: in kendra → {in_kendra}, not in kendra → {not_in_kendra}")
    is_present = len(not_in_kendra) == 0

    if is_present:
        satisfied.append("All 7 grahas are in kendra houses from lagna")
        counter_examples = [
            "If any graha moved to a non-kendra house (2/3/5/6/8/9/11/12), the yoga would break",
        ]
    else:
        missing.append(f"{len(not_in_kendra)} grahas not in kendra: {not_in_kendra}")
        counter_examples = []

    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-NY-013", name="Kamala Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(CLASSICAL_SEVEN),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-013", name="Kamala Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1", "HouseEngine"),
)(_evaluate_kamala)

# BPHS-NY-014: Vapi — all 7 within 3 consecutive signs
register_yoga(
    yoga_id="BPHS-NY-014", name="Vapi Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_make_sankhya_evaluator("BPHS-NY-014", "Vapi Nabhasa", 3))

# BPHS-NY-015: Dhanu — all planets in 10+ different signs
def _evaluate_dhanu(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    signs_map = _get_planet_signs(ctx)
    trace.append(f"Step 1: graha signs → {signs_map}")

    if len(signs_map) < 7:
        return YogaResult(
            yoga_id="BPHS-NY-015", name="Dhanu Nabhasa", category="Nabhasa Yoga",
            source_text="BPHS", rule_version="2.0", is_present=False,
            strength=None, missing=(f"Only {len(signs_map)}/7 classical grahas found",),
            trace=tuple(trace),
        )

    unique_count = len(set(signs_map.values()))
    trace.append(f"Step 2: unique signs = {unique_count}")

    is_present = unique_count >= 6
    if is_present:
        satisfied.append(f"Grahas spread across {unique_count} different signs (>= 6)")
        counter_examples = [
            f"If grahas were concentrated in fewer than 6 signs, this yoga would not form",
        ]
    else:
        missing.append(f"Only {unique_count} unique signs (need >= 6)")
        counter_examples = []

    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-NY-015", name="Dhanu Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(CLASSICAL_SEVEN),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-015", name="Dhanu Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1",),
)(_evaluate_dhanu)


# ---------------------------------------------------------------------------
# Phase 2: Dala Nabhasa (benefic/malefic concentration)
# ---------------------------------------------------------------------------

# BPHS-NY-016: Malavya Dala — all natural benefics in kendra from lagna
def _evaluate_malavya_dala(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    benefics_in_kendra = []
    benefics_not_in_kendra = []
    for planet in CLASSICAL_SEVEN:
        if planet not in NATURAL_BENEFICS:
            continue
        pos = get_planet(ctx, planet)
        if pos is None:
            missing.append(f"{planet} not found in chart")
            continue
        if pos.house_number in KENDRA_HOUSES:
            benefics_in_kendra.append(planet)
        else:
            benefics_not_in_kendra.append(planet)

    trace.append(f"Step 1: benefics in kendra → {benefics_in_kendra}")
    trace.append(f"Step 2: benefics NOT in kendra → {benefics_not_in_kendra}")

    is_present = len(benefics_not_in_kendra) == 0 and len(benefics_in_kendra) > 0
    if is_present:
        satisfied.append(f"All natural benefics ({benefics_in_kendra}) in kendra from lagna")
        counter_examples = [
            "If any benefic moved to a non-kendra house, this Dala yoga would break",
            "A malefic in kendra does not affect this yoga — only benefic placement matters",
        ]
    else:
        if benefics_not_in_kendra:
            missing.append(f"Benefics NOT in kendra: {benefics_not_in_kendra}")
        counter_examples = []

    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-NY-016", name="Malavya Dala Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(benefics_in_kendra),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-016", name="Malavya Dala Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1", "HouseEngine"),
)(_evaluate_malavya_dala)


# BPHS-NY-017: Sarala Dala — all natural malefics in kendra from lagna
def _evaluate_sarala_dala(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    malefics_in_kendra = []
    malefics_not_in_kendra = []
    for planet in CLASSICAL_SEVEN:
        if planet not in NATURAL_MALEFICS:
            continue
        pos = get_planet(ctx, planet)
        if pos is None:
            missing.append(f"{planet} not found in chart")
            continue
        if pos.house_number in KENDRA_HOUSES:
            malefics_in_kendra.append(planet)
        else:
            malefics_not_in_kendra.append(planet)

    trace.append(f"Step 1: malefics in kendra → {malefics_in_kendra}")
    trace.append(f"Step 2: malefics NOT in kendra → {malefics_not_in_kendra}")

    is_present = len(malefics_not_in_kendra) == 0 and len(malefics_in_kendra) > 0
    if is_present:
        satisfied.append(f"All natural malefics ({malefics_in_kendra}) in kendra from lagna")
        counter_examples = [
            "If any malefic moved to a non-kendra house, this Dala yoga would break",
            "A benefic in kendra does not affect this yoga — only malefic placement matters",
        ]
    else:
        if malefics_not_in_kendra:
            missing.append(f"Malefics NOT in kendra: {malefics_not_in_kendra}")
        counter_examples = []

    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-NY-017", name="Sarala Dala Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(malefics_in_kendra),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-017", name="Sarala Dala Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1", "HouseEngine"),
)(_evaluate_sarala_dala)


# BPHS-NY-018: Mukuta Dala — all planets in kendra or trikona houses
def _evaluate_mukuta_dala(ctx: YogaContext) -> Optional[YogaResult]:
    trace: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    kendra_trikona = KENDRA_HOUSES | TRIKONA_HOUSES
    in_target = []
    outside_target = []

    for planet in CLASSICAL_SEVEN:
        pos = get_planet(ctx, planet)
        if pos is None:
            missing.append(f"{planet} not found in chart")
            continue
        if pos.house_number in kendra_trikona:
            in_target.append(planet)
        else:
            outside_target.append(planet)

    trace.append(f"Step 1: planets in kendra/trikona → {in_target}")
    trace.append(f"Step 2: planets outside → {outside_target}")

    is_present = len(outside_target) == 0 and len(in_target) > 0
    if is_present:
        satisfied.append(f"All grahas ({in_target}) in kendra or trikona houses")
        counter_examples = [
            "If any graha moved to houses 2/3/6/8/11/12, this yoga would break",
        ]
    else:
        if outside_target:
            missing.append(f"Grahas outside kendra/trikona: {outside_target}")
        counter_examples = []

    trace.append(f"Step 3: rule {'satisfied' if is_present else 'not satisfied'}")

    return YogaResult(
        yoga_id="BPHS-NY-018", name="Mukuta Dala Nabhasa", category="Nabhasa Yoga",
        source_text="BPHS", rule_version="2.0", is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=tuple(in_target),
        satisfied=tuple(satisfied), missing=tuple(missing), trace=tuple(trace),
        counter_examples=tuple(counter_examples),
    )


register_yoga(
    yoga_id="BPHS-NY-018", name="Mukuta Dala Nabhasa", category="Nabhasa Yoga",
    source_text="BPHS", rule_version="2.0", requires=("D1", "HouseEngine"),
)(_evaluate_mukuta_dala)
