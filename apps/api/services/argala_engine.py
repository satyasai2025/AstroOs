"""
AstroOS — Argala & Virodhargala Engine (Layer 6: Calculation Engine)

Stateless service computing the four classical Argala ("intervention")
positions and their corresponding Virodhargala ("counter-argala",
obstruction) positions, counted from a reference sign or planet, on an
already-built D1Chart. No ephemeris/DB dependency.

The four Argala/Virodhargala pairs, counted (inclusively, whole-sign)
from the reference:
    Argala house  ->  Virodhargala house (its obstruction)
    2nd           ->  12th
    4th           ->  10th
    5th           ->  9th
    11th          ->  3rd
Virodhargala cancels its paired Argala when the Virodhargala house's
planet count is greater than or equal to the Argala house's count — a
weaker obstruction (fewer planets) reduces but does not fully cancel it.

Strength scoring: strength_score on each pair is the Argala house's net
benefic occupancy (benefic count - malefic count, natural classification
per jaimini_shared.is_benefic) — positive means net-supportive argala,
negative means net-obstructive/malefic argala, independent of whether
is_cancelled ends up True. The raw score AND the cancellation flag are
reported separately (rather than collapsing a cancelled pair's score to
zero) so the evidence panel can show both "what this house would
contribute" and "whether it actually applies."

On Rahu/Ketu and "reverse counting": Chara Karaka (jaimini_engine.py)
genuinely reverses Rahu's DEGREE-WITHIN-SIGN for ranking purposes,
because that calculation is about a graha's motion. Argala counting is a
different kind of operation — it counts SIGNS from a reference sign, a
purely positional relationship with no notion of "direction of motion."
No classical text (Jaimini's Upadesa Sutras, BPHS) prescribes a reversed
sign-count for Argala when the reference or an occupant is Rahu/Ketu, and
no major reference implementation does either — inventing one here would
be fabricating a rule, not implementing one. Rahu/Ketu instead affect the
result the correct, real way: they are always counted among the
occupants of whichever sign they sit in (contributing to argala/
virodhargala planet counts), and are always classified as natural
malefics (jaimini_shared.NATURAL_MALEFICS) in the strength score.
"""

from __future__ import annotations

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import ArgalaPair, ArgalaResult
from apps.api.services.jaimini_shared import RASHI_LIST, is_benefic, planets_in_rashi, signs_from

_ARGALA_PAIRS: tuple[tuple[int, int], ...] = ((2, 12), (4, 10), (5, 9), (11, 3))
"""(argala_house, virodhargala_house), each counted 1-indexed/inclusive
from the reference sign (offset = house - 1 signs forward)."""


class ArgalaEngine:
    """Stateless Argala/Virodhargala calculator — operates purely on an
    already-computed D1Chart, no ephemeris/DB dependency."""

    def compute(self, chart: D1Chart, reference: str) -> ArgalaResult:
        reference_rashi, label = self._resolve_reference(chart, reference)

        pairs = tuple(
            self._compute_pair(chart, reference_rashi, argala_house, virodh_house)
            for argala_house, virodh_house in _ARGALA_PAIRS
        )
        return ArgalaResult(reference_rashi=reference_rashi, reference_label=label, pairs=pairs)

    @staticmethod
    def _resolve_reference(chart: D1Chart, reference: str) -> tuple[str, str]:
        """`reference` is either a rashi name (used directly) or a graha
        name (resolved to that graha's current rashi)."""
        reference = reference.lower().strip()
        if reference in RASHI_LIST:
            return reference, reference

        matches = [p for p in chart.planets if p.planet == reference]
        if not matches:
            raise ValueError(
                f"{reference!r} is neither a recognized rashi nor a planet present on this chart."
            )
        return matches[0].rashi, reference

    @staticmethod
    def _compute_pair(
        chart: D1Chart, reference_rashi: str, argala_house: int, virodh_house: int
    ) -> ArgalaPair:
        argala_rashi = signs_from(reference_rashi, argala_house - 1)
        virodh_rashi = signs_from(reference_rashi, virodh_house - 1)

        argala_planets = tuple(planets_in_rashi(chart, argala_rashi))
        virodh_planets = tuple(planets_in_rashi(chart, virodh_rashi))

        is_active = len(argala_planets) > 0
        is_cancelled = is_active and len(virodh_planets) >= len(argala_planets)

        benefics = sum(1 for p in argala_planets if is_benefic(p, chart))
        malefics = len(argala_planets) - benefics

        return ArgalaPair(
            argala_house=argala_house,
            virodhargala_house=virodh_house,
            argala_rashi=argala_rashi,
            virodhargala_rashi=virodh_rashi,
            argala_planets=argala_planets,
            virodhargala_planets=virodh_planets,
            is_active=is_active,
            is_cancelled=is_cancelled,
            strength_score=float(benefics - malefics),
        )
