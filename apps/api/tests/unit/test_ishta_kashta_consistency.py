"""
AstroOS — Ishta/Kashta Bala cross-implementation consistency tests.

WHY THIS FILE EXISTS
--------------------
AstroOS contains TWO Ishta/Kashta implementations:

  A. apps/api/services/shadbala/ishta_kashta_bala.py  (IshtaKashtaBalaCalculator)
  B. apps/api/services/shadbala/saravali_summary.py   (inline fallback)

They previously DISAGREED on Kashta — A used `60 - Ishta`, B used
`sqrt((60 - Uchcha) * (60 - Chesta))` — diverging for every input where
Uchcha != Chesta, by as much as the full 60-point Shashtiamsa scale. Because
A emits nothing for Sun/Moon (Chesta Bala is not computed for the
luminaries), the `if p in m_ishta and p in m_kashta: ... else: ...` branch in
saravali_summary.py meant a SINGLE report could carry Kashta values from two
different formulas: Mars/Mercury/Jupiter/Venus/Saturn via A, Sun/Moon via B.

RESOLVED against the primary text. BPHS Chapter 28 ("Ishta and Kashta Bala"),
verse 6, R. Santhanam translation, p. 230:

    "...Half of the sum will represent the Ishta Phala (benefice tendency)
     of the planet. Reduce Ishta Phala from 60 to obtain the planet's
     Kashta Phala (or malefic tendency)."

Kashta is therefore the arithmetic complement of Ishta. Path B was changed to
match; path A was already correct. The `sqrt((60-U)*(60-C))` variant is
common in secondary literature and astrology software but contradicts BPHS.

What these tests cover:

  1. CHARACTERIZATION — lock each implementation's formula so accidental
     drift is caught immediately.
  2. CONSISTENCY — assert the two paths agree on Kashta for all inputs
     (formerly xfail(strict=True); now passing).
  3. REGRESSION GUARD — assert the rejected sqrt-complement variant is not
     reintroduced.

STILL OPEN (deliberately out of scope here, tracked separately):
  - The luminary SCOPE divergence: path A emits nothing for Sun/Moon; path B
    substitutes Ayana/Paksha Bala for their Chesta; BPHS Ch. 28 vv. 3-4
    specifies a third rule again (Sun's Cheshta Kendra = Sayana Sun + 3
    Rashis; Moon's = Moon - Sun). All three differ.
  - The ISHTA formula itself: both paths use sqrt(Uchcha Bala * Chesta Bala),
    whereas BPHS Ch. 28 v. 6 derives Ishta from Uchcha/Cheshta *Rasmis*
    (rays, 0-8 scale per v. 5), not from the Balas directly.
"""

from __future__ import annotations

import math

import pytest

from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.shadbala.ishta_kashta_bala import IshtaKashtaBalaCalculator
from apps.api.services.shadbala.saravali_summary import (
    CLASSICAL_SEVEN,
    SaravaliShadbalaEvaluator,
)

# The two Kashta formulas agree if and only if Uchcha == Chesta:
#   A: 60 - sqrt(U*C)          B: sqrt((60-U)*(60-C))
# With U == C == x both reduce to 60 - x. These cases are therefore NOT
# expected to fail and must not carry the xfail marker.
_AGREEING_CASES = [
    (30.0, 30.0),
    (10.0, 10.0),
    (0.0, 0.0),
]

# Inputs where the formulas genuinely diverge, up to the full 60-point scale.
_DIVERGING_CASES = [
    (40.0, 30.0),
    (55.0, 45.0),
    (50.0, 10.0),
    (59.0, 1.0),
    (60.0, 0.0),    # maximum divergence: A -> 60.0, B -> 0.0
    (0.0, 60.0),
]

_UCHCHA_CHESTA_CASES = _AGREEING_CASES + _DIVERGING_CASES


def _make_result(cid: str, name: str, planet: str, val: float) -> BalaComponentResult:
    return BalaComponentResult(
        component_id=cid,
        component_name=name,
        rule_version="1.0",
        planet=planet,
        value_shashtiamsas=val,
        trace=(),
    )


def _calculator_a(uchcha: float, chesta: float) -> tuple[float, float]:
    """Run the real IshtaKashtaBalaCalculator for a single planet."""
    ishta_results, kashta_results = IshtaKashtaBalaCalculator().calculate_all(
        [_make_result("SHADBALA-UCHCHA", "Uchcha Bala", "mars", uchcha)],
        [_make_result("SHADBALA-CHESTA", "Chesta Bala", "mars", chesta)],
    )
    return ishta_results[0].value_shashtiamsas, kashta_results[0].value_shashtiamsas


