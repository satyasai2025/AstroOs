"""
AstroOS — Relocation Engine (Astro-Cartography / Locational Facts)

Deterministic canonical-fact producer for the Relocation / Astro-Cartography
technique family. It computes, from a birth chart and a target location, the
relocated-chart facts the relocation techniques consume:

  - relocated Ascendant / Midheaven (degree + sign)
  - relocated house of every planet (Placidus or Whole Sign)
  - angular status per planet (angular / succedent / cadent) and its orb to
    the nearest angle (angular_cusp_orb)
  - longitude-system "map line" facts per planet: distance of the planet's
    longitude to the relocated ASC / MC (asc_line_orb / mc_line_orb), whether
    the planet is within the configured line orb (line_in_orb), which axis it
    is on (asc / mc / both), its line rank (major = tight orb / minor) and
    line type (natal / paran)
  - harmonic family of the ASC / MC angle labels (9th = round multiples of 10,
    5th = 72/108/144, 7th = fractional/minutes) per the harmonic methodology
  - shortest-arc midpoints of every planet pair vs the ASC / MC axes
    (midpoint.<a>_<b>.asc_orb / .mc_orb / .in_orb)
  - in-mundo angularity (house-based) facts per planet
  - paran crossings (planet pairs simultaneously angular in mundo)
  - local-space direction facts (azimuth + cardinal direction of each planet
    from the birth location at the birth moment)
  - Vedic Atmakaraka (planet at the highest degree within its sign)

The engine NEVER interprets. It emits Facts (domain/facts.py) that the
relocation RuleDefinitions / TechniqueDefinitions consume. Missing facts are
reported by the TechniqueEngine as INSUFFICIENT_DATA, never invented here.

Orb thresholds are engine-defined constants documented below; the map-line
orb convention (natal lines ~700 mi wide near the equator) maps to an angular
line orb of LINE_ORB_DEG degrees of the planet's longitude from the angle.

Fact namespace is `relocation.*` (or a caller-supplied `prefix`, e.g.
`relocation_a.*` / `relocation_b.*` for twin-location comparisons).
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Iterable, Optional

import swisseph as swe

from apps.api.domain.facts import Fact
from apps.api.services.fact_registry import FactRegistry

# ── Engine constants (documented, deterministic) ──────────────────────────────

#: Angular orb (degrees, planet longitude vs ASC/MC) inside which a planet is
#: considered "on its map line" at the target location. Maps the source's
#: ~700-mile natal-line convention to an angular orb.
LINE_ORB_DEG = 6.0

#: Angular orb for a "major" (rank-1) line — a planet essentially on the angle.
MAJOR_LINE_ORB_DEG = 1.0

#: Bodies computed by the engine, in fixed order. Values are pyswisseph body
#: IDs; rahu/ketu are handled via the mean node.
_PLANET_IDS: dict[str, int] = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "rahu": swe.MEAN_NODE,
    "ketu": swe.MEAN_NODE,
}

#: The nine Vedic planets used for the Atmakaraka computation.
_VEDIC_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
)

_ANGULAR_HOUSES = {1, 4, 7, 10}
_SUCCEDENT_HOUSES = {2, 5, 8, 11}

_SIGN_NAMES = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)

_AZIMUTH_CARDINALS = ((315.0, 45.0, "north"), (45.0, 135.0, "east"),
                      (135.0, 225.0, "south"), (225.0, 315.0, "west"))


def _normalize(deg: float) -> float:
    return deg % 360.0


def _angular_distance(a: float, b: float) -> float:
    diff = abs(_normalize(a) - _normalize(b)) % 360.0
    return min(diff, 360.0 - diff)


def _sign_of(lon: float) -> tuple[str, float]:
    idx = int(lon / 30.0) % 12
    return _SIGN_NAMES[idx], lon % 30.0


def _shortest_midpoint(a: float, b: float) -> float:
    a, b = _normalize(a), _normalize(b)
    diff = (b - a) % 360.0
    if diff <= 180.0:
        return _normalize(a + diff / 2.0)
    return _normalize(b + (360.0 - diff) / 2.0)


def _house_of_longitude(lon: float, cusps: Iterable[float]) -> int:
    """House number (1-12) of an ecliptic longitude in Placidus cusps."""
    lon = _normalize(lon)
    c = [_normalize(x) for x in cusps]
    for i in range(12):
        c1 = c[i]
        c2 = c[(i + 1) % 12]
        if c2 < c1:
            c2 += 360.0
        if c1 <= lon < c2:
            return i + 1
        if c1 <= lon + 360.0 < c2:
            return i + 1
    return 12


def _angular_status(house: int) -> str:
    if house in _ANGULAR_HOUSES:
        return "angular"
    if house in _SUCCEDENT_HOUSES:
        return "succedent"
    return "cadent"


def _cardinal_direction(azimuth: float) -> str:
    az = azimuth % 360.0
    for start, end, name in _AZIMUTH_CARDINALS:
        if start <= az < end:
            return name
    return "north"  # 315-45 wraps; the last bucket covers it


def _harmonic_family(angle_lon: float) -> str:
    """Classify an angle's label into a harmonic family per the methodology.

    9th harmonic: the label is a round multiple of 10 (comfort).
    5th harmonic: the label is 72 / 108 / 144 (creative, playful).
    7th harmonic: the label has a minutes/fractional component (discipline).
    """
    frac = (angle_lon * 60.0) % 60.0
    value = round(angle_lon, 6)
    if value in (72.0, 108.0, 144.0):
        return "fifth"
    if frac > 1e-6:
        return "seventh"
    if round(value) % 10 == 0:
        return "ninth"
    return "none"


def _in_ninth_harmonic(lon: float, angle: float, orb: float) -> bool:
    """True if `lon` sits within `orb` of a 9th-harmonic multiple (40°) of
    `angle` — the comfort-zone relation (Moon/Venus to an angular cusp)."""
    d = _angular_distance(lon, angle)
    return min(d % 40.0, 40.0 - d % 40.0) <= orb


def _in_trine_sextile(lon: float, angle: float, orb: float) -> bool:
    """True if `lon` sits within `orb` of a trine (120°) or sextile (60°)
    of `angle` — the Sun-shine harmonic relation."""
    d = _angular_distance(lon, angle)
    return min(d % 120.0, 120.0 - d % 120.0) <= orb or (
        min(d % 60.0, 60.0 - d % 60.0) <= orb)


class RelocationEngine:
    """Stateless deterministic relocation fact producer."""

    def __init__(
        self,
        ayanamsa: str = "lahiri",
        house_system: str = "P",
        line_orb_deg: float = LINE_ORB_DEG,
        major_line_orb_deg: float = MAJOR_LINE_ORB_DEG,
    ) -> None:
        self._ayanamsa = ayanamsa
        self._house_system = house_system
        self.line_orb_deg = line_orb_deg
        self.major_line_orb_deg = major_line_orb_deg

    # ── public API ────────────────────────────────────────────────────────────

    def compute_facts(
        self,
        birth_utc: datetime,
        birth_lat: float,
        birth_lon: float,
        target_lat: float,
        target_lon: float,
        prefix: str = "relocation",
    ) -> list[Fact]:
        """Compute all relocation facts for one target location."""
        facts: list[Fact] = []

        jd_et, jd_ut = swe.utc_to_jd(
            birth_utc.year, birth_utc.month, birth_utc.day,
            birth_utc.hour, birth_utc.minute,
            birth_utc.second + birth_utc.microsecond / 1e6,
            swe.GREG_CAL,
        )

        ayanamsa = self._ayanamsa_value(jd_ut)

        # Tropical + sidereal house computations for the target location.
        t_cusps, t_ascmc = swe.houses(jd_ut, target_lat, target_lon, b"P")
        t_cusps, t_ascmc = list(t_cusps), list(t_ascmc)
        asc_t, mc_t = t_ascmc[0], t_ascmc[1]
        asc = _normalize(asc_t - ayanamsa)
        mc = _normalize(mc_t - ayanamsa)
        sid_cusps = [_normalize(c - ayanamsa) for c in t_cusps]

        # Natal house framework (same birth instant, birth place) for the
        # house-change comparison used by Relocated Chart Evaluation (R4).
        n_cusps, _n_ascmc = swe.houses(jd_ut, birth_lat, birth_lon, b"P")
        natal_asc = _normalize(_n_ascmc[0] - ayanamsa)
        natal_cusps = [_normalize(c - ayanamsa) for c in n_cusps]

        self._emit(facts, f"{prefix}.birth_latitude", birth_lat, prefix)
        self._emit(facts, f"{prefix}.birth_longitude", birth_lon, prefix)
        self._emit(facts, f"{prefix}.target_latitude", target_lat, prefix)
        self._emit(facts, f"{prefix}.target_longitude", target_lon, prefix)
        self._emit(facts, f"{prefix}.location_changed",
                   (birth_lat, birth_lon) != (target_lat, target_lon), prefix)
        self._emit(facts, f"{prefix}.coordinate_system", "longitude", prefix)
        self._emit(facts, f"{prefix}.house_system", self._house_system, prefix)
        self._emit(facts, f"{prefix}.evaluated", True, prefix)
        self._emit(facts, f"{prefix}.in_mundo.available", True, prefix)

        # Angles.
        asc_sign, asc_deg_in = _sign_of(asc)
        mc_sign, mc_deg_in = _sign_of(mc)
        self._emit(facts, f"{prefix}.ascendant.degree", round(asc, 4), prefix)
        self._emit(facts, f"{prefix}.ascendant.sign", asc_sign, prefix)
        self._emit(facts, f"{prefix}.ascendant.label", round(asc, 2), prefix)
        self._emit(facts, f"{prefix}.ascendant.harmonic_family", _harmonic_family(asc), prefix)
        self._emit(facts, f"{prefix}.midheaven.degree", round(mc, 4), prefix)
        self._emit(facts, f"{prefix}.midheaven.sign", mc_sign, prefix)
        self._emit(facts, f"{prefix}.midheaven.label", round(mc, 2), prefix)
        self._emit(facts, f"{prefix}.midheaven.harmonic_family", _harmonic_family(mc), prefix)

        # Planets (longitudes are invariant under relocation — R1).
        planets: dict[str, dict] = {}
        for name, pid in _PLANET_IDS.items():
            lon = self._planet_longitude(jd_ut, name, pid)
            if name == "ketu":
                lon = _normalize(lon + 180.0)
            house = self._relocated_house(lon, asc, sid_cusps)
            natal_house = self._relocated_house(lon, natal_asc, natal_cusps)
            planets[name] = {
                "longitude": lon,
                "house": house,
                "natal_house": natal_house,
                "angular_status": _angular_status(house),
            }

        # Line / angular / house-change aggregates.
        in_orb = [p for p, d in planets.items() if self._in_orb(d, asc, mc)]
        major = [p for p, d in planets.items() if self._min_orb(d, asc, mc) <= self.major_line_orb_deg]
        angular = [p for p, d in planets.items() if d["angular_status"] == "angular"]
        changed = [p for p, d in planets.items() if d["house"] != d["natal_house"]]

        # Paran crossings: planet pairs simultaneously angular in mundo.
        paran_pairs: list[tuple[str, str]] = []
        for i in range(len(angular)):
            for j in range(i + 1, len(angular)):
                paran_pairs.append((angular[i], angular[j]))
        paran_members = {p for pair in paran_pairs for p in pair}

        # Line type per planet (paran overrides natal).
        line_type = {name: ("paran" if name in paran_members else "natal")
                     for name in planets}

        # Within-type proximity rank: 1 = closest in-orb line of that type.
        line_rank: dict[str, int] = {name: 0 for name in planets}
        for ptype in ("natal", "paran"):
            group = sorted(
                (p for p in in_orb if line_type[p] == ptype),
                key=lambda p: self._min_orb(planets[p], asc, mc),
            )
            for idx, name in enumerate(group, start=1):
                line_rank[name] = idx

        # Emit per-planet facts (rank known only after the full pass).
        for name in planets:
            self._emit_planet(facts, prefix, name,
                              planets[name]["longitude"], planets[name]["house"],
                              planets[name]["natal_house"], asc, mc,
                              line_type[name], line_rank[name])

        self._emit(facts, f"{prefix}.lines.in_orb_count", len(in_orb), prefix)
        self._emit(facts, f"{prefix}.lines.major_count", len(major), prefix)
        self._emit(facts, f"{prefix}.lines.minor_count", len(in_orb) - len(major), prefix)
        self._emit(facts, f"{prefix}.lines.natal.count",
                   sum(1 for p in in_orb if line_type[p] == "natal"), prefix)
        self._emit(facts, f"{prefix}.lines.natal.planets", ",".join(
            sorted(p for p in in_orb if line_type[p] == "natal")), prefix)
        self._emit(facts, f"{prefix}.lines.paran.count",
                   sum(1 for p in in_orb if line_type[p] == "paran"), prefix)
        self._emit(facts, f"{prefix}.lines.paran.planets", ",".join(
            sorted(p for p in in_orb if line_type[p] == "paran")), prefix)
        self._emit(facts, f"{prefix}.lines.natal.closest",
                   next((p for p in ("sun", "moon", "mercury", "venus", "mars",
                                     "jupiter", "saturn", "uranus", "neptune",
                                     "pluto", "rahu", "ketu")
                         if line_rank.get(p, 0) == 1 and line_type[p] == "natal"), ""),
                   prefix)

        # Angular & house-change aggregates (used by Relocated Chart Evaluation).
        self._emit(facts, f"{prefix}.angular.count", len(angular), prefix)
        self._emit(facts, f"{prefix}.angular.planets", ",".join(sorted(angular)), prefix)
        self._emit(facts, f"{prefix}.house_changed.count", len(changed), prefix)
        self._emit(facts, f"{prefix}.house_changed.planets",
                   ",".join(sorted(changed)), prefix)

        # Midpoints of every planet pair vs the axes.
        names = list(_PLANET_IDS.keys())
        asc_pairs: list[str] = []
        mc_pairs: list[str] = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                mid = _shortest_midpoint(planets[a]["longitude"], planets[b]["longitude"])
                asc_orb = _angular_distance(mid, asc)
                mc_orb = _angular_distance(mid, mc)
                key = f"{prefix}.midpoint.{a}_{b}"
                self._emit(facts, f"{key}.asc_orb", round(asc_orb, 4), prefix)
                self._emit(facts, f"{key}.mc_orb", round(mc_orb, 4), prefix)
                self._emit(facts, f"{key}.in_orb", min(asc_orb, mc_orb) <= self.line_orb_deg, prefix)
                if asc_orb <= self.line_orb_deg:
                    asc_pairs.append(f"{a}-{b}")
                if mc_orb <= self.line_orb_deg:
                    mc_pairs.append(f"{a}-{b}")

        # Midpoint axis aggregates (planetary-picture / isograph evidence).
        self._emit(facts, f"{prefix}.midpoints.asc.count", len(asc_pairs), prefix)
        self._emit(facts, f"{prefix}.midpoints.asc.pairs", ",".join(sorted(asc_pairs)), prefix)
        self._emit(facts, f"{prefix}.midpoints.asc.double", len(asc_pairs) >= 2, prefix)
        self._emit(facts, f"{prefix}.midpoints.mc.count", len(mc_pairs), prefix)
        self._emit(facts, f"{prefix}.midpoints.mc.pairs", ",".join(sorted(mc_pairs)), prefix)
        self._emit(facts, f"{prefix}.midpoints.mc.double", len(mc_pairs) >= 2, prefix)

        # Paran facts.
        self._emit(facts, f"{prefix}.paran.count", len(paran_pairs), prefix)
        self._emit(facts, f"{prefix}.paran.planets", ",".join(
            sorted({p for pair in paran_pairs for p in pair})), prefix)
        for a, b in paran_pairs:
            self._emit(facts, f"{prefix}.paran.{a}_{b}.present", True, prefix)

        # Local-space directions (azimuth of each planet from the birth place).
        self._local_space(facts, prefix, jd_ut, birth_lat, birth_lon)
        self._emit(facts, f"{prefix}.local_space.count", len(_PLANET_IDS), prefix)

        # Vedic Atmakaraka (highest degree within its sign).
        atmakaraka = max(_VEDIC_PLANETS, key=lambda p: planets[p]["longitude"] % 30.0)
        self._emit(facts, f"{prefix}.atmakaraka.planet", atmakaraka, prefix)
        ad = planets[atmakaraka]
        self._emit(facts, f"{prefix}.atmakaraka.line_in_orb",
                   self._in_orb(ad, asc, mc), prefix)
        self._emit(facts, f"{prefix}.atmakaraka.angular_status",
                   ad["angular_status"], prefix)

        # Treasure-map aggregates used by the place-selection technique.
        self._emit(facts, f"{prefix}.map.comfort.in_orb",
                   any(self._in_orb(planets[p], asc, mc) for p in ("moon", "venus")), prefix)
        self._emit(facts, f"{prefix}.map.comfort.planets", ",".join(
            p for p in ("moon", "venus") if self._in_orb(planets[p], asc, mc)), prefix)
        self._emit(facts, f"{prefix}.map.career.in_orb",
                   any(self._in_orb(planets[p], asc, mc) for p in ("sun", "mars")), prefix)
        self._emit(facts, f"{prefix}.map.career.planets", ",".join(
            p for p in ("sun", "mars") if self._in_orb(planets[p], asc, mc)), prefix)
        self._emit(facts, f"{prefix}.map.risk.in_orb",
                   self._in_orb(planets["uranus"], asc, mc), prefix)

        return facts

    def build_fact_registry(
        self,
        birth_utc: datetime,
        birth_lat: float,
        birth_lon: float,
        target_lat: float,
        target_lon: float,
        prefix: str = "relocation",
    ) -> FactRegistry:
        registry = FactRegistry()
        for fact in self.compute_facts(birth_utc, birth_lat, birth_lon,
                                       target_lat, target_lon, prefix):
            registry.add_fact(fact)
        return registry

    # ── internals ─────────────────────────────────────────────────────────────

    def _ayanamsa_value(self, jd_ut: float) -> float:
        if self._ayanamsa is None or self._ayanamsa.lower() == "tropical":
            return 0.0
        from packages.shared.enums import AyanamsaSystem
        mapping = {
            AyanamsaSystem.LAHIRI.value: swe.SIDM_LAHIRI,
            AyanamsaSystem.KRISHNAMURTI.value: swe.SIDM_KRISHNAMURTI,
            AyanamsaSystem.RAMAN.value: swe.SIDM_RAMAN,
            AyanamsaSystem.YUKTESHWAR.value: swe.SIDM_YUKTESHWAR,
            AyanamsaSystem.FAGAN_BRADLEY.value: swe.SIDM_FAGAN_BRADLEY,
            AyanamsaSystem.TRUE_CHITRA.value: swe.SIDM_TRUE_CITRA,
            AyanamsaSystem.TRUE_PUSHYA.value: swe.SIDM_TRUE_PUSHYA,
        }
        sid_mode = mapping.get(self._ayanamsa.lower(), swe.SIDM_LAHIRI)
        swe.set_sid_mode(sid_mode, 0, 0)
        return swe.get_ayanamsa_ut(jd_ut)

    def _planet_longitude(self, jd_ut: float, name: str, pid: int) -> float:
        pos, _ret = swe.calc_ut(jd_ut, pid, swe.FLG_SWIEPH)
        lon = pos[0]
        if self._ayanamsa_value(jd_ut):
            # sidereal via pyswisseph's own flag; fall back to subtraction.
            pos_sid, _r = swe.calc_ut(jd_ut, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            lon = pos_sid[0]
        return _normalize(lon)

    def _relocated_house(self, lon: float, asc: float, sid_cusps: list[float]) -> int:
        if self._house_system.upper() == "W":
            asc_sign = int(asc / 30.0) % 12
            lon_sign = int(lon / 30.0) % 12
            return ((lon_sign - asc_sign) % 12) + 1
        return _house_of_longitude(lon, sid_cusps)

    def _min_orb(self, planet: dict, asc: float, mc: float) -> float:
        return min(_angular_distance(planet["longitude"], asc),
                   _angular_distance(planet["longitude"], mc))

    def _in_orb(self, planet: dict, asc: float, mc: float) -> bool:
        return self._min_orb(planet, asc, mc) <= self.line_orb_deg

    def _emit_planet(self, facts: list[Fact], prefix: str, name: str,
                     lon: float, house: int, natal_house: int,
                     asc: float, mc: float,
                     line_type: str, line_rank: int) -> None:
        asc_orb = _angular_distance(lon, asc)
        mc_orb = _angular_distance(lon, mc)
        min_orb = min(asc_orb, mc_orb)
        in_orb = min_orb <= self.line_orb_deg
        if abs(asc_orb - mc_orb) < 1e-9:
            axis = "both" if in_orb else "none"
        elif asc_orb <= mc_orb:
            axis = "asc"
        else:
            axis = "mc"

        base = f"{prefix}.planet.{name}"
        self._emit(facts, f"{base}.longitude", round(lon, 4), prefix)
        self._emit(facts, f"{base}.house", house, prefix)
        self._emit(facts, f"{base}.natal_house", natal_house, prefix)
        self._emit(facts, f"{base}.house_changed", house != natal_house, prefix)
        self._emit(facts, f"{base}.angular_status", _angular_status(house), prefix)
        self._emit(facts, f"{base}.angular_cusp_orb", round(min_orb, 4), prefix)
        self._emit(facts, f"{base}.ninth_harmonic_asc",
                   _in_ninth_harmonic(lon, asc, self.line_orb_deg), prefix)
        self._emit(facts, f"{base}.ninth_harmonic_mc",
                   _in_ninth_harmonic(lon, mc, self.line_orb_deg), prefix)
        self._emit(facts, f"{base}.ninth_harmonic_to_angle",
                   (_in_ninth_harmonic(lon, asc, self.line_orb_deg)
                    or _in_ninth_harmonic(lon, mc, self.line_orb_deg)), prefix)
        self._emit(facts, f"{base}.trine_sextile_angle",
                   (_in_trine_sextile(lon, asc, self.line_orb_deg)
                    or _in_trine_sextile(lon, mc, self.line_orb_deg)), prefix)
        self._emit(facts, f"{base}.asc_line_orb", round(asc_orb, 4), prefix)
        self._emit(facts, f"{base}.mc_line_orb", round(mc_orb, 4), prefix)
        self._emit(facts, f"{base}.asc_line_in_orb", asc_orb <= self.line_orb_deg, prefix)
        self._emit(facts, f"{base}.mc_line_in_orb", mc_orb <= self.line_orb_deg, prefix)
        self._emit(facts, f"{base}.line_in_orb", in_orb, prefix)
        self._emit(facts, f"{base}.axis", axis, prefix)
        self._emit(facts, f"{base}.line_type", line_type, prefix)
        self._emit(facts, f"{base}.line_rank", line_rank, prefix)
        self._emit(facts, f"{base}.line_frequency",
                   "major" if min_orb <= self.major_line_orb_deg else "minor", prefix)
        self._emit(facts, f"{base}.line_coordinate_system", "longitude", prefix)
        self._emit(facts, f"{base}.in_mundo_angular_status", _angular_status(house), prefix)

    def _local_space(self, facts: list[Fact], prefix: str, jd_ut: float,
                     birth_lat: float, birth_lon: float) -> None:
        lst_hours = (swe.sidtime(jd_ut) + birth_lon / 15.0) % 24.0
        lst_deg = lst_hours * 15.0
        for name, pid in _PLANET_IDS.items():
            eq, _r = swe.calc_ut(jd_ut, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
            ra, dec = eq[0], eq[1]
            az = self._azimuth(ra, dec, birth_lat, lst_deg)
            base = f"{prefix}.local_space.{name}"
            self._emit(facts, f"{base}.azimuth", round(az, 4), prefix)
            self._emit(facts, f"{base}.direction", _cardinal_direction(az), prefix)

    @staticmethod
    def _azimuth(ra: float, dec: float, lat: float, lst_deg: float) -> float:
        """Standard spherical-astronomy azimuth from RA/Dec/LST."""
        h = math.radians(lst_deg - ra)
        lat_r = math.radians(lat)
        dec_r = math.radians(dec)
        az = math.atan2(math.sin(h),
                        math.cos(h) * math.sin(lat_r) - math.tan(dec_r) * math.cos(lat_r))
        return math.degrees(az) % 360.0

    @staticmethod
    def _emit(facts: list[Fact], key: str, value, prefix: str) -> None:
        facts.append(Fact(key=key, value=value, source=f"relocation_engine:{prefix}"))
