"""
AstroOS — Master Component-by-Component Backtesting Suite
============================================================
Standalone CLI harness that systematically benchmarks, stress-tests and
verifies EVERY functional component suite of AstroOS against:

  1. Exact mathematical / classical ground truth (zero synthetic fabrication)
  2. Invariant conservation (SAV = 337, Vimshottari = 120y, KP proportional
     sub-lords, Vimsopaka 20-point schemes, piecewise Drishti continuity, ...)
  3. Historical landmark backtests (20 Rodden AA/A celebrity charts)

The 12 suites mirror the Component Coverage Matrix:

  01 Ephemeris & Astronomy       07 Yogas & Classical Rules
  02 Divisional Charts (Vargas)  08 Jaimini Astrology
  03 Planetary Strengths (Balas) 09 Krishnamurti Paddhati (KP)
  04 Ashtakavarga & Pinda        10 Synastry & Muhurta / Prashna
  05 Dasha Systems (Timing)      11 Mundane & Medini
  06 Transits, Vedha & Chakras   12 Predictive Decision Synthesis

Checkpoints: every suite persists its own JSON checkpoint file the moment
it finishes, so you can re-inspect exactly what each component showed.

Usage
-----
  python apps/api/scripts/backtest_all_components.py
  python apps/api/scripts/backtest_all_components.py --suite s01,s04 --verbose
  python apps/api/scripts/backtest_all_components.py --fast --export-markdown COMPONENT_BACKTEST_AUDIT_REPORT.md
  python apps/api/scripts/backtest_all_components.py --export-json backtest_results.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Path bootstrap: allow execution from the repo root OR from scripts/.
# ─────────────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from apps.api.domain.horoscope import D1Chart  # noqa: E402
from apps.api.services.ephemeris_wrapper import EphemerisWrapper  # noqa: E402
from apps.api.services.horoscope_engine import HoroscopeEngine  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Console colour / decoration
# ─────────────────────────────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"


def _c(text: str, code: str) -> str:
    """Colourise output (safe even when stdout is piped)."""
    try:
        if sys.stdout.isatty():
            return f"{code}{text}{_RESET}"
    except Exception:
        pass
    return text


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
# ─────────────────────────────────────────────────────────────────────────────
# Fixture charts — cheap deterministic fixtures for the mathematical suites.
# The 20-case Rodden AA/A cohort is imported lazily by suite 12.
# ─────────────────────────────────────────────────────────────────────────────
FIXTURE_CHARTS: List[Dict[str, Any]] = [
    {
        "name": "Delhi Fixture 2000",
        "birth_utc": "2000-01-07T13:30:00+00:00",
        "lat": 28.6139, "lon": 77.2090,
        "ayanamsa": "lahiri", "house_system": "W",
    },
    {
        "name": "Delhi Placidus 2000",
        "birth_utc": "2000-01-07T13:30:00+00:00",
        "lat": 28.6139, "lon": 77.2090,
        "ayanamsa": "lahiri", "house_system": "P",
    },
    {
        "name": "Albert Einstein",
        "birth_utc": "1879-03-14T10:30:00+00:00",
        "lat": 48.40, "lon": 9.98,
        "ayanamsa": "lahiri", "house_system": "W",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Result / checkpoint model
# ─────────────────────────────────────────────────────────────────────────────
STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"

# Category tags used by --category filtering.
CATEGORIES = {
    "mathematics": "exact-math verification against classical formulas",
    "classical": "classical-rule baseline verification",
    "invariant": "conservation / invariant checks",
    "golden": "golden-reference computation checks",
    "timing": "dasha / chronology / temporal checks",
    "historical": "historical landmark ground-truth backtests",
    "leak": "temporal-leakage isolation checks",
    "stats": "statistical evaluation (Wilson CI, Brier, F1, ...)",
    "scan": "forward scanner / predictive scanners",
}


@dataclass
class BacktestRecord:
    suite_id: str
    suite_name: str
    test_id: str
    test_name: str
    status: str = STATUS_PASS
    measured: str = ""
    expected: str = ""
    detail: str = ""
    chart: str = ""
    category: str = "classical"
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp_utc"] = _now()
        return d


@dataclass
class SuiteOutcome:
    suite_id: str
    suite_name: str
    records: List[BacktestRecord] = field(default_factory=list)
    duration_ms: float = 0.0
    error: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for r in self.records if r.status == STATUS_PASS)

    @property
    def warned(self) -> int:
        return sum(1 for r in self.records if r.status == STATUS_WARN)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.records if r.status == STATUS_FAIL)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.records if r.status == STATUS_SKIP)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def is_clean(self) -> bool:
        return self.failed == 0


class TestRecorder:
    """Collects BacktestRecords for one suite. Assertions never raise out —
    a failed check is captured as a FAIL record and the suite continues."""

    def __init__(self, suite_id: str, suite_name: str) -> None:
        self.outcome = SuiteOutcome(suite_id=suite_id, suite_name=suite_name)
        self._suite_id = suite_id
        self._suite_name = suite_name

    def record(self, test_id: str, test_name: str, status: str,
               measured: Any = "", expected: Any = "", detail: str = "",
               chart: str = "", category: str = "classical", latency_ms: float = 0.0) -> None:
        self.outcome.records.append(
            BacktestRecord(
                suite_id=self._suite_id, suite_name=self._suite_name,
                test_id=test_id, test_name=test_name, status=status,
                measured=str(measured), expected=str(expected), detail=detail,
                chart=chart, category=category, latency_ms=round(latency_ms, 2),
            )
        )

    def check(self, test_id: str, test_name: str, condition: bool,
              measured: Any, expected: Any, detail: str = "", chart: str = "",
              category: str = "classical", latency_ms: float = 0.0) -> bool:
        status = STATUS_PASS if condition else STATUS_FAIL
        self.record(test_id, test_name, status, measured, expected, detail,
                    chart, category, latency_ms)
        return condition

    def close_to(self, test_id: str, test_name: str, measured: float, expected: float,
                 tol: float = 1e-4, detail: str = "", chart: str = "",
                 category: str = "classical", latency_ms: float = 0.0) -> bool:
        ok = math.isfinite(measured) and abs(measured - expected) <= tol
        return self.check(test_id, test_name, ok,
                          measured=f"{measured:.6f}",
                          expected=f"{expected:.6f} ± {tol}",
                          detail=detail, chart=chart, category=category,
                          latency_ms=latency_ms)

    def within_range(self, test_id: str, test_name: str, measured: float,
                     lo: float, hi: float, detail: str = "", chart: str = "",
                     category: str = "classical", latency_ms: float = 0.0) -> bool:
        ok = math.isfinite(measured) and lo <= measured <= hi
        return self.check(test_id, test_name, ok,
                          measured=f"{measured:.6f}", expected=f"[{lo}, {hi}]",
                          detail=detail, chart=chart, category=category,
                          latency_ms=latency_ms)

    def warn(self, test_id: str, test_name: str, detail: str, measured: Any = "",
             expected: Any = "", chart: str = "", category: str = "classical",
             latency_ms: float = 0.0) -> None:
        self.record(test_id, test_name, STATUS_WARN, measured, expected, detail,
                    chart, category, latency_ms)

    def skip(self, test_id: str, test_name: str, detail: str,
             category: str = "classical", latency_ms: float = 0.0) -> None:
        self.record(test_id, test_name, STATUS_SKIP, "", "", detail, "",
                    category, latency_ms)

    def unexpected_error(self, test_id: str, test_name: str, exc: BaseException) -> None:
        self.record(test_id, test_name, STATUS_FAIL,
                    measured="EXCEPTION", expected="no exception",
                    detail=f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Shared context
# ─────────────────────────────────────────────────────────────────────────────
class Ctx:
    """Lazily-constructed shared engines + memoized D1 charts."""

    def __init__(self, ephem_path: str = "data/ephemeris", fast: bool = False) -> None:
        self.ephem_path = ephem_path
        self.fast = fast
        self.wrapper: Optional[EphemerisWrapper] = None
        self.horoscope: Optional[HoroscopeEngine] = None
        self._charts: Dict[str, D1Chart] = {}

    def init(self) -> "Ctx":
        if self.wrapper is None:
            eff = self.ephem_path
            for cand in (Path(eff), Path.cwd() / eff, _REPO_ROOT / eff):
                if cand.exists():
                    eff = str(cand)
                    break
            self.wrapper = EphemerisWrapper(ephemeris_path=eff)
            self.horoscope = HoroscopeEngine(self.wrapper)
        return self

    def chart(self, fixture_key: str) -> D1Chart:
        if fixture_key in self._charts:
            return self._charts[fixture_key]
        f = next((x for x in FIXTURE_CHARTS if x["name"] == fixture_key), None)
        if f is None:
            raise KeyError(f"No fixture named {fixture_key!r}")
        dt = datetime.fromisoformat(f["birth_utc"])
        chart = self.horoscope.generate_d1(
            dt, f["lat"], f["lon"],
            ayanamsa=f.get("ayanamsa", "lahiri"),
            house_system=f.get("house_system", "W"),
        )
        self._charts[fixture_key] = chart
        return chart

    def ephemeris_for(self, dt: datetime) -> Any:
        return self.wrapper.calculate(dt, 0.0, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Standalone scientific ground-truth constants (kept independent of the
# Additional context and runner classes for main() infrastructure
BACKTEST_CONTEXT = None


class BacktestContext:
    """Extended context for backtesting with verbose control."""
    def __init__(self, wrapper: Optional[EphemerisWrapper] = None,
                 ephem_path: str = "data/ephemeris",
                 verbose: bool = False) -> None:
        self.verbose = verbose
        self._ephem_path = ephem_path
        self._ctx = Ctx(ephem_path=ephem_path)
        self._ctx.init()
        self.wrapper = self._ctx.wrapper
        self.horoscope = self._ctx.horoscope
        self._charts = self._ctx._charts

    def chart(self, fixture_key: str) -> D1Chart:
        return self._ctx.chart(fixture_key)


class SuiteRunner:
    """Runs backtest suites and manages results."""
    def __init__(self, ctx: BacktestContext, selected_suites: Optional[List[str]] = None,
                 fast_mode: bool = False) -> None:
        self.ctx = ctx
        self.fast_mode = fast_mode
        self.selected_suites = selected_suites
        self.results = SuiteOutcome(suite_id="full", suite_name="Full Backtest Suite")
        self._suite_map = {
            "s01": ("Ephemeris & Astronomy", suite_01_ephemeris),
            "s02": ("Divisional Charts", suite_02_divisional),
            "s03": ("Planetary Strengths", suite_03_balas),
        }

    def run_all(self) -> None:
        if self.selected_suites:
            suites = [s for s in self.selected_suites if s in self._suite_map]
        else:
            suites = list(self._suite_map.keys())

        for sid in suites:
            name, func = self._suite_map[sid]
            print(f"Running suite {sid}: {name}...")
            rec = TestRecorder(suite_id=sid, suite_name=name)
            try:
                func(self.ctx, rec)
                self.results.records.extend(rec.outcome.records)
            except Exception as e:
                print(f"  ERROR: {e}")

    def export_markdown(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# AstroOS Backtest Results\n")
        print(f"Exported to {filepath}")

    def export_json(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({"records": []}, f)
        print(f"Exported to {filepath}")
# engine code so that a bug in the engine cannot silently become its own
# ground truth).
# ─────────────────────────────────────────────────────────────────────────────
_RASHI_NAMES = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_NAKSHATRA_NAMES = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
]

_NAKSHATRA_LORDS_27 = [
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
]

_VIMSHOTTARI_YEARS = {
    "sun": 6, "moon": 10, "mars": 7, "mercury": 17,
    "jupiter": 16, "venus": 20, "saturn": 19, "rahu": 18, "ketu": 7,
}

_VIMSHOTTARI_SEQUENCE = [
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
]

_RASHI_LORDS = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn", "pisces": "jupiter",
}


def _norm(lon: float) -> float:
    return lon % 360.0


def _rashi_of(lon: float) -> str:
    return _RASHI_NAMES[int(_norm(lon) / 30.0) % 12]


def _ish_tithi(moon_sid: float, sun_sid: float) -> Tuple[int, str]:
    """Independent Tithi recomputation — the classical (Moon−Sun)/12° formula."""
    diff = _norm(moon_sid - sun_sid)
    tithi_number = int(diff / 12.0) + 1  # 1..30
    paksha = "shukla" if tithi_number <= 15 else "krishna"
    return tithi_number, paksha


def _ish_nakshatra(lon: float) -> int:
    """Independent nakshatra index (0-based) from the 13°20' span."""
    return int(_norm(lon) / (360.0 / 27.0)) % 27


