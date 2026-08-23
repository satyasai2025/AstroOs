"""
AstroOS — Varshaphal Engine (Stage 1: Varsha Pravesh chart + Muntha;
Stage 2: Tajika aspects)

Varsha Pravesh (solar return): the exact moment, in the target Gregorian
year, that the Sun returns to the same SIDEREAL longitude it held at
birth. The Varsha chart is a full chart computed at that moment and
location — EphemerisWrapper.calculate() is moment-agnostic, so no new
chart-computation logic is needed, only the solver that finds the moment.

Muntha: the natal Ascendant's Rashi, advanced by `varsha_year` signs
(one Rashi per year) — placed as a point in the Varsha chart's Whole
Sign houses.

Tajika aspects (Ithasala/Isharpha): unlike Sahams/Year Lord, these come
from orbital mechanics, not a named lookup table. For each pair of the
7 classical Grahas and each of the 5 aspect angles (0/60/90/120/180°),
this computes whether the angular separation is closing (applying) or
opening (separating), and — for applying pairs — whether the aspect
will become exact before EITHER planet leaves its current sign
(Ithasala) using each planet's own sidereal speed and degrees-to-
sign-end. See test_varshaphal_engine.py for kinematic self-checks
(constructed planet pairs with known closing/separating behaviour).

Year Lord (Panchadhikari): 5 candidate planets, shortlisted by whether
they cast a sign-based benefic (trine/sextile) or malefic (square/
opposition/conjunction) Tajika aspect onto the Varsha Lagna sign — see
domain/varshaphal.py's module docstring for the PyJHora cross-check and
the one documented simplification (Panchvargiya Bala tie-break skipped).

Sahams: all 36 classical A-B+C longitude formulas, cross-checked
against PyJHora's vedic/horoscope/transit/saham.py — same verified
source as Year Lord — AND against a real Classical Vedic System desktop-
software export supplied by the user (birth 1971-06-30 04:57:40 IST,
Vadodara; Varsha year 55 = 2026-06-30 solar return). 33 of 36 values
matched that Classical Vedic export within the same ~1-2 arcminute systematic
tolerance already documented for this codebase's ayanamsa (see
domain/varshaphal.py). One deliberate deviation from PyJHora:
Gaurava Saham uses the SAME formula as Yasas Saham (Jupiter - Punya +
Lagna), not PyJHora's book formula (Jupiter - Moon + Sun) — PyJHora's
own source comment admits that book formula "does not match Classical Vedic
s/w", and the real Classical Vedic export confirms Gaurava and Yasas share an
identical value, so the export was trusted over the book formula.

KNOWN LIMITATION — Karma, Bandhu, and Vanik Saham came out a full sign
(30°) off the Classical Vedic export, all three specifically when Mercury and
Lagna land in the same Rashi (true for the export chart: Mercury,
Jupiter, Venus, and Lagna were all in Cancer). PyJHora's
_is_C_between_B_to_A sweep never re-checks B's own Rashi, so B and C
sharing a Rashi is a genuine gap in the ported algorithm, not just
tolerance drift — but two different tie-break rules were tried (treat
same-Rashi B/C as "found", and re-prioritise A over C on ties) and
each fixed these 3 while silently breaking 10+ of the other 33 that
were already correct. Given one adversarial chart isn't enough to
derive the right general rule, these 3 are left as-is (matching
PyJHora's literal algorithm) rather than risk a blind fix. Needs a
second real Classical Vedic export — ideally one where B and C DON'T coincide in
sign — to properly diagnose.

Not yet built: Mudda Dasha, Patyayini Dasha — deferred, see
domain/varshaphal.py.
"""

from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