# Chesta Bala is not computed for the luminaries (see chesta_bala.py), which
# is precisely why Calculator A cannot cover them and they fall through to
# saravali_summary's inline fallback.
_LUMINARIES = ("sun", "moon")
_NON_LUMINARIES = tuple(p for p in CLASSICAL_SEVEN if p not in _LUMINARIES)


def _saravali_report(uchcha: float, chesta: float, *, with_calculator_a: bool):
    """
    Build a real SaravaliShadbalaReport.

    with_calculator_a=False forces the inline fallback branch (path B) for
    every planet by omitting the ishta/kashta arguments entirely.

    with_calculator_a=True mirrors PRODUCTION wiring: Calculator A is fed
    only the non-luminary Chesta results (as shadbala_engine does), so it
    emits values for 5 grahas and Sun/Moon fall through to path B.
    """
    planets = CLASSICAL_SEVEN
    zeros = lambda cid, name: [_make_result(cid, name, p, 0.0) for p in planets]  # noqa: E731

    uchcha_all = [_make_result("SHADBALA-UCHCHA", "Uchcha Bala", p, uchcha) for p in planets]
    chesta_all = [_make_result("SHADBALA-CHESTA", "Chesta Bala", p, chesta) for p in planets]

    kwargs = dict(
        naisargika=zeros("SHADBALA-NAISARGIKA", "Naisargika Bala"),
        dig=zeros("SHADBALA-DIG", "Dig Bala"),
        drik=zeros("SHADBALA-DRIK", "Drik Bala"),
        chesta=chesta_all,
        paksha=zeros("SHADBALA-PAKSHA", "Paksha Bala"),
        ayana=zeros("SHADBALA-AYANA", "Ayana Bala"),
        yuddha=zeros("SHADBALA-YUDDHA", "Yuddha Bala"),
        uchcha=uchcha_all,
        kendradi=zeros("SHADBALA-KENDRADI", "Kendradi Bala"),
        drekkana=zeros("SHADBALA-DREKKANA", "Drekkana Bala"),
        saptavargaja=zeros("SHADBALA-SAPTAVARGAJA", "Saptavargaja Bala"),
        ojayugmarasyamsa=zeros("SHADBALA-OJAYUGMA", "Ojayugmarasyamsa Bala"),
        tribhaga=zeros("SHADBALA-TRIBHAGA", "Tribhaga Bala"),
        nathonnata=zeros("SHADBALA-NATHONNATA", "Nathonnata Bala"),
        dina_hora=zeros("SHADBALA-DINAHORA", "Dina Hora Bala"),
    )

    if with_calculator_a:
        chesta_non_luminary = [r for r in chesta_all if r.planet not in _LUMINARIES]
        ishta, kashta = IshtaKashtaBalaCalculator().calculate_all(
            uchcha_all, chesta_non_luminary
        )
        kwargs["ishta"] = ishta
        kwargs["kashta"] = kashta

    return SaravaliShadbalaEvaluator.evaluate(**kwargs)


# ── 1. Characterization: Calculator A (ishta_kashta_bala.py) ────────────────

@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_calculator_a_ishta_is_geometric_mean(uchcha, chesta):
    """Locks: Ishta = sqrt(Uchcha * Chesta). Both implementations agree here."""
    ishta, _ = _calculator_a(uchcha, chesta)
    assert ishta == pytest.approx(math.sqrt(uchcha * chesta), abs=1e-4)


@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_calculator_a_kashta_is_sixty_minus_ishta(uchcha, chesta):
    """Locks path A's Kashta = 60 - Ishta. Takes no position on correctness."""
    ishta, kashta = _calculator_a(uchcha, chesta)
    assert kashta == pytest.approx(60.0 - ishta, abs=1e-4)


@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_calculator_a_complementarity_invariant(uchcha, chesta):
    """
    Path A guarantees Ishta + Kashta == 60 by construction. Any consumer
    relying on this (stacked bars, "% benefic" splits) breaks if the formula
    changes to path B, which does NOT preserve this invariant.
    """
    ishta, kashta = _calculator_a(uchcha, chesta)
    assert ishta + kashta == pytest.approx(60.0, abs=1e-4)


def test_calculator_a_scope_is_intersection_of_inputs():
    """
    Path A only emits values for planets present in BOTH Uchcha and Chesta
    inputs. Since Chesta Bala excludes Sun/Moon, so does Ishta/Kashta —
    this is what routes Sun/Moon into saravali_summary's fallback branch.
    """
    uchcha = [_make_result("SHADBALA-UCHCHA", "Uchcha Bala", p, 40.0)
              for p in ("sun", "moon", "mars", "mercury")]
    chesta = [_make_result("SHADBALA-CHESTA", "Chesta Bala", p, 30.0)
              for p in ("mars", "mercury")]

    ishta, kashta = IshtaKashtaBalaCalculator().calculate_all(uchcha, chesta)

    assert {r.planet for r in ishta} == {"mars", "mercury"}
    assert {r.planet for r in kashta} == {"mars", "mercury"}