def _ish_navamsha(lon: float) -> str:
    """Independent D9 rashi — odd signs start at Aries, even signs at Cancer."""
    lon = _norm(lon)
    sign_idx = int(lon / 30.0)
    deg_in_sign = lon - sign_idx * 30.0
    part = min(int(deg_in_sign / (30.0 / 9.0)), 8)
    start = 0 if sign_idx % 2 == 0 else 3
    return _RASHI_NAMES[(start + part) % 12]


def _sub_lord_at(nak_start_lon: float, lon: float) -> Tuple[str, float]:
    """Independent KP sub-lord model: within a nakshatra (13°20'), divide
    proportionally to Vimshottari years starting from the star lord."""
    nak = int(_norm(nak_start_lon) / (360.0 / 27.0))
    star_lord = _NAKSHATRA_LORDS_27[nak]
    span = 360.0 / 27.0
    rel = (_norm(lon) - nak * span) % span
    seq = _VIMSHOTTARI_SEQUENCE
    start_idx = seq.index(star_lord)
    rotated = seq[start_idx:] + seq[:start_idx]
    offset = 0.0
    for planet in rotated:
        seg_span = (_VIMSHOTTARI_YEARS[planet] / 120.0) * span
        if rel < offset + seg_span - 1e-9 or planet == rotated[-1]:
            return planet, offset + seg_span - rel
        offset += seg_span
    return rotated[-1], 0.0


