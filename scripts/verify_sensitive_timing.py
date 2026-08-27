"""
Strict verification of the sensitive-timing stack against real data.

Three passes, run in order because each depends on the one before:

1. **Ephemeris → nakshatra** for all five GC-MASTER celebrity charts,
   compared against that dataset's own verified ``expected_planets``.
   Everything downstream (Janma Nakshatra, Tara, Latta, SBC) is keyed
   off nakshatra, so if this pass fails nothing after it means anything.
2. **Technique invariants** — Latta offsets, Tara cycle boundaries, and
   the convergence rule that distinguishes techniques from hits.
3. **Real-life backtest** — timelines for each celebrity against their
   documented public life events, scored by the retrodiction validation
   engine, reporting coverage-adjusted lift rather than raw recall.

Run: python scripts/verify_sensitive_timing.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.services.ephemeris_wrapper import datetime_to_jd, longitude_to_nakshatra
from apps.api.services.latta_engine import LattaEngine
from apps.api.services.retrodiction_validation_engine import RetrodictionValidationEngine
from apps.api.services.sbc_report_service import SBCReportService
from apps.api.services.sensitive_narrative import render_window
from apps.api.services.sensitive_timeline_service import SensitiveTimelineService
from packages.shared.disclosed_events import (
    SANGYA_DOMAINS,
    DisclosedEvent,
    EventValence,
    LifeDomain,
)
from packages.shared.enums import Nakshatra
from packages.shared.latta import LATTA_RULES, latta_target
from packages.shared.sensitive_convergence import ConvergenceGrade, Indicator, Technique, grade_convergence
from packages.shared.tarabala import current_age_year, solar_return_boundary, yearly_tara
from packages.shared.temporal_stance import SubjectStatus

GC_MASTER = Path(__file__).resolve().parents[1] / "datasets/gc-master/GC-MASTER-v1.0.0.json"
ALL_27 = [n.value for n in Nakshatra]


def _wrapper():
    from apps.api.main import _make_ephemeris_wrapper

    return _make_ephemeris_wrapper()


# ── Documented public life events ─────────────────────────────────────────────
#
# Public record only, and only for figures whose lives are extensively
# documented. Dates are the widely-reported ones; where a source gives a month
# rather than a day, the event is entered as a month-long range instead of
# being sharpened to a false point. Four of the five subjects are deceased, so
# they run in research/backtesting mode; Obama is living and runs in the normal
# living-subject mode, which blocks the longevity family of formulas outright.


@dataclass
class Subject:
    chart_id: str
    name: str
    status: SubjectStatus
    events: list[DisclosedEvent]


def _ev(eid, domain, start, end=None, desc="", sig=4, valence=EventValence.DIFFICULT):
    return DisclosedEvent(
        event_id=eid,
        domain=domain,
        occurred_start_utc=datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
        occurred_end_utc=(
            datetime.fromisoformat(end).replace(tzinfo=timezone.utc) if end else None
        ),
        description=desc,
        significance=sig,
        valence=valence,
        recorded_via="public record",
    )


SUBJECTS: dict[str, Subject] = {
    "GC-REF-001": Subject(
        "GC-REF-001", "Queen Elizabeth II", SubjectStatus.DECEASED_HISTORICAL,
        [
            _ev("e2-accession", LifeDomain.CAREER, "1952-02-06", desc="accession to the throne",
                sig=5, valence=EventValence.MIXED),
            _ev("e2-annus", LifeDomain.FAMILY, "1992-01-01", "1992-12-31",
                desc="the year she publicly called 'annus horribilis'", sig=5),
            _ev("e2-diana", LifeDomain.FAMILY, "1997-08-31", desc="death of Diana and the public crisis that followed", sig=5),
            _ev("e2-philip", LifeDomain.FAMILY, "2021-04-09", desc="death of Prince Philip", sig=5),
            _ev("e2-death", LifeDomain.HEALTH, "2022-09-08", desc="her own death", sig=5),
        ],
    ),
    "GC-REF-002": Subject(
        "GC-REF-002", "Barack Obama", SubjectStatus.LIVING,
        [
            _ev("bo-senate", LifeDomain.CAREER, "2005-01-04", desc="sworn in as US Senator",
                sig=4, valence=EventValence.SUPPORTIVE),
            _ev("bo-elected", LifeDomain.CAREER, "2008-11-04", desc="elected President",
                sig=5, valence=EventValence.SUPPORTIVE),
            _ev("bo-mother", LifeDomain.FAMILY, "1995-11-07", desc="death of his mother", sig=5),
            _ev("bo-leaves", LifeDomain.CAREER, "2017-01-20", desc="left office",
                sig=4, valence=EventValence.MIXED),
        ],
    ),
    "GC-REF-003": Subject(
        "GC-REF-003", "Diana, Princess of Wales", SubjectStatus.DECEASED_HISTORICAL,
        [
            _ev("di-wedding", LifeDomain.RELATIONSHIP, "1981-07-29", desc="marriage",
                sig=5, valence=EventValence.SUPPORTIVE),
            _ev("di-separation", LifeDomain.RELATIONSHIP, "1992-12-09", desc="formal separation", sig=5),
            _ev("di-divorce", LifeDomain.RELATIONSHIP, "1996-08-28", desc="divorce finalised", sig=5),
            _ev("di-death", LifeDomain.HEALTH, "1997-08-31", desc="her own death", sig=5),
        ],
    ),
    "GC-REF-004": Subject(
        "GC-REF-004", "Nelson Mandela", SubjectStatus.DECEASED_HISTORICAL,
        [
            _ev("nm-arrest", LifeDomain.LEGAL, "1962-08-05", desc="arrest", sig=5),
            _ev("nm-rivonia", LifeDomain.LEGAL, "1964-06-12", desc="life sentence at the Rivonia Trial", sig=5),
            _ev("nm-release", LifeDomain.LEGAL, "1990-02-11", desc="release from prison",
                sig=5, valence=EventValence.SUPPORTIVE),
            _ev("nm-president", LifeDomain.CAREER, "1994-05-10", desc="inaugurated President",
                sig=5, valence=EventValence.SUPPORTIVE),
            _ev("nm-death", LifeDomain.HEALTH, "2013-12-05", desc="his own death", sig=5),
        ],
    ),
    "GC-REF-005": Subject(
        "GC-REF-005", "Steve Jobs", SubjectStatus.DECEASED_HISTORICAL,
        [
            _ev("sj-ousted", LifeDomain.CAREER, "1985-09-17", desc="forced out of Apple", sig=5),
            _ev("sj-return", LifeDomain.CAREER, "1997-07-09", desc="return to lead Apple",
                sig=5, valence=EventValence.SUPPORTIVE),
            _ev("sj-illness", LifeDomain.HEALTH, "2003-10-01", "2003-10-31",
                desc="diagnosis of serious illness", sig=5),
            _ev("sj-leave", LifeDomain.HEALTH, "2009-01-14", desc="medical leave of absence", sig=4),
            _ev("sj-death", LifeDomain.HEALTH, "2011-10-05", desc="his own death", sig=5),
        ],
    ),
}


# ── Pass 1: ephemeris → nakshatra ─────────────────────────────────────────────


def pass_1_ephemeris(refs) -> bool:
    print("\n" + "=" * 78)
    print("PASS 1 — Ephemeris → nakshatra vs GC-MASTER verified expectations")
    print("=" * 78)

    wrapper = _wrapper()
    total = matched = 0
    failures: list[str] = []

    for ref in refs:
        bd = ref["birth_data"]
        moment = datetime.fromisoformat(f"{bd['date']}T{bd['time_utc']}").replace(tzinfo=timezone.utc)
        jd = datetime_to_jd(moment)
        ayanamsa = wrapper.get_ayanamsa(jd)

        per_chart_ok = 0
        per_chart_total = 0
        for planet, expected in ref["expected_planets"].items():
            if "nakshatra" not in expected:
                continue
            tropical = wrapper.get_planet_position(planet, jd)
            sidereal = wrapper.to_sidereal(tropical.longitude, ayanamsa)
            computed = longitude_to_nakshatra(sidereal)

            per_chart_total += 1
            total += 1
            if computed.nakshatra == expected["nakshatra"]:
                per_chart_ok += 1
                matched += 1
            else:
                failures.append(
                    f"  {ref['chart_id']} {planet}: computed {computed.nakshatra} "
                    f"({sidereal:.4f}°) vs expected {expected['nakshatra']} "
                    f"({expected['longitude']:.4f}°)"
                )

        flag = "OK " if per_chart_ok == per_chart_total else "FAIL"
        print(f"  [{flag}] {ref['person_name']:<28} {per_chart_ok}/{per_chart_total} nakshatras match")

    print(f"\n  TOTAL: {matched}/{total} planetary nakshatras match the verified dataset")
    for line in failures:
        print(line)
    return matched == total


# ── Pass 2: technique invariants ──────────────────────────────────────────────


def pass_2_invariants() -> bool:
    print("\n" + "=" * 78)
    print("PASS 2 — Technique invariants")
    print("=" * 78)
    ok = True

    # Latta: each planet's fixed offset must be a bijection on the 27-circle.
    for planet in LATTA_RULES:
        targets = {latta_target(planet, n) for n in ALL_27}
        good = len(targets) == 27
        ok &= good
        print(f"  [{'OK ' if good else 'FAIL'}] Latta {planet:<8} strikes {len(targets)}/27 distinct stars")

    # Worked example: Sun's 12th-star Latta, inclusive count.
    got = latta_target("sun", "ashwini")
    good = got == "uttara_phalguni"
    ok &= good
    print(f"  [{'OK ' if good else 'FAIL'}] Sun in ashwini kicks the 12th star inclusively -> {got}")

    # Convergence: many hits from one technique must stay SINGLE.
    same = [Indicator(Technique.SBC_VEDHA, f"s{i}", frozenset()) for i in range(5)]
    good = grade_convergence(same) is ConvergenceGrade.SINGLE
    ok &= good
    print(f"  [{'OK ' if good else 'FAIL'}] 5 hits from one technique grade as {grade_convergence(same).value}")

    mixed = [
        Indicator(Technique.SBC_VEDHA, "a", frozenset()),
        Indicator(Technique.LATTA, "b", frozenset()),
        Indicator(Technique.YEARLY_TARA, "c", frozenset()),
    ]
    good = grade_convergence(mixed) is ConvergenceGrade.CONVERGING
    ok &= good
    print(f"  [{'OK ' if good else 'FAIL'}] 3 distinct techniques grade as {grade_convergence(mixed).value}")

    # Tara year boundaries must be exact solar-return anniversaries.
    birth = datetime(1961, 8, 5, 5, 24, tzinfo=timezone.utc)
    b1 = solar_return_boundary(birth, 1)
    just_before = current_age_year(birth, b1.replace(year=b1.year))
    age_at_birth = current_age_year(birth, birth)
    good = age_at_birth == 1
    ok &= good
    print(f"  [{'OK ' if good else 'FAIL'}] Age-year at the birth moment itself = {age_at_birth} (expected 1)")

    age, position, name = yearly_tara("rohini", birth, datetime(1990, 1, 1, tzinfo=timezone.utc))
    good = 1 <= position <= 27
    ok &= good
    print(f"  [{'OK ' if good else 'FAIL'}] Yearly Tara at 1990-01-01: age {age}, position {position} ({name})")

    return bool(ok)


# ── Pass 3: real-life backtest ────────────────────────────────────────────────


def pass_3_backtest(refs) -> None:
    print("\n" + "=" * 78)
    print("PASS 3 — Real-life backtest against documented public events")
    print("=" * 78)

    wrapper = _wrapper()
    service = SensitiveTimelineService(SBCReportService(wrapper), LattaEngine(wrapper))
    validator = RetrodictionValidationEngine()
    now = datetime(2026, 8, 27, tzinfo=timezone.utc)

    rows = []
    for ref in refs:
        subject = SUBJECTS[ref["chart_id"]]
        bd = ref["birth_data"]
        birth = datetime.fromisoformat(f"{bd['date']}T{bd['time_utc']}").replace(tzinfo=timezone.utc)
        janma = ref["expected_planets"]["moon"]["nakshatra"]

        first = min(e.start_utc for e in subject.events)
        last = max(e.end_utc for e in subject.events)
        start = first.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = last.replace(year=last.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        timeline = service.build_timeline(
            janma_nakshatra=janma,
            birth_datetime_utc=birth,
            start_utc=start,
            end_utc=end,
            step_days=15,
            now_utc=now,
            disclosed_events=subject.events,
            subject_status=subject.status,
            min_grade=ConvergenceGrade.CONVERGING,
        )
        report = validator.validate(timeline, events=subject.events)
        m = report.metrics

        print(f"\n  {subject.name}  (Janma Nakshatra: {janma}, {subject.status.value})")
        print(f"    scanned {start:%Y}-{end:%Y}, {len(timeline.all_windows)} windows, step 15d")
        print(f"    events {m.total_events} | hits {m.hits} | wrong-domain {m.overlapped_wrong_domain} | misses {m.misses}")
        print(f"    coverage {m.coverage:.1%} | recall {_fmt(m.recall)} | LIFT {_fmt(m.lift)}"
              f" -> better than chance: {m.is_better_than_chance}")
        for outcome in report.outcomes:
            mark = "HIT " if outcome.is_hit else ("~DOM" if outcome.overlapped_wrong_domain else "MISS")
            print(f"      [{mark}] {outcome.event.occurred_start_utc:%Y-%m-%d} "
                  f"{outcome.event.domain.value:<14} {outcome.event.description}")

        rows.append((subject.name, m))

    print("\n" + "-" * 78)
    print("  AGGREGATE")
    print("-" * 78)
    total_events = sum(m.total_events for _, m in rows)
    total_hits = sum(m.hits for _, m in rows)
    mean_coverage = sum(m.coverage for _, m in rows) / len(rows)
    overall_recall = total_hits / total_events if total_events else None
    overall_lift = (overall_recall / mean_coverage) if (overall_recall and mean_coverage) else None
    print(f"    {total_hits}/{total_events} events caught across {len(rows)} charts")
    print(f"    mean window coverage {mean_coverage:.1%}")
    print(f"    pooled recall {_fmt(overall_recall)} | pooled LIFT {_fmt(overall_lift)}")
    if overall_lift is not None and overall_lift <= 1.05:
        print("\n    READ THIS: a lift at or below ~1.0 means these windows are not")
        print("    distinguishable from marking dates at random. High recall here is an")
        print("    artefact of how much of each life the windows cover, not a result.")


# ── Pass 4: domain reachability ───────────────────────────────────────────────


def pass_4_domain_reachability() -> None:
    """Which life domains can never be hit, because no Sangya maps to them.

    An event in an unreachable domain is a guaranteed miss no matter how well
    the timing works, so this has to be known before any recall number is
    interpreted. Found by running the backtest, not by inspection — Mandela's
    largely legal-domain life is what surfaced it.
    """
    print("\n" + "=" * 78)
    print("PASS 4 — Life-domain reachability through the 10-Sangya scheme")
    print("=" * 78)

    covered: set[LifeDomain] = set()
    for domains in SANGYA_DOMAINS.values():
        covered |= domains
    unreachable = [d.value for d in LifeDomain if d not in covered]

    print(f"  reachable:   {sorted(d.value for d in covered)}")
    print(f"  UNREACHABLE: {unreachable}")
    print("  An event in an unreachable domain cannot be caught at any threshold.")
    print("  Note: adding mappings *after* seeing which events were missed would be")
    print("  fitting the framework to this sample. Any new mapping needs a source.")


# ── Pass 5: sensitivity sweep ─────────────────────────────────────────────────


def pass_5_sensitivity(refs) -> None:
    """Does *any* threshold beat chance? Reported as a sweep, not one lucky config."""
    print("\n" + "=" * 78)
    print("PASS 5 — Sensitivity sweep (does any configuration beat chance?)")
    print("=" * 78)

    wrapper = _wrapper()
    service = SensitiveTimelineService(SBCReportService(wrapper), LattaEngine(wrapper))
    validator = RetrodictionValidationEngine()
    now = datetime(2026, 8, 27, tzinfo=timezone.utc)

    covered: set[LifeDomain] = set()
    for domains in SANGYA_DOMAINS.values():
        covered |= domains
    unreachable = {d for d in LifeDomain if d not in covered}

    print(f"  {'min_grade':<12}{'step':<6}{'excl?':<7}{'hits':<9}{'coverage':<10}{'recall':<9}{'LIFT':<8}")
    for exclude in (False, True):
        for grade in (ConvergenceGrade.SINGLE, ConvergenceGrade.CONVERGING, ConvergenceGrade.STRONG):
            for step in (7, 15):
                hits = total = 0
                coverages = []
                for ref in refs:
                    subject = SUBJECTS[ref["chart_id"]]
                    events = [e for e in subject.events if not (exclude and e.domain in unreachable)]
                    if not events:
                        continue
                    bd = ref["birth_data"]
                    birth = datetime.fromisoformat(f"{bd['date']}T{bd['time_utc']}").replace(tzinfo=timezone.utc)
                    first = min(e.start_utc for e in subject.events)
                    last = max(e.end_utc for e in subject.events)
                    start = first.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    end = last.replace(year=last.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

                    timeline = service.build_timeline(
                        ref["expected_planets"]["moon"]["nakshatra"], birth, start, end,
                        step_days=step, now_utc=now, disclosed_events=events,
                        subject_status=subject.status, min_grade=grade,
                    )
                    m = validator.validate(timeline, events=events).metrics
                    hits += m.hits
                    total += m.total_events
                    coverages.append(m.coverage)

                coverage = sum(coverages) / len(coverages)
                recall = hits / total
                lift = recall / coverage if coverage else 0.0
                mark = " <-- beats chance" if lift > 1.05 else ""
                print(f"  {grade.value:<12}{step:<6}{'yes' if exclude else 'no':<7}"
                      f"{f'{hits}/{total}':<9}{coverage:<10.1%}{recall:<9.3f}{lift:<8.3f}{mark}")

    print("\n  'excl?' = unreachable-domain events excluded, so the framework is judged")
    print("  only on events it is structurally capable of catching.")


def _fmt(value) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def main() -> int:
    refs = json.loads(GC_MASTER.read_text(encoding="utf-8"))["references"]
    ok1 = pass_1_ephemeris(refs)
    ok2 = pass_2_invariants()
    pass_3_backtest(refs)
    pass_4_domain_reachability()
    pass_5_sensitivity(refs)

    print("\n" + "=" * 78)
    print(f"  Pass 1 (ephemeris): {'PASS' if ok1 else 'FAIL'}")
    print(f"  Pass 2 (invariants): {'PASS' if ok2 else 'FAIL'}")
    print("  Passes 3-5 report; they do not assert. A negative result here is a")
    print("  finding about the techniques, not a test failure.")
    print("=" * 78)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