# ── 2. Characterization: Path B (saravali_summary.py inline fallback) ───────

@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_saravali_fallback_kashta_is_sixty_minus_ishta(uchcha, chesta):
    """
    Locks path B's Kashta = 60 - Ishta, reached whenever ishta/kashta are
    not supplied to the evaluator.

    This replaced sqrt((60 - Uchcha) * (60 - Chesta)) once BPHS Ch. 28 v. 6
    was verified against the primary text (R. Santhanam translation, p. 230):
    "Reduce Ishta Phala from 60 to obtain the planet's Kashta Phala."
    """
    report = _saravali_report(uchcha, chesta, with_calculator_a=False)
    row = next(r for r in report.planets if r.planet == "mars")

    expected = 60.0 - math.sqrt(uchcha * chesta)
    assert row.kashta_bala_virupas == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_saravali_fallback_does_not_use_complement_geometric_mean(uchcha, chesta):
    """
    Regression guard against reintroducing the sqrt((60-U)*(60-C)) variant.

    Only checked on inputs where the two formulas actually differ — for
    Uchcha == Chesta both reduce to 60 - x and the assertion would be
    vacuous.
    """
    if uchcha == chesta:
        pytest.skip("formulas coincide when Uchcha == Chesta")

    report = _saravali_report(uchcha, chesta, with_calculator_a=False)
    row = next(r for r in report.planets if r.planet == "mars")

    rejected = math.sqrt((60.0 - uchcha) * (60.0 - chesta))
    assert row.kashta_bala_virupas != pytest.approx(rejected, abs=1e-4)


@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_both_paths_agree_on_ishta(uchcha, chesta):
    """Ishta is NOT in dispute — both paths compute the same geometric mean."""
    ishta_a, _ = _calculator_a(uchcha, chesta)
    report_b = _saravali_report(uchcha, chesta, with_calculator_a=False)
    ishta_b = next(r for r in report_b.planets if r.planet == "mars").ishta_bala_virupas

    assert ishta_a == pytest.approx(ishta_b, abs=1e-4)


# ── 3. THE BUG: the two paths disagree on Kashta ────────────────────────────

@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_both_paths_agree_on_kashta(uchcha, chesta):
    """
    THE FIX, LOCKED. Previously xfail(strict=True): the two implementations
    disagreed for every input where Uchcha != Chesta, up to the full
    60-point scale at (60, 0).

    saravali_summary.py now uses 60 - Ishta, matching ishta_kashta_bala.py
    and BPHS Ch. 28 v. 6. Parametrized over BOTH the agreeing and diverging
    case families — the distinction no longer matters, which is the point.
    """
    _, kashta_a = _calculator_a(uchcha, chesta)
    report_b = _saravali_report(uchcha, chesta, with_calculator_a=False)
    kashta_b = next(r for r in report_b.planets if r.planet == "mars").kashta_bala_virupas

    assert kashta_a == pytest.approx(kashta_b, abs=1e-4)


def test_previously_maximal_divergence_case_now_agrees():
    """
    (Uchcha=60, Chesta=0) was the worst case: path A gave 60.0, path B gave
    0.0 — the entire Shashtiamsa range. Both now yield 60.0.
    """
    _, kashta_a = _calculator_a(60.0, 0.0)
    report_b = _saravali_report(60.0, 0.0, with_calculator_a=False)
    kashta_b = next(r for r in report_b.planets if r.planet == "mars").kashta_bala_virupas

    assert kashta_a == pytest.approx(60.0, abs=1e-4)
    assert kashta_b == pytest.approx(60.0, abs=1e-4)


@pytest.mark.parametrize("uchcha,chesta", _UCHCHA_CHESTA_CASES)
def test_complementarity_invariant_now_holds_in_both_paths(uchcha, chesta):
    """
    Ishta + Kashta == 60 is now guaranteed by BOTH implementations. Under the
    old path-B formula this held only for path A, so any consumer relying on
    it (stacked bars, "% benefic" splits) was correct for the 5 non-luminaries
    and silently wrong for Sun/Moon.
    """
    report = _saravali_report(uchcha, chesta, with_calculator_a=False)
    row = next(r for r in report.planets if r.planet == "mars")

    assert row.ishta_bala_virupas + row.kashta_bala_virupas == pytest.approx(
        60.0, abs=1e-4
    )