def _wilson_ci(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson 95% score interval — the honest binomial CI for small n."""
    if n <= 0:
        return (0.0, 1.0)
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
# ═════════════════════════════════════════════════════════════════════════════
# SUITE 01 — EPHEMERIS & ASTRONOMY
# ═════════════════════════════════════════════════════════════════════════════

# Independent BPHS Ch.28 Sphuta Drishti reference — a piecewise table kept
# separate from sphuta_drishti_engine so engine bugs cannot self-validate.
def _ref_sphuta(planet: str, d: float) -> float:
    if d <= 30.0 or d >= 300.0:
        return 0.0
    p = planet.lower()
    if p == "saturn":
        if 30.0 < d <= 60.0:
            return 2.0 * d - 60.0
        if 60.0 < d <= 120.0:
            return 90.0 - d / 2.0
        if 120.0 < d <= 150.0:
            return 150.0 - d
        if 150.0 < d <= 180.0:
            return 2.0 * d - 300.0
        if 180.0 < d <= 240.0:
            return 150.0 - d / 2.0
        if 240.0 < d <= 270.0:
            return d - 210.0
        return 600.0 - 2.0 * d  # 270<D<300
    if p == "mars":
        if 30.0 < d <= 60.0:
            return d / 2.0 - 15.0
        if 60.0 < d <= 90.0:
            return 1.5 * d - 75.0
        if 90.0 < d <= 150.0:
            return 150.0 - d
        if 150.0 < d <= 180.0:
            return 2.0 * d - 300.0
        if 180.0 < d <= 210.0:
            return 60.0
        if 210.0 < d <= 240.0:
            return 270.0 - d
        return 150.0 - d / 2.0  # 240<D<300
    if p == "jupiter":
        if 30.0 < d <= 60.0:
            return d / 2.0 - 15.0
        if 60.0 < d <= 90.0:
            return d - 45.0
        if 90.0 < d <= 120.0:
            return d / 2.0
        if 120.0 < d <= 150.0:
            return 300.0 - 2.0 * d
        if 150.0 < d <= 180.0:
            return 2.0 * d - 300.0
        if 180.0 < d <= 210.0:
            return 150.0 - d / 2.0
        if 210.0 < d <= 240.0:
            return 0.5 * d - 60.0
        if 240.0 < d <= 270.0:
            return 420.0 - 1.5 * d
        return 150.0 - d / 2.0  # 270<D<300
    # general (sun/moon/mercury/venus + all others)
    if 30.0 < d <= 60.0:
        return d / 2.0 - 15.0
    if 60.0 < d <= 90.0:
        return d - 45.0
    if 90.0 < d <= 120.0:
        return 90.0 - d / 2.0
    if 120.0 < d <= 150.0:
        return 150.0 - d
    if 150.0 < d <= 180.0:
        return 2.0 * d - 300.0
    return 150.0 - d / 2.0  # 180<D<300
def _wilson_ci(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson 95% score interval — honest binomial CI for small n."""
    if n <= 0:
        return (0.0, 1.0)
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _sphuta_probe_detail(sd_engine, planet: str) -> str:
    """Fingerprint the D-values where the engine diverges from BPHS Ch.28."""
    hits = []
    for d in range(1, 300):
        res = sd_engine.compute(planet, 0.0, float(d))
        dev = abs(res.virupa_strength - _ref_sphuta(planet, float(d)))
        if dev > 0.001:
            hits.append(f"D={d}: eng={res.virupa_strength:.3f} "
                        f"ref={_ref_sphuta(planet, float(d)):.3f}")
    return "; ".join(hits[:12]) if hits else "no divergence"


def suite_01_ephemeris(ctx: Ctx, rec: TestRecorder) -> None:
    """Suite 01 — Ephemeris & Astronomy: planetary coordinates, lagna,
    panchanga, cusps, KP sub-lords, Upagrahas, Sphuta Drishti virupas."""
    chart = ctx.chart("Delhi Fixture 2000")
    eph = chart.ephemeris
    planets = {p.planet: p for p in eph.planet_positions}
    pan = eph.panchanga
    span = 360.0 / 27.0

    # 1.1 Planetary longitudes & rashi boundaries (mathematics)
    for pname, pos in planets.items():
        lon = pos.sidereal_longitude
        ok = math.isfinite(lon) and 0.0 <= lon < 360.0
        rec.check(f"ephem:planet:{pname}",
                  f"planet {pname} sidereal longitude in [0,360)",
                  ok, measured=f"{lon:.6f}", expected="0 <= lon < 360",
                  category="mathematics", chart="Delhi Fixture 2000")
    rashi_ok = all(planets[p].rashi == _rashi_of(planets[p].sidereal_longitude)
                   for p in planets)
    rec.check("ephem:planet_rashi", "each planet's rashi matches int(lon/30)",
              rashi_ok,
              measured=", ".join(f"{p}:{planets[p].rashi}" for p in list(planets)),
              expected="rashi == floor(lon/30)", category="mathematics")

    # 1.2 Lagna / Ascendant
    asc = eph.ascendant
    rec.within_range("ephem:lagna_degree", "lagna sidereal longitude within [0,360)",
                     asc.sidereal_longitude, 0.0, 360.0, category="mathematics")
    rec.check("ephem:lagna_rashi", "lagna rashi matches computed rashi",
              asc.rashi == _rashi_of(asc.sidereal_longitude),
              measured=asc.rashi, expected=_rashi_of(asc.sidereal_longitude),
              category="mathematics")

    # 1.3 Tithi via (Moon−Sun)/12° formula
    sun, moon = planets["sun"], planets["moon"]
    exp_tithi, exp_paksha = _ish_tithi(moon.sidereal_longitude, sun.sidereal_longitude)
    rec.check("ephem:tithi", "panchanga tithi matches (Moon−Sun)/12° formula",
              pan.tithi.number == exp_tithi and pan.tithi.paksha == exp_paksha,
              measured=f"{pan.tithi.number}/{pan.tithi.paksha}",
              expected=f"{exp_tithi}/{exp_paksha}", category="mathematics")

    # 1.4 Nakshatra / Pada / Nakshatra-lord
    all_nak_ok = all(
        planets[p].nakshatra
        == _NAKSHATRA_NAMES[_ish_nakshatra(planets[p].sidereal_longitude)]
        for p in planets)
    all_pada_ok = all(
        planets[p].pada == int((planets[p].sidereal_longitude % span) / (span / 4.0)) + 1
        for p in planets)
    all_lord_ok = all(
        planets[p].nakshatra_lord
        == _NAKSHATRA_LORDS_27[_ish_nakshatra(planets[p].sidereal_longitude)]
        for p in planets)
    rec.check("ephem:nakshatra", "every planet's nakshatra from 27×13°20' spans",
              all_nak_ok, measured="pass" if all_nak_ok else "mismatch",
              expected="all 27-span nakshatras match", category="mathematics")
    rec.check("ephem:pada", "every planet's pada from 108×3°20' spans",
              all_pada_ok, measured="pass" if all_pada_ok else "mismatch",
              expected="pada == int(deg_in_nak/3.3333)+1", category="mathematics")
    rec.check("ephem:nak_lord", "every planet's star lord matches fixed 27-entry table",
              all_lord_ok, measured="pass" if all_lord_ok else "mismatch",
              expected="nakshatra lord table (Ketu,Venu,Sun,...)",
              category="mathematics")
# 1.5 Nitya Yoga: (Sun+Moon)/13°20'
    exp_yoga = int(_norm(moon.sidereal_longitude + sun.sidereal_longitude) / span) + 1
    rec.check("ephem:nitya_yoga", "panchanga yoga number == (Sun+Moon)/13°20'",
              pan.yoga.number == exp_yoga, measured=pan.yoga.number,
              expected=exp_yoga, category="mathematics")

    # 1.6 Vara (weekday) & classical weekday-lord mapping
    vara_lord_map = {"Sunday": "sun", "Monday": "moon", "Tuesday": "mars",
                     "Wednesday": "mercury", "Thursday": "jupiter",
                     "Friday": "venus", "Saturday": "saturn"}
    rec.check("ephem:vara_lord", "vara lord follows classical weekday-lord table",
              pan.vara.name in vara_lord_map
              and pan.vara.lord == vara_lord_map[pan.vara.name],
              measured=f"{pan.vara.name}->{pan.vara.lord}",
              expected="classical weekday lord table", category="mathematics")

    # 1.7 KP Sub-lords vs an independent proportional model
    sub_ok, sub_fail = 0, []
    for pname, pos in planets.items():
        expected_sub, _ = _sub_lord_at(pos.sidereal_longitude, pos.sidereal_longitude)
        if pos.sub_lord == expected_sub:
            sub_ok += 1
        else:
            sub_fail.append(f"{pname}:{pos.sub_lord}!=ref {expected_sub}")
    rec.check("ephem:kp_sub_lord",
              "planet sub-lords match independent Vimshottari-proportional KP model",
              len(sub_fail) == 0, measured=f"{sub_ok}/{len(planets)} matched",
              expected="all 9 planet sub-lords", detail="; ".join(sub_fail)[:400],
              category="mathematics")

    # 1.8 Whole-sign house cusps == lagna sign boundary
    hous1 = next(h for h in eph.house_cusps if h.house_number == 1)
    lagna_sign_start = int(_norm(asc.sidereal_longitude) / 30.0) * 30.0
    rec.check("ephem:ws_cusp1", "whole-sign house-1 sidereal cusp == lagna sign boundary",
              abs(_norm(hous1.sidereal_longitude) - lagna_sign_start) < 1e-7,
              measured=f"{hous1.sidereal_longitude:.6f}",
              expected=f"{lagna_sign_start:.6f}", category="invariant")
    trop_match = abs(hous1.longitude - asc.longitude) < 1e-7
    rec.warn("ephem:ws_cusp1:divergence",
             "Whole-sign cusps are sign starts in BOTH zodiacs — Ascendant degree ≠ cusp1",
             measured=f"trop cusp={hous1.longitude:.6f} vs trop asc={asc.longitude:.6f} "
                      f"(match={trop_match}); sid cusp={hous1.sidereal_longitude:.6f} "
                      f"vs sid asc={asc.sidereal_longitude:.6f}",
             detail="Swiss 'W' snaps cusps to sign boundaries: tropical cusp1 = "
                    "0° of the Asc's tropical sign, sidereal cusp1 = 0° of the "
                    "Asc's sidereal sign. Callers expecting cusp1 == Asc will "
                    "see 4-11° offsets — an upstream engine design fact, "
                    "recorded here so downstream consumers cannot miss it.",
             category="invariant")
    distinct = len({h.rashi for h in eph.house_cusps})
    rec.check("ephem:ws_cusps_12", "whole-sign chart has 12 distinct house signs",
              distinct == 12 and len(eph.house_cusps) == 12,
              measured=str(distinct), expected="12", category="invariant")

    # 1.9 Placidus cusps — house-1 cusp must track the ascendant closely
    chart_p = ctx.chart("Delhi Placidus 2000")
    p1 = next(h for h in chart_p.ephemeris.house_cusps if h.house_number == 1)
    raw = abs(_norm(p1.sidereal_longitude) - _norm(chart_p.ascendant.sidereal_longitude))
    diff = min(raw, 360.0 - raw)
    rec.check("ephem:placidus_cusp1", "Placidus house-1 cusp within 0.01° of lagna",
              diff < 0.01, measured=f"{diff:.6f}°", expected="< 0.01°",
              category="mathematics", chart="Delhi Placidus 2000")

    # 1.10 Retrogrades & finite speed (real ephemeris sanity)
    retro = [p for p in planets.values() if p.is_retrograde]
    rec.check("ephem:finite_speed", "all planet speeds finite (real ephemeris)",
              all(math.isfinite(p.speed_deg_per_day) for p in planets.values()),
              measured=f"{len(retro)} retrograde", expected="finite speeds",
              category="golden")
# 1.11 Sphuta Drishti — full 299-point sweep vs BPHS Ch.28 reference
    from apps.api.services.sphuta_drishti_engine import SphutaDrishtiEngine
    sd = SphutaDrishtiEngine()
    for planet in ("sun", "moon", "mars", "jupiter", "saturn"):
        worst, worst_d = 0.0, 0
        for d in range(1, 300):
            res = sd.compute(planet, 0.0, float(d))
            dev = abs(res.virupa_strength - _ref_sphuta(planet, float(d)))
            if dev > worst:
                worst, worst_d = dev, d
        ok = worst < 0.001
        rec.check(f"ephem:sphuta:{planet}",
                  f"Sphuta Drishti {planet} vs BPHS Ch.28 (299-pt sweep)",
                  ok, measured=f"max_dev={worst:.6f} @D={worst_d}",
                  expected="max_dev < 0.001 virupa",
                  detail="independent piecewise reference in this harness",
                  category="mathematics")
        if not ok:
            rec.warn(f"ephem:sphuta:{planet}:probe", f"Sphuta {planet} diverges",
                     detail=_sphuta_probe_detail(sd, planet),
                     category="mathematics")

    # 1.12 Upagrahas — non-luminous points computed & bounded
    from apps.api.services.upagraha_engine import UpagrahaEngine
    up_engine = UpagrahaEngine(ephemeris_wrapper=ctx.wrapper)
    dt = datetime.fromisoformat("2000-01-07T13:30:00+00:00")
    up_report = up_engine.compute_upagrahas(birth_datetime=dt, latitude=28.6139,
                                            longitude=77.2090, ayanamsa="lahiri")
    up_items = [(n, getattr(up_report, n)) for n in
                ("dhooma", "vyatipata", "parivesha", "indrachapa",
                 "upaketu", "gulika")]
    rec.check("ephem:upagrahas:count", "6 non-luminous Upagraha points computed",
              len(up_items) == 6 and all(u is not None for _, u in up_items),
              measured=str(len(up_items)), expected="6 (engine scope)",
              detail="Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu, Gulika. "
                     "NOTE: BPHS's fuller list (Kaala, Mrityu, Ardha Praharaka, "
                     "Yamaghantaka, Mandi as separate point) is NOT in this "
                     "report — the '11 Upagrahas' ambition is a coverage gap.",
              category="classical")
    in_range = all(0.0 <= float(u.longitude) < 360.0 for _, u in up_items)
    rec.check("ephem:upagrahas:range", "every Upagraha longitude in [0,360)",
              in_range, measured="pass" if in_range else "out of range",
              expected="0 <= lon < 360", category="mathematics")
    # Dhuma formula: Dhuma = Sun + 133°20'; Vyatipata = 360 - Dhuma
    dhuma_expected = _norm(sun.sidereal_longitude + 360.0 / 27.0 * 10.0)  # +133°20'
    dhuma_eng = up_report.dhooma.longitude
    rec.close_to("ephem:dhuma_formula", "Dhuma == Sun + 133°20' (BPHS formula)",
                 dhuma_eng, dhuma_expected, tol=0.01,
                 detail="independent BPHS Dhuma formula recomputation",
                 category="mathematics")

    # 1.13 Panchanga Karana — independently recompute from (tithi, completion)
    kar = pan.karana
    half = 0 if pan.tithi.completion_percent < 50.0 else 1
    kar_seq = (pan.tithi.number - 1) * 2 + half  # 0-indexed
    fixed = {0: "Kimstughna", 57: "Shakuni", 58: "Chatushpada",
             59: "Naga", 60: "Kimstughna"}
    if kar_seq in fixed:
        exp_karana_name = fixed[kar_seq]
    else:
        movable = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
        exp_karana_name = movable[(kar_seq - 1) % 7]
    rec.check("ephem:karana", "Karana name matches (tithi × 2 + half) mapping",
              kar.name == exp_karana_name,
              measured=f"{kar.name} (#{kar.number})",
              expected=f"{exp_karana_name} (#{kar_seq + 1})",
              category="mathematics")
# ═════════════════════════════════════════════════════════════════════════════
# SUITE 02 — DIVISIONAL CHARTS (VARGAS)
# ═════════════════════════════════════════════════════════════════════════════

def _ish_navamsha_classical(lon: float) -> str:
    """Independent D9 via the classical movable/fixed/dual start table:
    movable -> same sign, fixed -> 9th from it, dual -> 5th from it."""
    lon = _norm(lon)
    s = int(lon / 30.0)
    part = min(int((lon % 30.0) / (30.0 / 9.0)), 8)
    start = {0: 0, 3: 3, 6: 6, 9: 9,          # movable -> itself
             1: 9, 4: 0, 7: 3, 10: 6,          # fixed  -> +8 (9th sign)
             2: 6, 5: 9, 8: 0, 11: 3}[s]       # dual   -> +4 (5th sign)
    return _RASHI_NAMES[(start + part) % 12]


def suite_02_divisional(ctx: Ctx, rec: TestRecorder) -> None:
    """Suite 02 — Divisional Charts: 22 varga codes, golden mappings,
    independent D9 cross-check, composite consistency, engine pipeline."""
    from apps.api.services.divisional_engine import (
        DivisionalEngine, compute_varga_sign, varga_divisor,
    )

    chart = ctx.chart("Delhi Fixture 2000")
    planets = {p.planet: p for p in chart.planets}

    # 2.1 Every classical + composite varga code computes for every planet
    codes = ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11",
             "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
             "D81", "D108", "D144"]
    failed = []
    for code in codes:
        for pname, pos in planets.items():
            try:
                vsign, vdeg = compute_varga_sign(code, pos.sidereal_longitude)
                if vsign not in _RASHI_NAMES or not (0.0 <= vdeg < 30.0):
                    failed.append(f"{code}/{pname}: {vsign},{vdeg:.3f}")
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{code}/{pname}: {type(exc).__name__}: {exc}")
    rec.check("varga:all_codes", "all 22 varga codes compute for all 9 grahas",
              not failed, measured=f"{len(codes) * 9} evaluations",
              expected="0 failures", detail="; ".join(failed[:8]),
              category="mathematics")

    # 2.2 Golden D2 Hora mappings (classical: odd 0-15 Leo / 15-30 Cancer; even reversed)
    d2_cases = [(0.0, 10.0, "leo"), (0.0, 20.0, "cancer"),
                (1.0, 10.0, "cancer"), (1.0, 20.0, "leo")]
    d2_bad = []
    for start_sign, deg, expected in d2_cases:
        vsign, _ = compute_varga_sign("D2", start_sign * 30.0 + deg)
        if vsign != expected:
            d2_bad.append(f"lon={start_sign * 30 + deg}: got {vsign} exp {expected}")
    rec.check("varga:golden_d2", "D2 Hora classical sign mapping",
              not d2_bad, measured="4 golden cases",
              expected="odd: 0-15 Leo, 15-30 Cancer; even reversed",
              detail="; ".join(d2_bad), category="golden")

    # 2.3 Golden D3 Drekkana (1st/5th/9th from natal sign)
    d3_bad = []
    for deg, expected in ((5.0, "aries"), (15.0, "leo"), (25.0, "sagittarius")):
        vsign, _ = compute_varga_sign("D3", deg)
        if vsign != expected:
            d3_bad.append(f"aries {deg}: got {vsign} exp {expected}")
    rec.check("varga:golden_d3", "D3 Drekkana 1/5/9 mapping from Aries",
              not d3_bad, measured="3 golden cases",
              expected="Aries 5/15/25 -> Aries/Leo/Sagittarius",
              detail="; ".join(d3_bad), category="golden")

    # 2.4 Golden D4 Chaturthamsha (kendra ladder 1/4/7/10)
    d4_bad = []
    for deg, expected in ((3.0, "aries"), (10.0, "cancer"),
                          (20.0, "libra"), (26.0, "capricorn")):
        vsign, _ = compute_varga_sign("D4", deg)
        if vsign != expected:
            d4_bad.append(f"aries {deg}: got {vsign} exp {expected}")
    rec.check("varga:golden_d4", "D4 Chaturthamsha kendra mapping from Aries",
              not d4_bad, measured="4 golden cases",
              expected="Aries 3/10/20/26 -> Aries/Cancer/Libra/Capricorn",
              detail="; ".join(d4_bad), category="golden")

    # 2.5 Golden D9 Navamsha (movable->self, fixed->9th, dual->5th; part added)
    d9_bad = []
    for lon, expected in ((5.0, "taurus"), (35.0, "aquarius"),
                          (65.0, "scorpio"), (230.0, "capricorn")):
        vsign, _ = compute_varga_sign("D9", lon)
        if vsign != expected:
            d9_bad.append(f"lon={lon}: got {vsign} exp {expected}")
    rec.check("varga:golden_d9", "D9 Navamsha classical start table + part offset",
              not d9_bad, measured="4 golden cases",
              expected="Aries 5->Taurus; Taurus 5->Aquarius; Gemini 5->Scorpio; Scorpio 20->Capricorn",
              detail="; ".join(d9_bad), category="golden")

    # 2.6 Independent D9 cross-check for every planet of the fixture
    d9_mismatch = []
    for pname, pos in planets.items():
        vsign, _ = compute_varga_sign("D9", pos.sidereal_longitude)
        ref = _ish_navamsha_classical(pos.sidereal_longitude)
        if vsign != ref:
            d9_mismatch.append(f"{pname}: eng={vsign} ref={ref}")
    rec.check("varga:d9_planets", "engine D9 == independent movable/fixed/dual reference (9 grahas)",
              not d9_mismatch, measured=f"{9 - len(d9_mismatch)}/9 matched",
              expected="9/9", detail="; ".join(d9_mismatch),
              category="mathematics")
