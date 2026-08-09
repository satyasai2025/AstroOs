"""
AstroOS — Jaimini Internal Consistency Validation (Layer 6: Calculation Engine)

Stateless validators that check an already-computed Jaimini result for
internal consistency — catching a bug in an engine (or a future change
to one) rather than validating astrological "correctness" (not a
computable property). These are structural/logical invariants that MUST
hold if the computation is implemented correctly.

Not wired into any engine's compute() automatically — callers (tests,
routers, other engines) call these explicitly. Every check raises a
JaiminiValidationError subclass carrying a machine-readable `rule` slug
and `details` dict, rather than returning a bool, so a failure is loud
and traceable rather than silently producing a wrong answer downstream.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.jaimini import ArudhaResult, CharaKarakaResult
from apps.api.services.jaimini_shared import RASHI_LIST, rashi_at, rashi_index, signs_from


class JaiminiValidationError(ValueError):
    """Base class for all Jaimini internal-consistency validation failures."""

    def __init__(self, message: str, *, rule: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.rule = rule
        self.details = details or {}


class CharaKarakaValidationError(JaiminiValidationError):
    pass


class ArudhaValidationError(JaiminiValidationError):
    pass


class DashaValidationError(JaiminiValidationError):
    pass


class SignIndexingError(JaiminiValidationError):
    pass


def validate_sign_indexing() -> None:
    """
    Self-consistency check of jaimini_shared's rashi arithmetic itself:
    every sign must round-trip through rashi_index -> rashi_at, and
    signs_from(r, 12) must return to r (one full zodiac revolution).
    """
    for i, rashi in enumerate(RASHI_LIST):
        if rashi_index(rashi) != i:
            raise SignIndexingError(
                f"rashi_index({rashi!r}) returned {rashi_index(rashi)}, expected {i}.",
                rule="sign_indexing.round_trip",
                details={"rashi": rashi, "expected_index": i},
            )
        if rashi_at(i) != rashi:
            raise SignIndexingError(
                f"rashi_at({i}) returned {rashi_at(i)!r}, expected {rashi!r}.",
                rule="sign_indexing.round_trip",
                details={"index": i, "expected_rashi": rashi},
            )
        if signs_from(rashi, 12) != rashi:
            raise SignIndexingError(
                f"signs_from({rashi!r}, 12) did not return to {rashi!r} after a full revolution.",
                rule="sign_indexing.full_revolution",
                details={"rashi": rashi},
            )


def validate_chara_karaka_result(result: CharaKarakaResult) -> None:
    """
    Enforces: exactly 7 (sapta) or 8 (ashta) distinct karakas, no
    duplicate planets, no duplicate karaka names, and rank/position
    internally aligned.
    """
    expected_count = 7 if result.scheme == "sapta_karaka" else 8
    if len(result.karakas) != expected_count:
        raise CharaKarakaValidationError(
            f"{result.scheme} must have exactly {expected_count} karakas, got {len(result.karakas)}.",
            rule="chara_karaka.count",
            details={"scheme": result.scheme, "actual_count": len(result.karakas)},
        )

    planets = [k.planet for k in result.karakas]
    if len(set(planets)) != len(planets):
        raise CharaKarakaValidationError(
            "Duplicate planet(s) found among Chara Karakas.",
            rule="chara_karaka.duplicate_planet",
            details={"planets": planets},
        )

    names = [k.karaka_name for k in result.karakas]
    if len(set(names)) != len(names):
        raise CharaKarakaValidationError(
            "Duplicate karaka name(s) found among Chara Karakas.",
            rule="chara_karaka.duplicate_name",
            details={"names": names},
        )

    for i, karaka in enumerate(result.karakas):
        if karaka.rank != i + 1:
            raise CharaKarakaValidationError(
                f"Karaka at position {i} has rank={karaka.rank}, expected {i + 1}.",
                rule="chara_karaka.rank_sequence",
                details={"position": i, "actual_rank": karaka.rank},
            )


def validate_arudha_result(result: ArudhaResult) -> None:
    """
    Enforces: exactly 12 padas covering houses 1-12 with no gaps or
    repeats, and the same/7th-from-itself exception invariant —
    whenever exception_applied is True, the final rashi must be exactly
    raw_rashi shifted by +9 signs; whenever it's False, final rashi must
    equal raw_rashi unchanged. This is the precise, checkable form of
    "no impossible Arudha positions": a Pada can never end up landing on
    its own house's sign or that sign's 7th (see arudha_engine.py's
    docstring for why a single +9 shift always clears both).
    """
    houses = [p.house_number for p in result.padas]
    if sorted(houses) != list(range(1, 13)):
        raise ArudhaValidationError(
            "Arudha result must contain exactly one entry for each house 1-12.",
            rule="arudha.house_coverage",
            details={"houses": houses},
        )

    for pada in result.padas:
        if pada.exception_applied:
            expected = signs_from(pada.raw_rashi, 9)
            if pada.rashi != expected:
                raise ArudhaValidationError(
                    f"{pada.pada_name}: exception_applied=True but rashi={pada.rashi!r} "
                    f"!= raw_rashi+9={expected!r}.",
                    rule="arudha.exception_shift",
                    details={"pada_name": pada.pada_name, "rashi": pada.rashi, "expected": expected},
                )
        elif pada.rashi != pada.raw_rashi:
            raise ArudhaValidationError(
                f"{pada.pada_name}: exception_applied=False but rashi ({pada.rashi!r}) != "
                f"raw_rashi ({pada.raw_rashi!r}).",
                rule="arudha.exception_shift",
                details={"pada_name": pada.pada_name, "rashi": pada.rashi, "raw_rashi": pada.raw_rashi},
            )


def validate_dasha_tree(tree: DashaTree) -> None:
    """
    Structural validation of an ALREADY-COMPUTED DashaTree (e.g. from
    dasha_engine.py's existing compute_chara/compute_narayana) —
    chronological continuity with no gaps/overlaps between consecutive
    mahadashas, and every period's duration_days matching its own
    start/end dates. Does not recompute or second-guess the dasha
    calculation itself, only its structural shape.

    Validate the DashaTree BEFORE it goes through jaimini_dasha_adapter
    (i.e. call this on DashaEngine.compute_chara/compute_narayana's
    direct return value) — the adapter is a pure field-renaming reshape
    with no computation of its own, so a tree that validates here is
    still valid after adaptation; there is no separate validator for
    JaiminiDashaResult on purpose.
    """
    mahadashas = tree.mahadashas
    if not mahadashas:
        raise DashaValidationError(
            "DashaTree has no mahadashas.", rule="dasha.empty", details={"system": tree.system}
        )

    for period in mahadashas:
        actual_days = (period.end_date - period.start_date).days
        if actual_days != period.duration_days:
            raise DashaValidationError(
                f"{tree.system} mahadasha {period.lord!r}: duration_days={period.duration_days} "
                f"but start/end dates span {actual_days} days.",
                rule="dasha.duration_mismatch",
                details={
                    "lord": period.lord,
                    "duration_days": period.duration_days,
                    "actual_days": actual_days,
                },
            )

    for prev, cur in zip(mahadashas, mahadashas[1:]):
        if cur.start_date != prev.end_date:
            raise DashaValidationError(
                f"{tree.system}: gap or overlap between {prev.lord!r} (ends {prev.end_date}) "
                f"and {cur.lord!r} (starts {cur.start_date}).",
                rule="dasha.sequence_continuity",
                details={"prev_lord": prev.lord, "cur_lord": cur.lord},
            )
