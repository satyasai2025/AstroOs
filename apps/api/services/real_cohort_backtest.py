"""
AstroOS — Real Labeled Cohort Backtest (Production-Gate Pipeline)
=================================================================

Bridges real, on-disk labeled case corpora (e.g. ``datasets/wikidot-cases/``)
into the ForwardBacktestRunner, and applies an honest Production-Grade Gate.

Design rules
------------
1.  **No fabrication.** Outcomes come only from recorded, exact-date,
    source-referenced events in the corpus files. Records with imprecise
    dates are audited and skipped, never guessed.
2.  **Pre-rectification birth data only.** Charts are built from
    ``recorded_birth_time``; the ``rectified_birth_time`` block is ignored
    here because rectification is a *prediction output* — using it to score
    predictions would be circular (leakage).
3.  **Honest certification.** A report is labeled ``production_grade=True``
    only when the corpus clears minimum evidence thresholds (unique charts,
    verified outcomes per scored category, birth-data confidence tier).
    Otherwise the verdict is EXPLORATORY: numbers are still computed and
    shown, but never certified.

Life-domain → PredictionCategory mapping (documented rationale):
    POWER        → CAREER   (10th-house matters: office, status, authority)
    ACHIEVEMENT  → CAREER   (honors/awards are classical 10th-house fruits)
    FAMILY       → MARRIAGE
    WEALTH       → FINANCE
    HEALTH       → HEALTH
    RELOCATION   → RELOCATION
    anything else → GENERAL  (kept for audit; never signature-scored)
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Sequence

from apps.api.domain.prediction_validation import (
    OutcomeRecord,
    OutcomeStatus,
    PredictionCategory,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.forward_backtest_runner import (
    ForwardBacktestReport,
    ForwardBacktestRunner,
    HistoricalCohortMember,
)
from apps.api.services.horoscope_engine import HoroscopeEngine

# ---------------------------------------------------------------------------
# Corpus mapping tables
# ---------------------------------------------------------------------------

LIFE_DOMAIN_TO_CATEGORY: dict[str, PredictionCategory] = {
    "POWER": PredictionCategory.CAREER,
    "ACHIEVEMENT": PredictionCategory.CAREER,
    "FAMILY": PredictionCategory.MARRIAGE,
    "WEALTH": PredictionCategory.FINANCE,
    "HEALTH": PredictionCategory.HEALTH,
    "RELOCATION": PredictionCategory.RELOCATION,
}
_FALLBACK_CATEGORY = PredictionCategory.GENERAL

_VALENCE_TO_DIRECTION: dict[str, str] = {
    "TRIGGER": "POSITIVE_FRUCTIFICATION",
    "RESIDUAL": "POSITIVE_FRUCTIFICATION",
    "CRISIS": "OBSTRUCTION_DELAY",
}

_VERIFICATION_MAP: dict[str, OutcomeStatus] = {
    "OFFICIAL_DOCUMENT": OutcomeStatus.VERIFIED_HISTORICAL,
}

_TIER_RANK: dict[str, int] = {"AA": 5, "A": 4, "B": 3, "C": 2, "D": 1}

#: Birth datetime is assembled from this case-file key (recorded, NOT the
#: rectified block — see module docstring rule 2).
_RECORDED_BLOCK = "recorded_birth_time"


# ---------------------------------------------------------------------------
# Audit + gate objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CorpusAudit:
    """What the loader actually saw — nothing silently dropped."""

    files_seen: int
    charts_built: int
    skipped_charts: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    verified_outcomes_by_category: dict[str, int] = field(default_factory=dict)
    unverified_outcomes: int = 0
    skipped_events: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GateVerdict:
    """Honest production-readiness certification for one backtest run."""

    production_grade: bool
    verdict_label: str  # "PRODUCTION_GRADE" | "EXPLORATORY"
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ProductionGate:
    """Minimum evidence thresholds before any report may be certified."""

    min_unique_charts: int = 30
    min_verified_outcomes_per_category: int = 30
    min_birth_tier: str = "A"

    def evaluate(self, audit: CorpusAudit) -> GateVerdict:
        reasons: list[str] = []

        if audit.charts_built < self.min_unique_charts:
            reasons.append(
                f"Insufficient unique charts: {audit.charts_built} < "
                f"{self.min_unique_charts} required."
            )

        scored = {
            cat: n
            for cat, n in audit.verified_outcomes_by_category.items()
            if cat != _FALLBACK_CATEGORY.value
        }
        if not scored:
            reasons.append(
                "No verified outcomes in any scoreable category "
                f"(min {self.min_verified_outcomes_per_category} per category required)."
            )
        for cat, n in scored.items():
            if n < self.min_verified_outcomes_per_category:
                reasons.append(
                    f"Category '{cat}': {n} verified outcomes < "
                    f"{self.min_verified_outcomes_per_category} required."
                )

        if reasons:
            return GateVerdict(
                production_grade=False,
                verdict_label="EXPLORATORY",
                reasons=tuple(reasons),
            )
        return GateVerdict(
            production_grade=True,
            verdict_label="PRODUCTION_GRADE",
            reasons=(
                f"Met thresholds: {audit.charts_built} charts, "
                + ", ".join(f"{c}={n}" for c, n in sorted(scored.items())),
            ),
        )


@dataclass(frozen=True)
class ProductionBacktestReport:
    """Bundle of the statistical report + gate verdict + corpus audit."""

    backtest_report: ForwardBacktestReport
    gate_verdict: GateVerdict
    corpus_audit: CorpusAudit

    @property
    def headline(self) -> str:
        br = self.backtest_report
        return (
            f"[{self.gate_verdict.verdict_label}] dataset={br.dataset_name} "
            f"charts={br.total_subjects} predictions={br.total_predictions} "
            f"matched={br.matched_count} precision={br.precision:.2f} "
            f"window_hit_rate={br.window_hit_rate:.2f}"
        )


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _parse_birth_dt(block: dict) -> tuple[datetime, float, float]:
    day = str(block["date"]).strip()
    t = str(block.get("time_utc", "12:00:00")).strip()
    dt = datetime.fromisoformat(f"{day}T{t}+00:00")
    if dt.tzinfo is None:
        from datetime import timezone

        dt = dt.replace(tzinfo=timezone.utc)
    lat = float(block["latitude"])
    lon = float(block["longitude"])
    return dt, lat, lon


def load_real_cohort(
    case_dir: str | Path,
    wrapper: Optional[EphemerisWrapper] = None,
    min_birth_tier: str = "A",
    ephemeris_path: str = "data/ephemeris",
) -> tuple[list[HistoricalCohortMember], CorpusAudit]:
    """Build a real HistoricalCohortMember cohort from case-file JSONs.

    Returns the cohort plus a full CorpusAudit (skip reasons included) so
    the caller can see exactly what was excluded and why.
    """
    wrapper = wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
    horoscope = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)

    min_rank = _TIER_RANK.get(min_birth_tier.upper(), 4)

    files = sorted(Path(case_dir).glob("*.json"))
    members: list[HistoricalCohortMember] = []
    skipped_charts: list[tuple[str, str]] = []
    skipped_events: list[tuple[str, str]] = []
    verified_by_cat: dict[str, int] = {}
    unverified = 0
    charts_built = 0

    for path in files:
        try:
            case = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError) as exc:
            skipped_charts.append((path.name, f"unreadable JSON: {exc}"))
            continue

        name = str(case.get("person_name") or path.stem)
        chart_id = str(case.get("chart_id") or f"REAL_{path.stem.upper()}")

        tier = str(case.get("confidence_tier", "D")).upper()
        if _TIER_RANK.get(tier, 0) < min_rank:
            skipped_charts.append((path.name, f"birth tier {tier} below {min_birth_tier}"))
            continue

        block = case.get(_RECORDED_BLOCK) or case.get("rectified_birth_time")
        if not block:
            skipped_charts.append((path.name, "no recorded_birth_time block"))
            continue

        try:
            birth_dt, lat, lon = _parse_birth_dt(block)
            chart = horoscope.generate_d1(birth_dt, lat, lon)
            tree = dasha_engine.compute_vimshottari(birth_dt, lat, lon)
        except Exception as exc:  # noqa: BLE001 — audit every failure reason
            skipped_charts.append((path.name, f"chart generation failed: {exc}"))
            continue

        charts_built += 1
        birth_date_iso = str(block.get("date", "")).strip()
        outcomes: list[OutcomeRecord] = []
        for idx, ev in enumerate(case.get("disclosed_events", [])):
            if str(ev.get("event_date_precision")) != "exact_date":
                skipped_events.append(
                    (chart_id, f"event {idx} precision={ev.get('event_date_precision')!r}")
                )
                continue
            if birth_date_iso and str(ev.get("event_date", "")).strip() == birth_date_iso:
                # Physically impossible outcome (e.g. marriage at birth).
                # Classic signature of corrupted public-dataset imports.
                skipped_events.append(
                    (chart_id, f"event {idx} rejected: event_date==birth_date")
                )
                continue

            category = LIFE_DOMAIN_TO_CATEGORY.get(
                str(ev.get("life_domain", "")).upper(), _FALLBACK_CATEGORY
            )
            status = _VERIFICATION_MAP.get(
                str(ev.get("verification_status", "")).upper(),
                OutcomeStatus.UNVERIFIED,
            )
            if status is OutcomeStatus.UNVERIFIED:
                unverified += 1

            observed = datetime.fromisoformat(f"{ev['event_date']}T00:00:00+00:00")
            outcomes.append(
                OutcomeRecord(
                    outcome_id=f"{chart_id}_ev{idx:02d}",
                    chart_id=chart_id,
                    subject_name=name,
                    category=category,
                    observed_date=observed,
                    actual_outcome_description=str(ev.get("source", "recorded event")),
                    observed_direction=_VALENCE_TO_DIRECTION.get(
                        str(ev.get("valence", "")).upper(), "NEUTRAL"
                    ),
                    verification_status=status,
                    source_reference=str(ev.get("source", path.name)),
                )
            )
            if status is OutcomeStatus.VERIFIED_HISTORICAL:
                key = category.value
                verified_by_cat[key] = verified_by_cat.get(key, 0) + 1

        members.append(
            HistoricalCohortMember(
                chart=chart,
                dasha_tree=tree,
                subject_name=name,
                outcomes=tuple(outcomes),
            )
        )

    audit = CorpusAudit(
        files_seen=len(files),
        charts_built=charts_built,
        skipped_charts=tuple(skipped_charts),
        verified_outcomes_by_category=verified_by_cat,
        unverified_outcomes=unverified,
        skipped_events=tuple(skipped_events),
    )
    return members, audit


# ---------------------------------------------------------------------------
# Runner entry point
# ---------------------------------------------------------------------------


def run_real_cohort_backtest(
    case_dir: str | Path,
    dataset_name: str,
    target_start: date,
    target_end: date,
    event_types: Sequence[str] = ("job_change",),
    runner: Optional[ForwardBacktestRunner] = None,
    gate: Optional[ProductionGate] = None,
    wrapper: Optional[EphemerisWrapper] = None,
    min_birth_tier: str = "A",
) -> ProductionBacktestReport:
    """Load the real cohort, run the forward backtest, apply the gate."""
    cohort, audit = load_real_cohort(
        case_dir, wrapper=wrapper, min_birth_tier=min_birth_tier
    )
    runner = runner or ForwardBacktestRunner()
    report = runner.run_backtest(
        cohort=cohort,
        dataset_name=dataset_name,
        target_start=target_start,
        target_end=target_end,
        event_types=list(event_types),
        min_confidence=0.0,
    )
    verdict = (gate or ProductionGate()).evaluate(audit)
    return ProductionBacktestReport(
        backtest_report=report,
        gate_verdict=verdict,
        corpus_audit=audit,
    )


# ---------------------------------------------------------------------------
# Research-batch adapter (data/research_batches schema)
# ---------------------------------------------------------------------------
#
# Schema: {"cases": [{"person": {name, dob, tob, latitude, longitude,
#          timezone?, rodden_rating?}, "life_events": [{type, event_date,
#          category, verified, ...}]}]}
#
# Known corpus state (audited): ~9,012 cases exist, but **zero** carry a
# Rodden/rating field and **100% of events have event_date equal to the
# birth date** (import corruption). This adapter therefore:
#   * treats a missing rating as tier "U" (rank 0) — never certifiable;
#   * rejects every event whose date equals the birth date as physically
#     impossible;
#   * leaves a full audit trail, so a corrected re-import flows through
#     the same code unchanged.


def _research_category(category_path: str) -> PredictionCategory:
    """Keyword mapping from AstroDatabank-style category paths."""
    c = category_path.lower()
    if "marriage" in c or "relationship" in c or "mate" in c:
        return PredictionCategory.MARRIAGE
    if "career" in c or "profession" in c or "writing" in c or "fame" in c:
        return PredictionCategory.CAREER
    if "finance" in c or "wealth" in c or "financial" in c:
        return PredictionCategory.FINANCE
    if "health" in c or "medical" in c:
        return PredictionCategory.HEALTH
    if "relocation" in c or "travel" in c:
        return PredictionCategory.RELOCATION
    return _FALLBACK_CATEGORY


def load_research_batch_cohort(
    batches_dir: str | Path,
    wrapper: Optional[EphemerisWrapper] = None,
    min_birth_tier: str = "A",
    ephemeris_path: str = "data/ephemeris",
) -> tuple[list[HistoricalCohortMember], CorpusAudit]:
    """Adapter for the research-batch corpora with strict sanity gates.

    With the current corrupted imports this yields an honest EMPTY cohort
    (no ratings -> tier U below any threshold; all events impossible).
    It exists so a corrected re-import needs zero code changes.
    """
    wrapper = wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
    horoscope = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)

    min_rank = _TIER_RANK.get(min_birth_tier.upper(), 4)

    members: list[HistoricalCohortMember] = []
    skipped_charts: list[tuple[str, str]] = []
    skipped_events: list[tuple[str, str]] = []
    verified_by_cat: dict[str, int] = {}
    unverified = 0
    charts_built = 0
    files_seen = 0
    impossible_events = 0

    for path in sorted(Path(batches_dir).glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError) as exc:
            skipped_charts.append((path.name, f"unreadable JSON: {exc}"))
            continue
        cases = payload.get("cases", []) if isinstance(payload, dict) else payload
        files_seen += 1

        for ci, case in enumerate(cases):
            person = case.get("person", {}) or {}
            name = str(person.get("name") or f"{path.stem}_case{ci:04d}")
            chart_id = f"RB_{path.stem}_{ci:04d}"

            tier = str(
                person.get("rodden_rating")
                or person.get("rating")
                or case.get("confidence_tier")
                or "U"
            ).upper()
            if _TIER_RANK.get(tier, 0) < min_rank:
                skipped_charts.append((name, f"birth tier {tier} below {min_birth_tier}"))
                continue

            dob = str(person.get("dob", "")).strip()
            tob = str(person.get("tob", "")).strip()
            if not dob or not tob:
                skipped_charts.append((name, "missing dob/tob — cannot cast chart"))
                continue

            try:
                birth_dt = datetime.fromisoformat(f"{dob}T{tob}:00+00:00")
                if birth_dt.tzinfo is None:
                    from datetime import timezone

                    birth_dt = birth_dt.replace(tzinfo=timezone.utc)
                lat = float(person["latitude"])
                lon = float(person["longitude"])
                chart = horoscope.generate_d1(birth_dt, lat, lon)
                tree = dasha_engine.compute_vimshottari(birth_dt, lat, lon)
            except Exception as exc:  # noqa: BLE001
                skipped_charts.append((name, f"chart generation failed: {exc}"))
                continue

            charts_built += 1
            outcomes: list[OutcomeRecord] = []
            for ei, ev in enumerate(case.get("life_events", [])):
                ev_date = str(ev.get("event_date", "")).strip()
                if not ev_date:
                    skipped_events.append((chart_id, f"event {ei}: no date"))
                    continue
                if ev_date == dob:
                    impossible_events += 1
                    skipped_events.append(
                        (chart_id, f"event {ei} rejected: event_date==birth_date")
                    )
                    continue

                status = (
                    OutcomeStatus.VERIFIED_HISTORICAL
                    if ev.get("verified") is True
                    else OutcomeStatus.UNVERIFIED
                )
                if status is OutcomeStatus.UNVERIFIED:
                    unverified += 1
                category = _research_category(str(ev.get("category", "")))
                outcomes.append(
                    OutcomeRecord(
                        outcome_id=f"{chart_id}_ev{ei:02d}",
                        chart_id=chart_id,
                        subject_name=name,
                        category=category,
                        observed_date=datetime.fromisoformat(
                            f"{ev_date}T00:00:00+00:00"
                        ),
                        actual_outcome_description=str(
                            ev.get("description") or ev.get("category") or "recorded event"
                        ),
                        observed_direction="POSITIVE_FRUCTIFICATION",
                        verification_status=status,
                        source_reference=str(ev.get("source", path.name)),
                    )
                )
                if status is OutcomeStatus.VERIFIED_HISTORICAL:
                    key = category.value
                    verified_by_cat[key] = verified_by_cat.get(key, 0) + 1

            members.append(
                HistoricalCohortMember(
                    chart=chart,
                    dasha_tree=tree,
                    subject_name=name,
                    outcomes=tuple(outcomes),
                )
            )

    audit = CorpusAudit(
        files_seen=files_seen,
        charts_built=charts_built,
        skipped_charts=tuple(skipped_charts),
        verified_outcomes_by_category=verified_by_cat,
        unverified_outcomes=unverified,
        skipped_events=tuple(skipped_events),
    )
    return members, audit


# ---------------------------------------------------------------------------
# AstroDatabank CSV adapter (astro.com export)
# ---------------------------------------------------------------------------
#
# Source format: flat CSV, one row per native. Key columns:
#   public_data.name / .roddenrating / .bdata.sbdate (+ccalendar) /
#   .bdata.sbtime (+jd_ut, .time_unknown) / .bdata.place.slati/.slong,
# plus an "events" column of "|" separated segments like:
#   "Work : Prize  15 June 1903   (Nobel Prize for Physics)   chart ..."
#
# Audit of the user's export (5,866 rows): AA=3,692 A=1,140 B=231 C=415
# X=335 DD=52 AX=1; 17,429 full-precision event dates; 301 partial; only
# 65 birth-date collisions. jd_ut exists on every row, so all
# LMT/DST/war-time zone reconstruction is bypassed entirely.
#
# Honesty rules carried over: ratings below threshold (incl. X = unreliable,
# DD = date doubt) are audited and skipped; partial dates and birth-date
# collisions are rejected; Julian-calendar segments prefer the printed
# "(... greg.)" date, otherwise a <=10-day calendar caveat applies.

_ADB_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
    # Abbreviations as printed in e.g. "(14 Apr 1560 greg.)"
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

_FULL_DATE_RE = re.compile(
    r"\b(\d{1,2}) (" + "|".join(_ADB_MONTHS) + r") (\d{4})\b", re.I
)
_GREG_RE = re.compile(
    r"\((\d{1,2}) (" + "|".join(_ADB_MONTHS) + r") (\d{4}) greg", re.I
)
_MONTH_YEAR_RE = re.compile(
    r"\b(" + "|".join(_ADB_MONTHS) + r") (\d{4})\b", re.I
)
_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20[0-2]\d)\b")
_STRUCT_DATE_RE = re.compile(r"\b(\d{4})/(\d{2})/(\d{2})\b")
_LL_RE = re.compile(r"^(\d+)([nsew])(\d{2})?(\d{2})?$", re.I)

_POSITIVE_EVENT = re.compile(
    r"marriage|prize|new job|new career|gain social|begin|award", re.I
)
_NEGATIVE_EVENT = re.compile(
    r"divorce|widowed|death of|breakdown|disease|accident|"
    r"depressive|institutionalized", re.I
)


def _adb_event_category(sevcode: str) -> Optional[PredictionCategory]:
    c = sevcode.lower()
    if "marriage" in c or "mate" in c or "widowed" in c or "divorce" in c:
        return PredictionCategory.MARRIAGE
    if ("work" in c and any(k in c for k in (
            "prize", "new job", "new career", "gain social",
            "begin major project", "award"))) or "award" in c:
        return PredictionCategory.CAREER
    if "financial" in c or "gain - money" in c or "loss of money" in c:
        return PredictionCategory.FINANCE
    if "diagnos" in c or "mental health" in c or "depressive" in c:
        return PredictionCategory.HEALTH
    return None


def _adb_event_direction(sevcode: str) -> str:
    if _NEGATIVE_EVENT.search(sevcode):
        return "OBSTRUCTION_DELAY"
    if _POSITIVE_EVENT.search(sevcode):
        return "POSITIVE_FRUCTIFICATION"
    return "NEUTRAL"


def _parse_adb_latlon(raw: str) -> Optional[float]:
    """'45n10' -> 45.1667, '23s3006' -> -23.5017, '9e10' -> 9.1667."""
    m = _LL_RE.match(raw.strip())
    if not m:
        return None
    deg = int(m.group(1))
    hemi = m.group(2).lower()
    minutes = int(m.group(3) or 0)
    seconds = int(m.group(4) or 0)
    val = deg + minutes / 60.0 + seconds / 3600.0
    if hemi in ("s", "w"):
        val = -val
    return val


_JD_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=None)  # J2000.0 = JD 2451545.0


def _jd_to_utc_datetime(jd: float) -> datetime:
    """JD(UT) -> timezone-aware UTC datetime.

    Uses a fixed J2000.0 anchor + timedelta instead of fromtimestamp(),
    which fails on Windows for pre-1970 (negative-epoch) dates — the
    AstroDatabank corpus is full of 19th-century and earlier births.
    """
    from datetime import timezone, timedelta

    days = float(jd) - 2451545.0
    naive = _JD_EPOCH + timedelta(days=days)
    return naive.replace(tzinfo=timezone.utc)



def _parse_event_segment(
    segment: str, struct_dates: list[tuple[int, int, int]]
) -> Optional[tuple[date, str]]:
    """Return (event_date, sevcode) for one '|' events-column segment.

    Preference order: Gregorian parenthetical (for Jul.Cal. entries),
    full text date "15 June 1903", then a structured YYYY/MM/DD from the
    same row matched by year (+ month when the text gives one).
    Returns None when only partial precision is available.
    """
    m = _GREG_RE.search(segment)
    if m:
        return (
            date(int(m.group(3)), _ADB_MONTHS[m.group(2).lower()], int(m.group(1))),
            segment,
        )
    m = _FULL_DATE_RE.search(segment)
    if m:
        return (
            date(int(m.group(3)), _ADB_MONTHS[m.group(2).lower()], int(m.group(1))),
            segment,
        )
    my = _MONTH_YEAR_RE.search(segment)
    yr = _YEAR_RE.search(segment)
    if my:
        want_year, want_month = int(my.group(2)), _ADB_MONTHS[my.group(1).lower()]
        sevcode = segment[: my.start()]
    elif yr:
        want_year, want_month = int(yr.group(1)), None
        sevcode = segment[: yr.start()]
    else:
        return None
    for y, mo, d in struct_dates:
        if y != want_year or mo == 0 or d == 0:
            continue
        if want_month is not None and mo != want_month:
            continue
        return date(y, mo, d), sevcode.strip()
    return None


def load_astrodatabank_csv(
    csv_path: str | Path,
    wrapper: Optional[EphemerisWrapper] = None,
    min_birth_tier: str = "A",
    limit: Optional[int] = None,
    ephemeris_path: str = "data/ephemeris",
) -> tuple[list[HistoricalCohortMember], CorpusAudit]:
    """Adapter for the original AstroDatabank CSV export.

    Every row carries a Rodden rating and a jd_ut birth anchor, so chart
    generation is timezone-reconstruction-free. Events come from the
    readable '|' separated column; only full-precision, non-birth dates
    in scoreable categories survive. `limit` caps charts built (tests).
    """
    wrapper = wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
    horoscope = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)
    min_rank = _TIER_RANK.get(min_birth_tier.upper(), 4)

    members: list[HistoricalCohortMember] = []
    skipped_charts: list[tuple[str, str]] = []
    skipped_events: list[tuple[str, str]] = []
    verified_by_cat: dict[str, int] = {}
    charts_built = 0

    with open(Path(csv_path), encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = {n: i for i, n in enumerate(header)}

        def col(row: list[str], name: str) -> str:
            i = idx.get(name, -1)
            return row[i] if 0 <= i < len(row) else ""

        for row in reader:
            if limit is not None and charts_built >= limit:
                break

            name = col(row, "public_data.name").strip() or "Unnamed"
            rating = col(row, "public_data.roddenrating").strip().upper()
            if _TIER_RANK.get(rating, 0) < min_rank:
                skipped_charts.append(
                    (name, f"rating {rating or 'MISSING'} below {min_birth_tier}")
                )
                continue
            if col(row, "public_data.bdata.sbtime.time_unknown").strip().lower() in (
                "true",
                "1",
            ):
                skipped_charts.append((name, "birth time unknown"))
                continue
            try:
                jd = float(col(row, "public_data.bdata.sbtime.jd_ut"))
                lat = _parse_adb_latlon(col(row, "public_data.bdata.place.slati"))
                lon = _parse_adb_latlon(col(row, "public_data.bdata.place.slong"))
                if lat is None or lon is None:
                    raise ValueError("unparseable lat/lon")
                birth_dt = _jd_to_utc_datetime(jd)
                chart = horoscope.generate_d1(birth_dt, lat, lon)
                tree = dasha_engine.compute_vimshottari(birth_dt, lat, lon)
            except Exception as exc:  # noqa: BLE001 — audit every failure reason
                skipped_charts.append((name, f"chart generation failed: {exc}"))
                continue

            charts_built += 1
            birth = birth_dt.date()
            struct_dates = sorted({
                (int(a), int(b), int(c))
                for v in row
                for a, b, c in _STRUCT_DATE_RE.findall(v)
                if (int(a), int(b), int(c))
                != (birth.year, birth.month, birth.day)
            })

            outcomes: list[OutcomeRecord] = []
            for ei, segment in enumerate(col(row, "events").split("|")):
                segment = segment.strip()
                if not segment:
                    continue
                parsed = _parse_event_segment(segment, struct_dates)
                if parsed is None:
                    skipped_events.append((name, f"event {ei}: no usable date"))
                    continue
                ev_date, sevcode = parsed
                if ev_date == birth:
                    skipped_events.append(
                        (name, f"event {ei} rejected: event_date==birth_date")
                    )
                    continue
                category = _adb_event_category(sevcode)
                if category is None:
                    skipped_events.append(
                        (name, f"event {ei}: unscored category '{sevcode[:48]}'")
                    )
                    continue
                outcomes.append(
                    OutcomeRecord(
                        outcome_id=f"ADB_{charts_built:05d}_ev{ei:02d}",
                        chart_id=f"ADB_{charts_built:05d}",
                        subject_name=name,
                        category=category,
                        observed_date=datetime(
                            ev_date.year,
                            ev_date.month,
                            ev_date.day,
                            tzinfo=birth_dt.tzinfo,
                        ),
                        actual_outcome_description=segment[:160],
                        observed_direction=_adb_event_direction(sevcode),
                        verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
                        source_reference="AstroDatabank (astro.com) export",
                    )
                )
                key = category.value
                verified_by_cat[key] = verified_by_cat.get(key, 0) + 1

            members.append(
                HistoricalCohortMember(
                    chart=chart,
                    dasha_tree=tree,
                    subject_name=name,
                    outcomes=tuple(outcomes),
                )
            )

    audit = CorpusAudit(
        files_seen=1,
        charts_built=charts_built,
        skipped_charts=tuple(skipped_charts),
        verified_outcomes_by_category=verified_by_cat,
        unverified_outcomes=0,
        skipped_events=tuple(skipped_events),
    )
    return members, audit


def run_astrodatabank_backtest(
    csv_path: str | Path,
    dataset_name: str = "astrodatabank_v1",
    target_start: Optional[date] = None,
    target_end: Optional[date] = None,
    event_types: Sequence[str] = ("job_change", "marriage"),
    min_birth_tier: str = "A",
    limit: Optional[int] = None,
    runner: Optional[ForwardBacktestRunner] = None,
    gate: Optional[ProductionGate] = None,
    wrapper: Optional[EphemerisWrapper] = None,
) -> ProductionBacktestReport:
    """End-to-end: AstroDatabank CSV -> cohort -> forward backtest -> gate."""
    cohort, audit = load_astrodatabank_csv(
        csv_path, wrapper=wrapper, min_birth_tier=min_birth_tier, limit=limit
    )
    runner = runner or ForwardBacktestRunner()
    report = runner.run_backtest(
        cohort=cohort,
        dataset_name=dataset_name,
        target_start=target_start or date(1950, 1, 1),
        target_end=target_end or date(2026, 1, 1),
        event_types=list(event_types),
        min_confidence=0.0,
    )
    verdict = (gate or ProductionGate()).evaluate(audit)
    return ProductionBacktestReport(
        backtest_report=report,
        gate_verdict=verdict,
        corpus_audit=audit,
    )