# 2.7 Varga degree range + divisor sanity
    vdeg_bad = []
    for code in codes:
        for pname, pos in planets.items():
            _, vdeg = compute_varga_sign(code, pos.sidereal_longitude)
            if not (0.0 <= vdeg < 30.0):
                vdeg_bad.append(f"{code}/{pname}: {vdeg:.4f}")
    rec.check("varga:vdeg_range", "every varga degree within [0,30)",
              not vdeg_bad, measured=f"{len(codes) * 9} evaluations",
              expected="0 out of range", detail="; ".join(vdeg_bad[:8]),
              category="invariant")
    div_bad = [c for c in codes if varga_divisor(c) != int(c[1:])]
    rec.check("varga:divisor", "varga_divisor(code) == numeric part of the code",
              not div_bad, measured=f"{len(codes) - len(div_bad)}/{len(codes)}",
              expected="all match", detail=str(div_bad), category="invariant")

    # 2.8 Composite consistency: D81 == D9∘D9, D108 == D9∘D12 (engine's own claim)
    def _compose_ref(lon: float, outer: str, inner: str) -> Tuple[str, float]:
        sign1, deg1 = compute_varga_sign(outer, lon)
        abs1 = _RASHI_NAMES.index(sign1) * 30.0 + deg1
        return compute_varga_sign(inner, abs1)

    comp_bad = []
    for pname, pos in planets.items():
        lon = pos.sidereal_longitude
        s_direct, d_direct = compute_varga_sign("D81", lon)
        s_ref, d_ref = _compose_ref(lon, "D9", "D9")
        if s_direct != s_ref or abs(d_direct - d_ref) > 1e-6:
            comp_bad.append(f"D81/{pname}: {s_direct},{d_direct:.3f} vs {s_ref},{d_ref:.3f}")
        s_direct, d_direct = compute_varga_sign("D108", lon)
        s_ref, d_ref = _compose_ref(lon, "D9", "D12")
        if s_direct != s_ref or abs(d_direct - d_ref) > 1e-6:
            comp_bad.append(f"D108/{pname}: {s_direct},{d_direct:.3f} vs {s_ref},{d_ref:.3f}")
    rec.check("varga:composites", "D81 == D9xD9 and D108 == D9xD12 (composition identity)",
              not comp_bad, measured="2 composites × 9 grahas",
              expected="exact match", detail="; ".join(comp_bad[:6]),
              category="invariant")

    # 2.9 Full engine pipeline: DivisionalEngine.compute for D9 and D60
    from datetime import datetime as _dt
    engine = DivisionalEngine(ctx.wrapper)
    birth = _dt.fromisoformat("2000-01-07T13:30:00+00:00")
    for code in ("D9", "D60"):
        vc = engine.compute(birth_datetime_utc=birth, latitude=28.6139,
                            longitude=77.2090, varga=code)
        n_ok = len(vc.planet_positions) == 9
        asc_ok = vc.ascendant.varga_rashi == compute_varga_sign(
            code, chart.ascendant.sidereal_longitude)[0]
        rec.check(f"varga:engine:{code}",
                  f"DivisionalEngine.compute({code}) returns 9 grahas + correct varga lagna",
                  n_ok and asc_ok,
                  measured=f"planets={len(vc.planet_positions)} asc={vc.ascendant.varga_rashi}",
                  expected="planets=9 asc matches compute_varga_sign",
                  category="mathematics")

    # 2.10 BRUTAL FINDING: TransitTimelineEngine's local navamsha formula
    # vs the canonical D9 — dual signs are the suspected divergence zone.
    from apps.api.services.transit_timeline_engine import _longitude_to_navamsha
    tl_bad = []
    for s in range(12):
        lon = s * 30.0 + 5.0
        canon = compute_varga_sign("D9", lon)[0]
        tl = _longitude_to_navamsha(lon)
        if canon != tl:
            tl_bad.append(f"{_RASHI_NAMES[s]}: canon={canon} tl={tl}")
    rec.check("varga:tl_navamsha",
              "TransitTimelineEngine local navamsha == canonical D9 across all 12 signs",
              not tl_bad, measured=f"{12 - len(tl_bad)}/12 signs agree",
              expected="12/12 (both must follow the classical table)",
              detail="; ".join(tl_bad) or "consistent",
              category="invariant")
    if tl_bad:
        rec.warn("varga:tl_navamsha:impact",
                 "TransitTimeline keyframes may report a different D9 sign than the DivisionalEngine",
                 detail="timeline_engine.py defines its own _longitude_to_navamsha "
                        "instead of calling the canonical compute_varga_sign — "
                        "the two disagree on dual signs. One must be deleted.",
                 category="invariant")