def test_luminary_chesta_substitution_exists_only_in_path_b():
    """
    THIRD divergence, distinct from the Kashta-formula one.

    saravali_summary.py:241-246 applies a classical substitution for the
    luminaries — Sun's Chesta Bala := its Ayana Bala, Moon's := its Paksha
    Bala — so Sun/Moon DO receive Ishta/Kashta values there.

    Calculator A has no such rule: it emits nothing for Sun/Moon at all
    (intersection of Uchcha and Chesta inputs). So the two implementations
    disagree not only on the Kashta formula but on whether the luminaries
    have an Ishta/Kashta figure in the first place.
    """
    ishta, kashta = IshtaKashtaBalaCalculator().calculate_all(
        [_make_result("SHADBALA-UCHCHA", "Uchcha Bala", p, 50.0) for p in CLASSICAL_SEVEN],
        [_make_result("SHADBALA-CHESTA", "Chesta Bala", p, 10.0) for p in _NON_LUMINARIES],
    )
    assert {r.planet for r in ishta}.isdisjoint(_LUMINARIES)
    assert {r.planet for r in kashta}.isdisjoint(_LUMINARIES)

    report = _saravali_report(50.0, 10.0, with_calculator_a=True)
    rows = {r.planet: r for r in report.planets}
    for luminary in _LUMINARIES:
        assert luminary in rows
        assert rows[luminary].kashta_bala_virupas is not None


def test_single_report_uses_one_kashta_formula_for_all_planets():
    """
    THE FIXED SYMPTOM. With Calculator A supplied (the real production wiring
    via shadbala_engine.compute_ishta_kashta_bala), Sun/Moon still take the
    fallback branch while the 5 non-luminaries take path A — but both branches
    now compute Kashta the same way, so one report column is internally
    consistent. Previously the luminaries' values came from a different
    formula than everyone else's.

    Ayana/Paksha are set explicitly because path B substitutes them for the
    luminaries' Chesta Bala (see test_luminary_chesta_substitution_exists_
    only_in_path_b); leaving them at zero would give the luminaries a
    different effective Chesta and mask the comparison.

    NOTE: the luminary SCOPE divergence (path A emits nothing for Sun/Moon;
    path B substitutes Ayana/Paksha, while BPHS Ch. 28 vv. 3-4 defines a
    third rule) is a SEPARATE open issue, deliberately not addressed here.
    """
    uchcha, chesta = 50.0, 10.0
    planets = CLASSICAL_SEVEN

    def _all(cid, name, val):
        return [_make_result(cid, name, p, val) for p in planets]

    uchcha_all = _all("SHADBALA-UCHCHA", "Uchcha Bala", uchcha)
    chesta_all = _all("SHADBALA-CHESTA", "Chesta Bala", chesta)
    # Make the luminary substitution yield the same effective Chesta value.
    ayana_all = _all("SHADBALA-AYANA", "Ayana Bala", chesta)
    paksha_all = _all("SHADBALA-PAKSHA", "Paksha Bala", chesta)
    zeros = lambda cid, name: _all(cid, name, 0.0)  # noqa: E731

    ishta, kashta = IshtaKashtaBalaCalculator().calculate_all(
        uchcha_all, [r for r in chesta_all if r.planet not in _LUMINARIES]
    )

    report = SaravaliShadbalaEvaluator.evaluate(
        naisargika=zeros("SHADBALA-NAISARGIKA", "Naisargika Bala"),
        dig=zeros("SHADBALA-DIG", "Dig Bala"),
        drik=zeros("SHADBALA-DRIK", "Drik Bala"),
        chesta=chesta_all,
        paksha=paksha_all,
        ayana=ayana_all,
        yuddha=zeros("SHADBALA-YUDDHA", "Yuddha Bala"),
        uchcha=uchcha_all,
        kendradi=zeros("SHADBALA-KENDRADI", "Kendradi Bala"),
        drekkana=zeros("SHADBALA-DREKKANA", "Drekkana Bala"),
        saptavargaja=zeros("SHADBALA-SAPTAVARGAJA", "Saptavargaja Bala"),
        ojayugmarasyamsa=zeros("SHADBALA-OJAYUGMA", "Ojayugmarasyamsa Bala"),
        tribhaga=zeros("SHADBALA-TRIBHAGA", "Tribhaga Bala"),
        nathonnata=zeros("SHADBALA-NATHONNATA", "Nathonnata Bala"),
        dina_hora=zeros("SHADBALA-DINAHORA", "Dina Hora Bala"),
        ishta=ishta,
        kashta=kashta,
    )

    rows = {r.planet: r for r in report.planets}
    expected_kashta = 60.0 - math.sqrt(uchcha * chesta)          # 37.6393
    rejected_kashta = math.sqrt((60.0 - uchcha) * (60.0 - chesta))  # 22.3607

    # Sanity: for this input the old and new formulas differ, so the
    # assertions below are not vacuous.
    assert abs(expected_kashta - rejected_kashta) > 1.0

    for planet in CLASSICAL_SEVEN:
        assert rows[planet].kashta_bala_virupas == pytest.approx(
            expected_kashta, abs=1e-4
        ), f"{planet} should use Kashta = 60 - Ishta regardless of branch"
