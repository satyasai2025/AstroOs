"""
AstroOS — Shodhana Calculator (Module 10 Phase 2)

Trikona Shodhana and Ekadhipatya Shodhana — the two classical reduction
passes applied to a Bhinnashtakavarga (per-planet), never to
Sarvashtakavarga, which always uses unreduced figures.

**Sourcing — genuinely stronger footing than Phase 1's bindu table.**
Verbatim from the user's own physical copy: C.S. Patel & C.A.S. Aiyar,
*Ashtakavarga* (1957 edition), p. 44 (scan page 80):

    "1. In Trikonashodhana subtract the minimum figure out of the three
    houses of a triad irrespective of the figures in them.
    2. No reduction should be made when one house has no bindu.
    3. If the three figures in the three houses are equal, remove all.
    In the Ekadhipatyashodhana the same rules apply with the exception
    that figures in the house occupied by a planet should not be
    changed."

Rules 2 and 3 are mathematical corollaries of rule 1, not separate
exceptions: subtracting a minimum of 0 is a no-op (rule 2), and
subtracting three equal values reduces all three to 0 (rule 3). Both
are implemented here as the single "subtract the group minimum" rule
rule 1 actually states — the source itself presents 2 and 3 as
illustrative special cases, not additional logic.

Applied sequentially: Trikona Shodhana first, then Ekadhipatya Shodhana
on its result — consistent with the source's own term "Shodhyavashishta"
("that which remains after reduction"), stated as the total after BOTH
reductions, not either one alone.
"""

from __future__ import annotations

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

TRIKONA_GROUPS: tuple[tuple[str, str, str], ...] = (
    ("aries", "leo", "sagittarius"),
    ("taurus", "virgo", "capricorn"),
    ("gemini", "libra", "aquarius"),
    ("cancer", "scorpio", "pisces"),
)

EKADHIPATYA_PAIRS: tuple[tuple[str, str], ...] = (
    ("aries", "scorpio"),
    ("taurus", "libra"),
    ("gemini", "virgo"),
    ("sagittarius", "pisces"),
    ("capricorn", "aquarius"),
)

# Ekadhipatya Shodhana only reduces a planet's OWN bindu table, at the
# ONE pair of rashis IT co-owns — not all 5 pairs applied uniformly to
# every planet. Sun and Moon own exactly one rashi each (Leo, Cancer)
# and are excluded entirely: their tables are never touched by this
# step. Cross-verified against PyJHora's _ekadhipatya_sodhana(), whose
# loop only runs for Mars..Saturn (range(MOON_ID+1, SATURN_ID+1)), each
# planet only ever modifying its own bav[p] at its own rasi_owners[p]
# pair.
PLANET_EKADHIPATYA_PAIR: dict[str, tuple[str, str]] = {
    "mars": ("aries", "scorpio"),
    "venus": ("taurus", "libra"),
    "mercury": ("gemini", "virgo"),
    "jupiter": ("sagittarius", "pisces"),
    "saturn": ("capricorn", "aquarius"),
}

_RULE_VERSION = "1.0"


class ShodhanaCalculator:
    """Stateless — operates purely on an already-computed BhinnashtakavargaResult."""

    def apply_trikona_shodhana(
        self, bhinna: BhinnashtakavargaResult
    ) -> BhinnashtakavargaResult:
        bindus = list(bhinna.bindus_by_rashi)

        for group in TRIKONA_GROUPS:
            indices = [_RASHI_LIST.index(r) for r in group]
            values = [bindus[i] for i in indices]
            minimum = min(values)
            for i in indices:
                bindus[i] -= minimum

        return BhinnashtakavargaResult(
            target_planet=bhinna.target_planet,
            bindus_by_rashi=tuple(bindus),
            total_bindus=sum(bindus),
            rule_version=_RULE_VERSION,
        )

    def apply_ekadhipatya_shodhana(
        self, bhinna: BhinnashtakavargaResult, occupied_rashis: set[str]
    ) -> BhinnashtakavargaResult:
        """
        `occupied_rashis` — rashis occupied by ANY graha in the D1 chart,
        including Rahu/Ketu (see AshtakavargaEngine._occupied_rashis);
        bindus in an occupied rashi are never reduced, per the source's
        stated exception.

        Unlike Trikona Shodhana, this is NOT a "subtract the group
        minimum" operation — it's a REPLACE operation between the two
        co-lorded rashis. Cross-verified against PyJHora's
        jhora.horoscope.chart.ashtakavarga._ekadhipatya_sodhana():
          - Either bindu is 0, or both rashis are occupied -> no change.
          - Both rashis empty: unequal -> both become the lower value;
            equal -> both become 0.
          - Exactly one rashi occupied: the empty one becomes 0 if its
            value is lower than the occupied one's, otherwise the empty
            one is set EQUAL to the occupied one's value (copied, not
            subtracted) — the occupied rashi's own bindu count never
            changes.
        """
        bindus = list(bhinna.bindus_by_rashi)
        pair = PLANET_EKADHIPATYA_PAIR.get(bhinna.target_planet)

        if pair is not None:
            i1, i2 = (_RASHI_LIST.index(r) for r in pair)
            r1, r2 = pair
            v1, v2 = bindus[i1], bindus[i2]
            r1_occupied = r1 in occupied_rashis
            r2_occupied = r2 in occupied_rashis

            if v1 == 0 or v2 == 0 or (r1_occupied and r2_occupied):
                pass
            elif not r1_occupied and not r2_occupied:
                if v1 != v2:
                    lower = min(v1, v2)
                    bindus[i1] = lower
                    bindus[i2] = lower
                else:
                    bindus[i1] = 0
                    bindus[i2] = 0
            elif r1_occupied:
                bindus[i2] = 0 if v2 < v1 else v1
            else:
                bindus[i1] = 0 if v1 < v2 else v2

        return BhinnashtakavargaResult(
            target_planet=bhinna.target_planet,
            bindus_by_rashi=tuple(bindus),
            total_bindus=sum(bindus),
            rule_version=_RULE_VERSION,
        )

    def apply_both(
        self, bhinna: BhinnashtakavargaResult, occupied_rashis: set[str]
    ) -> BhinnashtakavargaResult:
        """
        The full classical reduction pipeline: Trikona Shodhana, then
        Ekadhipatya Shodhana on its result. The result's total is the
        source's "Shodhyavashishta" — bindus remaining after both
        reductions.
        """
        after_trikona = self.apply_trikona_shodhana(bhinna)
        return self.apply_ekadhipatya_shodhana(after_trikona, occupied_rashis)