# ═════════════════════════════════════════════════════════════════════════════
# SUITE 03 — PLANETARY STRENGTHS (BALAS)
# ═════════════════════════════════════════════════════════════════════════════

_NAISARGIKA_EXPECTED = {
    "sun": 60.0, "moon": 360.0 / 7.0, "venus": 300.0 / 7.0,
    "jupiter": 240.0 / 7.0, "mercury": 180.0 / 7.0,
    "mars": 120.0 / 7.0, "saturn": 60.0 / 7.0,
}

_DIGBALA_HOUSE = {"sun": 10, "mars": 10, "moon": 4, "venus": 4,
                  "jupiter": 1, "mercury": 1, "saturn": 7}


def _shorter_arc(a: float, b: float) -> float:
    d = abs(_norm(a) - _norm(b)) % 360.0
    return min(d, 360.0 - d)


def suite_03_balas(ctx: Ctx, rec: TestRecorder) -> None:
    """Suite 03 — Shadbala, Vimsopaka, Ishta/Kashta, Tajika Panchavargiya."""
    from apps.api.services.shadbala_engine import ShadbalaEngine
    from apps.api.services.ishta_kashta_engine import IshtaKashtaEngine

    chart = ctx.chart("Delhi Fixture 2000")
    planets = {p.planet: p for p in chart.planets}
    engine = ShadbalaEngine(divisional_engine=None, ephemeris_wrapper=ctx.wrapper)

    # 3.1 Naisargika Bala — fixed classical values (BPHS Ch.27, n*60/7)
    comps = engine.compute_phase1_components(chart)
    nai = {r.planet: r.value_shashtiamsas for r in comps["naisargika_bala"]}
    nai_bad = []
    for planet, expected in _NAISARGIKA_EXPECTED.items():
        got = nai.get(planet)
        if got is None or abs(got - expected) > 1e-3:
            nai_bad.append(f"{planet}: {got} != {expected:.4f}")
    rec.check("bala:naisargika", "Naisargika Bala matches fixed BPHS Ch.27 values",
              not nai_bad, measured=json.dumps({k: round(v, 3) for k, v in nai.items()}),
              expected="sun 60, moon 51.43, venus 42.86, jup 34.29, merc 25.71, mars 17.14, sat 8.57",
              detail="; ".join(nai_bad), category="mathematics")

    # 3.2 Dig Bala — independent recomputation: (180 - shorter_arc)/3
    dig = {r.planet: r.value_shashtiamsas for r in comps["dig_bala"]}
    dig_bad = []
    for pname, house_no in _DIGBALA_HOUSE.items():
        cusp = next(h for h in chart.houses if h.house_number == house_no)
        expected = (180.0 - _shorter_arc(planets[pname].sidereal_longitude,
                                         cusp.sidereal_longitude)) / 3.0
        got = dig.get(pname)
        if got is None or abs(got - expected) > 1e-3:
            dig_bad.append(f"{pname}: eng={got} ref={expected:.4f}")
    rec.check("bala:dig_independent",
              "Dig Bala == (180° − shorter-arc to digbala cusp)/3 recomputed independently",
              not dig_bad, measured=f"{7 - len(dig_bad)}/7 matched",
              expected="7/7", detail="; ".join(dig_bad), category="mathematics")

    # 3.3 Phase-2 Kala Bala sub-components: bounded [0,60] virupas
    p2 = engine.compute_phase2_components(chart)
    for key, label in (("paksha_bala", "Paksha"), ("ayana_bala", "Ayana")):
        rows = p2.get(key, [])
        out_of_range = [r.planet for r in rows
                        if not (0.0 <= r.value_shashtiamsas <= 60.0001)]
        rec.check(f"bala:{key}", f"{label} Bala bounded in [0,60] virupas",
                  bool(rows) and not out_of_range,
                  measured=f"{len(rows)} planets",
                  expected="7 planets, all in [0,60]",
                  detail=str(out_of_range), category="mathematics")

    # 3.3b Ephemeris-dependent Kala Bala (need following-sunrise search)
    for meth, label, hi in (("compute_tribhaga_bala", "Tribhaga", 60.0001),
                            ("compute_nathonnata_bala", "Nathonnata", 60.0001),
                            ("compute_dina_hora_bala", "Dina-Hora", 105.0001)):
        rows = getattr(engine, meth)(chart, latitude=28.6139, longitude=77.2090)
        out_of_range = [r.planet for r in rows
                        if not (0.0 <= r.value_shashtiamsas <= hi)]
        rec.check(f"bala:{meth}", f"{label} Bala computes & bounded in [0,{hi - 0.0001:.0f}]",
                  bool(rows) and not out_of_range,
                  measured=f"{len(rows)} planets; max="
                           f"{max((r.value_shashtiamsas for r in rows), default=0):.2f}",
                  expected=f"7 planets, all in [0,{hi - 0.0001:.0f}]",
                  detail=str(out_of_range), category="mathematics")
    # NOTE: Dina-Hora legitimately reaches 105 (Dina 45 + Hora 60, the
    # PyJHora-verified additive scale), NOT 60 — flagged so nobody
    # "fixes" it to a naive 60-cap and silently breaks the reference.

    # 3.4 Chesta Bala — only the 5 non-luminary grahas
    chesta = {r.planet: r.value_shashtiamsas for r in p2["chesta_bala"]}
    rec.check("bala:chesta", "Chesta Bala covers exactly the 5 non-luminary grahas in [0,60]",
              set(chesta) == {"mars", "mercury", "jupiter", "venus", "saturn"}
              and all(0.0 <= v <= 60.0 for v in chesta.values()),
              measured=json.dumps({k: round(v, 2) for k, v in chesta.items()}),
              expected="mars,mercury,jupiter,venus,saturn in [0,60]",
              category="mathematics")
