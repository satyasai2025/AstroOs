"""
AstroOS — Premium domain analysis report data.

Builds the two-part structure the report tier spec defines for every premium
domain report:

    PART 1 — THE PROMISE   relevant houses, significators, classical rules,
                           supporting and contradicting factors, evidence,
                           a promise verdict
    PART 2 — THE TIMING    Vimshottari mahadasa/antardasa windows relevant to
                           the domain, with the evidence behind each

HARD RULE, straight from the spec:

    "Never produce a timing prediction without a canonical calculation/rule/
     evidence basis."

So this module authors NO interpretation. Every statement it emits is one of:
  · a chart fact from a canonical engine (house, sign, dignity, dasha dates),
  · a classical rule evaluated by ClassicalRuleEvidenceEngine, carrying its
    own citation and SATISFIED / NOT_PRESENT status,
  · an explicit statement that something could not be established.

Where the evidence is thin the report says so. It does not fill the gap with
prose. A verdict of INSUFFICIENT_EVIDENCE is a valid, honest outcome and is
returned rather than being smoothed into a confident-sounding reading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Sequence

from apps.api.services.classical_rule_evidence_engine import (
    ClassicalRuleEvidenceEngine,
)
from apps.api.services.dasha_engine import DashaEngine


@dataclass(frozen=True)
class DomainSpec:
    """
    Which parts of a chart a domain is read from.

    Houses and karakas here are standard textbook significations, not
    interpretation — they define WHERE to look, and the classical rule engine
    supplies WHAT the chart actually shows there.
    """

    key: str
    title: str
    primary_houses: tuple[int, ...]
    supporting_houses: tuple[int, ...]
    karakas: tuple[str, ...]
    dasha_lords_of_interest: tuple[str, ...]
    note: str = ""


DOMAIN_SPECS: dict[str, DomainSpec] = {
    "MARRIAGE_ANALYSIS": DomainSpec(
        key="marriage",
        title="Marriage Analysis",
        primary_houses=(7,),
        supporting_houses=(2, 11, 12),
        karakas=("Venus", "Jupiter"),
        dasha_lords_of_interest=("Venus", "Jupiter", "Moon"),
        note=(
            "The 7th house is the primary seat of marriage; the 2nd (family), "
            "11th (fulfilment) and 12th (bed pleasures) are read in support. "
            "Venus is the natural karaka for a spouse, Jupiter for a husband "
            "in a woman's chart."
        ),
    ),
    "CAREER_ANALYSIS": DomainSpec(
        key="career",
        title="Career Analysis",
        primary_houses=(10,),
        supporting_houses=(1, 2, 6, 11),
        karakas=("Sun", "Saturn", "Mercury"),
        dasha_lords_of_interest=("Sun", "Saturn", "Mercury", "Jupiter"),
        note=(
            "The 10th house governs action and standing in the world; the "
            "1st (self), 2nd (earnings), 6th (service) and 11th (gains) are "
            "read in support."
        ),
    ),
    "DASHA_ANALYSIS": DomainSpec(
        key="dasha",
        title="Dasha Analysis",
        primary_houses=(),
        supporting_houses=(),
        karakas=(),
        dasha_lords_of_interest=(),
        note=(
            "A period-by-period reading of the Vimshottari sequence. Every "
            "window below comes from the canonical dasha engine."
        ),
    ),
}


@dataclass
class PromiseFactor:
    """One supporting or contradicting factor, always with its source."""

    label: str
    detail: str
    source: str
    is_supporting: bool


@dataclass
class DomainPromise:
    houses: list[dict[str, Any]] = field(default_factory=list)
    karakas: list[dict[str, Any]] = field(default_factory=list)
    rules: list[dict[str, Any]] = field(default_factory=list)
    supporting: list[PromiseFactor] = field(default_factory=list)
    contradicting: list[PromiseFactor] = field(default_factory=list)
    verdict: str = "INSUFFICIENT_EVIDENCE"
    verdict_basis: str = ""


class DomainAnalysisBuilder:
    """Assembles Promise and Timing for one premium domain report."""

    def __init__(self, wrapper: Any) -> None:
        self._wrapper = wrapper
        self._dasha = DashaEngine(wrapper)
        self._evidence = ClassicalRuleEvidenceEngine()

    # ── Part 1 — Promise ─────────────────────────────────────────────────

    def build_promise(self, *, spec: DomainSpec, chart: Any,
                      report_data: dict[str, Any]) -> DomainPromise:
        promise = DomainPromise()
        planets = report_data.get("planets", [])
        by_house: dict[int, list[dict[str, Any]]] = {}
        for p in planets:
            by_house.setdefault(p.get("house"), []).append(p)

        for house in spec.primary_houses + spec.supporting_houses:
            occupants = by_house.get(house, [])
            promise.houses.append({
                "house": house,
                "role": "primary" if house in spec.primary_houses else "supporting",
                "occupants": [
                    {"name": o["name"], "sign": o.get("rashi_name"),
                     "dignity": o.get("dignity")}
                    for o in occupants
                ],
                "is_empty": not occupants,
            })

        for karaka in spec.karakas:
            row = next((p for p in planets if p.get("name") == karaka), None)
            if row is None:
                continue
            promise.karakas.append({
                "name": karaka,
                "sign": row.get("rashi_name"),
                "house": row.get("house"),
                "dignity": row.get("dignity"),
                "nakshatra": row.get("nakshatra"),
                "retrograde": row.get("retro_symbol") not in ("—", "", None),
            })
            dignity = (row.get("dignity") or "").lower()
            if dignity in ("exalted", "moolatrikona", "own"):
                promise.supporting.append(PromiseFactor(
                    label=f"{karaka} in {row.get('dignity')}",
                    detail=f"{karaka} occupies {row.get('rashi_name')} in house "
                           f"{row.get('house')}.",
                    source="Canonical dignity computation",
                    is_supporting=True,
                ))
            elif dignity in ("debilitated", "enemy"):
                promise.contradicting.append(PromiseFactor(
                    label=f"{karaka} in {row.get('dignity')}",
                    detail=f"{karaka} occupies {row.get('rashi_name')} in house "
                           f"{row.get('house')}.",
                    source="Canonical dignity computation",
                    is_supporting=False,
                ))

        # Classical rules — evaluated, cited, never authored.
        for chain in self._evidence.evaluate_chart_evidence(chart):
            citation = getattr(chain, "citation", None)
            status = str(getattr(chain, "status", "")).split(".")[-1]
            promise.rules.append({
                "rule_id": chain.rule_id,
                "rule_name": chain.rule_name,
                "category": chain.category,
                "status": status,
                "score": getattr(chain, "strength_score", 0.0),
                "description": chain.brief_description,
                "citation": self._format_citation(citation),
                "is_present": status == "SATISFIED",
            })

        present = [r for r in promise.rules if r["is_present"]]
        promise.verdict, promise.verdict_basis = self._verdict(
            promise, present, spec
        )
        return promise

    @staticmethod
    def _format_citation(citation: Any) -> str:
        if citation is None:
            return "—"
        book = getattr(citation, "book_title", "")
        author = getattr(citation, "author", "")
        chapter = getattr(citation, "chapter", "")
        sloka = getattr(citation, "sloka_range", "")
        bits = [b for b in (book, f"ch. {chapter}" if chapter else "",
                            sloka, f"({author})" if author else "") if b]
        return " · ".join(bits) or "—"

    @staticmethod
    def _verdict(promise: DomainPromise, present: Sequence[dict[str, Any]],
                 spec: DomainSpec) -> tuple[str, str]:
        """
        Deliberately conservative. A domain verdict is only raised above
        INSUFFICIENT_EVIDENCE when the chart actually supplies something to
        stand on, and the basis string always names what that was.
        """
        if not spec.primary_houses and not spec.karakas:
            # A domain with no house or karaka surface (Dasha Analysis) has no
            # promise to judge — it is a timing document. Emitting SUPPORTED
            # here would attach a verdict to a question the report never asked,
            # justified by rules that are not specific to the domain.
            return ("NOT_APPLICABLE",
                    "This report reads periods rather than a promise, so no "
                    "promise verdict is issued. See Part 2 for the timing.")

        occupied_primary = [
            h for h in promise.houses
            if h["role"] == "primary" and not h["is_empty"]
        ]
        signals = len(present) + len(promise.supporting)

        if not present and not promise.supporting and not promise.contradicting:
            return ("INSUFFICIENT_EVIDENCE",
                    "No classical rule in the registry fired for this chart and "
                    "no karaka dignity signal was found. AstroOS does not issue "
                    "a verdict on this basis.")
        if promise.contradicting and not signals:
            return ("CONTRADICTED",
                    f"{len(promise.contradicting)} contradicting factor(s) and no "
                    "supporting rule or dignity signal.")
        if signals and not promise.contradicting:
            return ("SUPPORTED",
                    f"{len(present)} classical rule(s) satisfied and "
                    f"{len(promise.supporting)} supporting dignity signal(s); "
                    f"{len(occupied_primary)} primary house(s) occupied.")
        return ("MIXED",
                f"{signals} supporting signal(s) against "
                f"{len(promise.contradicting)} contradicting factor(s) — "
                "the chart does not point one way.")

    # ── Part 2 — Timing ──────────────────────────────────────────────────

    def build_timing(self, *, spec: DomainSpec, birth_datetime_utc: datetime,
                     latitude: float, longitude: float,
                     ayanamsa: str = "lahiri") -> dict[str, Any]:
        """
        Vimshottari windows relevant to the domain, from the canonical engine.

        A "relevant" window is one whose mahadasa or antardasa lord is a karaka
        for this domain. That is a selection rule over canonical output, not a
        prediction: the report states which periods involve the domain's
        significators and leaves it there.
        """
        tree = self._dasha.compute_vimshottari(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            max_depth=2,
        )
        today = date.today()
        interest = {l.lower() for l in spec.dasha_lords_of_interest}

        windows: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        for md in tree.mahadashas:
            md_relevant = (not interest) or md.lord.lower() in interest
            for ad in md.sub_periods:
                is_now = ad.start_date <= today <= ad.end_date
                ad_relevant = (not interest) or ad.lord.lower() in interest
                if not (md_relevant or ad_relevant):
                    continue
                # Kept terse on purpose: this string is one narrow table cell
                # per row. Spelling out "<Lord> mahadasa is a <domain>
                # significator" wrapped every row onto two lines and pushed
                # the sheet past its page box. Which significator it is, and
                # what the selection rule means, are stated once in the
                # section heading and the Method paragraph.
                reasons = []
                if md.lord.lower() in interest:
                    reasons.append("Mahadasa lord")
                if ad.lord.lower() in interest:
                    reasons.append("Antardasa lord")
                entry = {
                    "mahadasa": md.lord.capitalize(),
                    "antardasa": ad.lord.capitalize(),
                    "start": ad.start_date.strftime("%d %b %Y"),
                    "end": ad.end_date.strftime("%d %b %Y"),
                    "is_current": is_now,
                    "is_future": ad.start_date > today,
                    "basis": " + ".join(reasons) or "Full sequence listed",
                }
                windows.append(entry)
                if is_now:
                    current = entry

        return {
            "windows": windows,
            "current_window": current,
            "total_windows": len(windows),
            "significators": list(spec.dasha_lords_of_interest),
            "method": (
                "Vimshottari mahadasa/antardasa from the canonical dasha "
                "engine. Windows are selected where a domain significator "
                "rules the period; no transit or event prediction is asserted."
            ),
            "limitations": (
                "Transit triggers and dasha-transit intersection are NOT "
                "included: AstroOS has no canonical engine wiring them to this "
                "report yet. Listing a window here states that a significator "
                "governs the period — not that an event will occur in it."
            ),
        }