from apps.api.domain.varshaphal import (
    MunthaInfo,
    SahamInfo,
    TajikaAspect,
    VarshaphalResult,
    YearLordInfo,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd, jd_to_datetime
from packages.shared.constants import DEGREES_PER_RASHI, SIGN_LORDS
from packages.shared.enums import AyanamsaSystem, Rashi

_RASHI_LIST: list[str] = [r.value for r in Rashi]

# Classical Tajika triplicity (Tri-Rasi) lords, one of the 5 Year Lord
# candidates. Index 0=Mesha … 11=Meena. Cross-checked against PyJHora's
# const.tri_rasi_daytime_lords / tri_rasi_nighttime_lords (verified
# against P.V.R. Narasimha Rao's book). Planet index order: 0=sun,
# 1=moon, 2=mars, 3=mercury, 4=jupiter, 5=venus, 6=saturn.
_TRI_RASI_PLANET_ORDER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_TRI_RASI_DAY_LORDS = [0, 5, 6, 5, 4, 1, 3, 2, 6, 2, 4, 1]
_TRI_RASI_NIGHT_LORDS = [4, 1, 3, 2, 0, 5, 6, 5, 6, 2, 4, 1]

# Sun's mean sidereal motion — used only to convert a longitude error into
# a time correction for the solver's Newton-style iteration; the iteration
# itself converges on the exact instantaneous position, so this being a
# mean (not true) rate only affects convergence speed, not accuracy.
_SUN_MEAN_DEG_PER_DAY = 0.9856

_SOLVER_MAX_ITERATIONS = 8
_SOLVER_TOLERANCE_DEG = 1e-6

# The 7 classical Grahas Tajika aspects are reckoned between (no Rahu/Ketu).
_TAJIKA_PLANETS: list[str] = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_ASPECT_ANGLES: list[int] = [0, 60, 90, 120, 180]
_ISHARPHA_LOOKBACK_DAYS = 1.0


class VarshaphalEngine:
    """Computes the Varsha Pravesh chart and Muntha for one solar-return year."""

    def __init__(self, wrapper: EphemerisWrapper):
        self._wrapper = wrapper

    def calculate(
        self,
        birth_dt: datetime,
        latitude: float,
        longitude: float,
        varsha_year: int,
        ayanamsa: str = AyanamsaSystem.LAHIRI.value,
        house_system: str = "W",
    ) -> VarshaphalResult:
        if varsha_year < 1:
            raise ValueError("varsha_year must be >= 1 (1 = first birthday).")

        natal_chart = self._wrapper.calculate(birth_dt, latitude, longitude, ayanamsa, house_system)
        natal_sun = next(p for p in natal_chart.planet_positions if p.planet == "sun")
        natal_sun_sid_lon = natal_sun.sidereal_longitude

        solar_return_jd = self._solve_solar_return(
            birth_dt, natal_sun_sid_lon, varsha_year, ayanamsa,
        )
        solar_return_dt = jd_to_datetime(solar_return_jd)

        varsha_chart = self._wrapper.calculate(
            solar_return_dt, latitude, longitude, ayanamsa, house_system
        )

        muntha = self._compute_muntha(natal_chart.ascendant.rashi, varsha_year, varsha_chart)
        tajika_aspects = self._compute_tajika_aspects(varsha_chart)
        year_lord = self._compute_year_lord(natal_chart.ascendant.rashi, muntha, varsha_chart)
        sahams = self._compute_sahams(varsha_chart)

        return VarshaphalResult(
            varsha_year=varsha_year,
            solar_return_jd=solar_return_jd,
            varsha_chart=varsha_chart,
            muntha=muntha,
            tajika_aspects=tajika_aspects,
            year_lord=year_lord,
            sahams=sahams,
        )

    def _solve_solar_return(
        self,
        birth_dt: datetime,
        natal_sun_sid_lon: float,
        varsha_year: int,
        ayanamsa: str,
    ) -> float:
        """
        Newton-style iterative solve for the Julian Day, near the
        `varsha_year`-th anniversary of `birth_dt`, at which the Sun's
        sidereal longitude equals `natal_sun_sid_lon`.
        """
        guess_dt = birth_dt + timedelta(days=365.2425 * varsha_year)
        jd = datetime_to_jd(guess_dt)

        # pyswisseph's sidereal mode is process-global — set it once under
        # the wrapper's lock for this whole solve, rather than per-iteration
        # unlocked calls that could interleave with a concurrent request's
        # calculate() and silently read the wrong ayanamsa (see
        # EphemerisWrapper.sidereal_mode's docstring).
        with self._wrapper.sidereal_mode(ayanamsa):
            for _ in range(_SOLVER_MAX_ITERATIONS):
                ayanamsa_val = self._wrapper.get_ayanamsa(jd)
                sun_tropical = self._wrapper.get_planet_position("sun", jd)
                sun_sid_lon = self._wrapper.to_sidereal(sun_tropical.longitude, ayanamsa_val)

                diff = sun_sid_lon - natal_sun_sid_lon
                diff = (diff + 180.0) % 360.0 - 180.0  # normalise to [-180, 180)

                if abs(diff) < _SOLVER_TOLERANCE_DEG:
                    break

                jd -= diff / _SUN_MEAN_DEG_PER_DAY

        return jd

    @staticmethod
    def _degrees_to_sign_exit(rashi_degree: float, speed_deg_per_day: float) -> float:
        """Degrees remaining, in the planet's own direction of travel, until it leaves its current sign."""
        if speed_deg_per_day >= 0:
            return DEGREES_PER_RASHI - rashi_degree
        return rashi_degree

    @classmethod
    def _compute_tajika_aspects(cls, varsha_chart) -> tuple[TajikaAspect, ...]:
        positions = {p.planet: p for p in varsha_chart.planet_positions if p.planet in _TAJIKA_PLANETS}
        aspects: list[TajikaAspect] = []

        for name_a, name_b in itertools.combinations(_TAJIKA_PLANETS, 2):
            a, b = positions.get(name_a), positions.get(name_b)
            if a is None or b is None:
                continue

            d = ((b.sidereal_longitude - a.sidereal_longitude + 180.0) % 360.0) - 180.0
            sep = abs(d)
            sign_d = 1.0 if d >= 0 else -1.0
            relative_speed = b.speed_deg_per_day - a.speed_deg_per_day
            dsep_dt = sign_d * relative_speed

            exit_a = cls._degrees_to_sign_exit(a.rashi_degree, a.speed_deg_per_day)
            exit_b = cls._degrees_to_sign_exit(b.rashi_degree, b.speed_deg_per_day)
            t_exit_a = exit_a / abs(a.speed_deg_per_day) if abs(a.speed_deg_per_day) > 1e-9 else float("inf")
            t_exit_b = exit_b / abs(b.speed_deg_per_day) if abs(b.speed_deg_per_day) > 1e-9 else float("inf")

            for angle in _ASPECT_ANGLES:
                orb = sep - angle
                if abs(orb) > 15.0:
                    continue  # not a "live" aspect worth reporting

                is_applying = (orb > 0 and dsep_dt < 0) or (orb < 0 and dsep_dt > 0)
                rate = abs(dsep_dt)

                is_ithasala = False
                is_isharpha = False
                days_to_exact = None

                if is_applying and rate > 1e-9:
                    days_to_exact = abs(orb) / rate
                    is_ithasala = days_to_exact < min(t_exit_a, t_exit_b)
                elif not is_applying and rate > 1e-9:
                    days_since_exact = abs(orb) / rate
                    is_isharpha = days_since_exact <= _ISHARPHA_LOOKBACK_DAYS

                aspects.append(TajikaAspect(
                    planet_a=name_a, planet_b=name_b, aspect_angle=angle,
                    current_orb_deg=round(abs(orb), 6), is_applying=is_applying,
                    is_ithasala=is_ithasala, is_isharpha=is_isharpha,
                    days_to_exact=round(days_to_exact, 6) if days_to_exact is not None else None,
                ))

        return tuple(aspects)

    @staticmethod
    def _benefic_houses_from(rashi_idx: int) -> set[int]:
        """Trine (5th/9th) + sextile (3rd/11th), 0-indexed, from a planet at `rashi_idx`."""
        return {(rashi_idx + 4) % 12, (rashi_idx + 8) % 12, (rashi_idx + 2) % 12, (rashi_idx + 10) % 12}

    @staticmethod
    def _malefic_houses_from(rashi_idx: int) -> set[int]:
        """Square (4th/10th) + opposition (7th) + conjunction (own sign), 0-indexed."""
        return {(rashi_idx + 3) % 12, (rashi_idx + 9) % 12, (rashi_idx + 6) % 12, rashi_idx}

    @classmethod
    def _compute_year_lord(cls, natal_asc_rashi: str, muntha: MunthaInfo, varsha_chart) -> YearLordInfo:
        positions = {p.planet: p for p in varsha_chart.planet_positions}
        varsha_lagna_idx = _RASHI_LIST.index(varsha_chart.ascendant.rashi)
        natal_asc_idx = _RASHI_LIST.index(natal_asc_rashi)
        is_day = bool(varsha_chart.is_daytime_birth)

        luminary = "sun" if is_day else "moon"
        luminary_rashi_idx = _RASHI_LIST.index(positions[luminary].rashi)

        tri_rasi_table = _TRI_RASI_DAY_LORDS if is_day else _TRI_RASI_NIGHT_LORDS
        tri_rasi_lord = _TRI_RASI_PLANET_ORDER[tri_rasi_table[varsha_lagna_idx]]

        raw_candidates = [
            SIGN_LORDS[_RASHI_LIST[luminary_rashi_idx]],
            SIGN_LORDS[_RASHI_LIST[natal_asc_idx]],
            SIGN_LORDS[_RASHI_LIST[muntha.rashi_index]],
            SIGN_LORDS[_RASHI_LIST[varsha_lagna_idx]],
            tri_rasi_lord,
        ]
        candidates: list[str] = []
        for c in raw_candidates:
            if c not in candidates:
                candidates.append(c)

        def candidate_rashi_idx(planet: str) -> int:
            return _RASHI_LIST.index(positions[planet].rashi)

        benefic_shortlist = [
            c for c in candidates if varsha_lagna_idx in cls._benefic_houses_from(candidate_rashi_idx(c))
        ]
        if len(benefic_shortlist) == 1:
            return YearLordInfo(
                candidates=tuple(candidates), selected=benefic_shortlist[0],
                selection_method="benefic_aspect",
            )

        malefic_shortlist = [
            c for c in candidates if varsha_lagna_idx in cls._malefic_houses_from(candidate_rashi_idx(c))
        ]
        if len(malefic_shortlist) == 1:
            return YearLordInfo(
                candidates=tuple(candidates), selected=malefic_shortlist[0],
                selection_method="malefic_aspect",
            )

        return YearLordInfo(
            candidates=tuple(candidates), selected=candidates[0],
            selection_method="fallback_first_candidate",
        )

    @staticmethod
    def _is_c_between_b_to_a(a_long: float, b_long: float, c_long: float) -> bool:
        """
        Sweeping forward SIGN by sign from B's Rashi, is C's Rashi reached
        before A's Rashi is? Sign-level granularity, matching the classical
        rule and PyJHora's saham.py:_is_C_between_B_to_A.
        """
        a_rashi, b_rashi, c_rashi = int(a_long // 30) % 12, int(b_long // 30) % 12, int(c_long // 30) % 12
        for step in range(11):
            next_rashi = (b_rashi + step + 1) % 12
            if next_rashi == c_rashi:
                return True
            if next_rashi == a_rashi:
                return False
        return False

    @classmethod
    def _saham_longitude(cls, a_long: float, b_long: float, c_long: float) -> float:
        """A - B + C, +30° if C does not fall between B and A (sign-wise)."""
        raw = (a_long - b_long + c_long) % 360.0
        if not cls._is_c_between_b_to_a(a_long, b_long, c_long):
            raw = (raw + 30.0) % 360.0
        return raw

    @staticmethod
    def _nth_house_longitude(lagna_long: float, n: int) -> float:
        """Longitude of the start of the Nth house from Lagna (n=1 is Lagna itself)."""
        return (lagna_long + (n - 1) * 30.0) % 360.0

    @classmethod
    def _compute_sahams(cls, varsha_chart) -> tuple[SahamInfo, ...]:
        pos = {p.planet: p.sidereal_longitude for p in varsha_chart.planet_positions}
        sun, moon, mars = pos["sun"], pos["moon"], pos["mars"]
        mercury, jupiter, venus, saturn = pos["mercury"], pos["jupiter"], pos["venus"], pos["saturn"]
        lagna = varsha_chart.ascendant.sidereal_longitude
        is_day = bool(varsha_chart.is_daytime_birth)
        S = cls._saham_longitude  # noqa: N806 — local alias, this method is formula-dense

        def house_lord_long(house_num: int) -> float:
            house_rashi_idx = int(cls._nth_house_longitude(lagna, house_num) // 30) % 12
            lord = SIGN_LORDS[_RASHI_LIST[house_rashi_idx]]
            return pos[lord]

        def day_night(a_day, b_day, c_day, a_night=None, b_night=None, c_night=None):
            """A/B/C day formula, swapped A<->B for night unless night_* overrides given."""
            if is_day:
                return S(a_day, b_day, c_day)
            if a_night is not None:
                return S(a_night, b_night, c_night)
            return S(b_day, a_day, c_day)

        results: dict[str, float] = {}

        results["punya"] = day_night(moon, sun, lagna)
        results["vidya"] = day_night(sun, moon, lagna)
        results["yasas"] = day_night(jupiter, results["punya"], lagna)
        results["gaurava"] = results["yasas"]  # see module docstring: real Classical Vedic matches Yasas, not the book formula
        results["mitra"] = day_night(jupiter, results["punya"], venus)
        results["mahatmya"] = day_night(results["punya"], mars, lagna)
        results["asha"] = day_night(saturn, mars, lagna)

        lagna_rashi_idx = int(lagna // 30) % 12
        lagna_lord = SIGN_LORDS[_RASHI_LIST[lagna_rashi_idx]]
        if lagna_lord == "mars":
            # Classical exception: if Mars owns the Lagna, Samartha substitutes
            # Jupiter for the Lagna-Lord operand and inverts day/night.
            samartha_b, samartha_is_day = jupiter, not is_day
        else:
            samartha_b, samartha_is_day = pos[lagna_lord], is_day
        results["samartha"] = S(mars, samartha_b, lagna) if samartha_is_day else S(samartha_b, mars, lagna)

        results["bhratri"] = S(jupiter, saturn, lagna)  # same day & night
        results["pitri"] = day_night(saturn, sun, lagna)
        results["rajya"] = results["pitri"]
        results["matri"] = day_night(moon, venus, lagna)
        results["putra"] = day_night(jupiter, moon, lagna)
        results["jeeva"] = day_night(saturn, jupiter, lagna)
        results["karma"] = day_night(mars, mercury, lagna)
        results["roga"] = S(lagna, moon, lagna)  # A==C degenerate case: correction never applies
        results["kali"] = day_night(jupiter, mars, lagna)
        results["sastra"] = day_night(jupiter, saturn, mercury)
        results["bandhu"] = day_night(mercury, moon, lagna)

        eighth_house = cls._nth_house_longitude(lagna, 8)
        results["mrityu"] = S(eighth_house, moon, lagna)  # same day & night

        ninth_house = cls._nth_house_longitude(lagna, 9)
        results["paradesa"] = S(ninth_house, house_lord_long(9), lagna)  # same day & night

        second_house = cls._nth_house_longitude(lagna, 2)
        results["artha"] = S(second_house, house_lord_long(2), lagna)  # same day & night

        results["paradara"] = day_night(venus, sun, lagna)
        results["vanik"] = day_night(moon, mercury, lagna)

        if is_day:
            sun_sign_lord_long = pos[SIGN_LORDS[_RASHI_LIST[int(sun // 30) % 12]]]
            results["karyasiddhi"] = S(saturn, sun, sun_sign_lord_long)
        else:
            moon_sign_lord_long = pos[SIGN_LORDS[_RASHI_LIST[int(moon // 30) % 12]]]
            results["karyasiddhi"] = S(saturn, moon, moon_sign_lord_long)

        results["vivaha"] = day_night(venus, saturn, lagna)

        sixth_house = cls._nth_house_longitude(lagna, 6)
        results["santapa"] = day_night(saturn, moon, sixth_house)

        results["sraddha"] = day_night(venus, mars, lagna)
        results["preeti"] = day_night(results["sastra"], results["punya"], lagna)
        results["jadya"] = day_night(mars, saturn, mercury)
        results["vyapara"] = S(mars, saturn, lagna)  # same day & night
        results["satru"] = day_night(mars, saturn, lagna)

        cancer_15deg = 105.0  # fixed point: 15° into Cancer
        results["jalapatana"] = day_night(cancer_15deg, saturn, lagna)

        results["bandhana"] = day_night(results["punya"], saturn, lagna)

        results["apamrityu"] = day_night(eighth_house, mars, lagna)

        eleventh_house = cls._nth_house_longitude(lagna, 11)
        eleventh_lord_long = house_lord_long(11)
        if is_day:
            results["labha"] = S(eleventh_house, eleventh_lord_long, lagna)
        else:
            results["labha"] = S(eleventh_lord_long, eleventh_house, lagna)

        return tuple(
            SahamInfo(name=name, sidereal_longitude=lon, rashi=_RASHI_LIST[int(lon // 30) % 12])
            for name, lon in results.items()
        )

    @staticmethod
    def _compute_muntha(natal_asc_rashi: str, varsha_year: int, varsha_chart) -> MunthaInfo:
        natal_asc_idx = _RASHI_LIST.index(natal_asc_rashi)
        muntha_idx = (natal_asc_idx + varsha_year) % 12
        muntha_rashi = _RASHI_LIST[muntha_idx]

        varsha_lagna_idx = _RASHI_LIST.index(varsha_chart.ascendant.rashi)
        house_number = ((muntha_idx - varsha_lagna_idx) % 12) + 1

        return MunthaInfo(
            rashi=muntha_rashi, rashi_index=muntha_idx, house_number=house_number,
        )