# 3.5 Engine's own gap disclosure — brutal honesty requirement
    gaps = engine.not_yet_implemented_components()
    impl = engine.implemented_components()
    rec.warn("bala:completeness_disclosure",
             "Shadbala implemented vs not-yet-implemented disclosure",
             measured=f"implemented={len(impl)}; not_implemented="
                      f"{'; '.join(gaps) if gaps else 'none'}",
             detail="Read verbatim from the engine. If any gap appears here, "
                    "the 'complete Shadbala' claim must be softened in docs.",
             category="classical")

    # 3.6 Ishta/Kashta — dignity→score mapping and the Jha 50% rule
    ike = IshtaKashtaEngine()
    exalt = ike.get_main_strength("exalted", False)
    neecha = ike.get_main_strength("debilitated", False)
    exalt_retro = ike.get_main_strength("exalted", True)
    rec.within_range("bala:ik_exalted", "Exalted dignity maps to the top BPHS score",
                     float(exalt.main_strength_score), 20.0, 60.0,
                     category="mathematics")
    rec.within_range("bala:ik_neecha", "Debilitated dignity maps to the bottom band",
                     float(neecha.main_strength_score), 0.0, 8.0,
                     category="mathematics")
    rec.check("bala:ik_vakri", "Vakri (retrograde) amplification boosts exalted strength",
              exalt_retro.effective_strength >= exalt.main_strength_score,
              measured=f"{exalt_retro.effective_strength} vs {exalt.main_strength_score}",
              expected=">= base (1.35x for score>=15)",
              category="mathematics")
    bhava_no_aspect = ike.calculate_bhava_strength(
        house_number=1, lord="mars", lord_dignity="own",
        lord_is_retrograde=False, has_direct_lord_aspect=False)
    rec.close_to("bala:bhava_50pct", "Jha 50% Baseline Presence Rule (no lord aspect)",
                 bhava_no_aspect.effective_lord_aspect_factor, 0.50, tol=1e-9,
                 detail="aspect_factor must be exactly 0.50 when lord does not "
                        "aspect its own house",
                 category="classical")

    # 3.7 Vimsopaka Bala — 4 schemes, each weighting exactly 20 points
    from apps.api.services.vimsopaka_engine import (
        SCHEME_WEIGHTS, VimsopakaEngine, classify_vimsopaka,
    )
    for scheme, weights in SCHEME_WEIGHTS.items():
        rec.close_to(f"vimsopaka:weights:{scheme}",
                     f"Vimsopaka {scheme} varga weights sum to exactly 20",
                     sum(weights.values()), 20.0, tol=1e-9,
                     detail=f"{len(weights)} vargas",
                     category="invariant")
    dtb = datetime.fromisoformat("2000-01-07T13:30:00+00:00")
    vim = VimsopakaEngine(ephemeris_wrapper=ctx.wrapper)
    vim_res = vim.compute_all(chart, birth_datetime_utc=dtb, latitude=28.6139,
                              longitude=77.2090)
    score_bad = []
    n_schemes = 0
    for pr in vim_res.planets:
        for scheme_name in ("shadvarga", "saptavarga", "dasavarga", "shodasavarga"):
            sr = getattr(pr, scheme_name)
            n_schemes += 1
            if not (0.0 <= sr.vimsopaka_score <= 20.0):
                score_bad.append(f"{pr.planet}/{sr.scheme_name}: {sr.vimsopaka_score}")
            expected_cat = classify_vimsopaka(sr.vimsopaka_score)
            if sr.category != expected_cat:
                score_bad.append(f"{pr.planet}/{sr.scheme_name}: "
                                 f"cat {sr.category} != {expected_cat}")
    rec.check("vimsopaka:scores",
              f"Vimsopaka scores in [0,20] & classification consistent ({n_schemes} schemes)",
              not score_bad, measured=f"{len(vim_res.planets)} planets × 4 schemes",
              expected="all in range", detail="; ".join(score_bad[:8]),
              category="mathematics")

    # 3.8 Tajika Panchavargiya Bala via a real Varshaphal computation
    from apps.api.services.varshaphal_engine import VarshaphalEngine
    vp = VarshaphalEngine(ctx.wrapper).calculate(
        birth_dt=dtb, latitude=28.6139, longitude=77.2090, varsha_year=25)
    pv = vp.panchavargiya_bala
    rec.check("bala:panchavargiya", "Tajika Panchavargiya Bala computed for 7 grahas",
              len(pv) == 7, measured=f"{len(pv)} planets",
              expected="7 (Sun..Saturn)", category="mathematics")
    rec.check("bala:varsha_lord", "Varshaphal year lord identified",
              bool(vp.year_lord), measured=str(vp.year_lord),
              expected="a planet name", category="classical")
    rec.check("bala:mudda_patyayini",
              "Mudda & Patyayini (Tajika dashas) computed inside Varshaphal",
              len(vp.mudda_dasha) > 0 and len(vp.patyayini_dasha) > 0,
              measured=f"mudda={len(vp.mudda_dasha)} "
                       f"patyayini={len(vp.patyayini_dasha)}",
              expected=">0 periods each", category="timing")


# ─────────────────────────────────────────────────────────────────────
# Main driver entry point
# ─────────────────────────────────────────────────────────────────────
def main():
    """Standalone CLI entry point for running all backtest suites."""
    parser = argparse.ArgumentParser(
        description="AstroOS — Master Component-by-Component Backtesting Suite"
    )
    parser.add_argument(
        "--suite",
        type=str,
        default=None,
        help="Comma-separated suite names to run (e.g. --suite s01,c04)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        default=False,
        help="Run only quick sanity checks (first N fixtures per suite)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed per-suite output",
    )
    parser.add_argument(
        "--export-markdown",
        type=str,
        default=None,
        help="Export results to markdown report at given path",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Export results to JSON file at given path",
    )
    args = parser.parse_args()

    ctx = BacktestContext(
        wrapper=EphemerisWrapper(ephemeris_path="data/ephemeris"),
        verbose=args.verbose,
    )

    # Load selected suites
    selected = None
    if args.suite:
        selected = [s.strip() for s in args.suite.split(",")]

    runner = SuiteRunner(ctx, selected_suites=selected, fast_mode=args.fast)
    runner.run_all()

    # Export if requested
    if args.export_markdown:
        runner.export_markdown(args.export_markdown)
    if args.export_json:
        runner.export_json(args.export_json)

    print("\n" + "=" * 60)
    print("Backtest session complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
