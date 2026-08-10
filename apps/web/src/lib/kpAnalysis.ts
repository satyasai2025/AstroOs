/**
 * AstroOS — KP Analysis Library
 *
 * Client-side computation layer for the KP (Krishnamurti Paddhati)
 * Analysis Center. Every value here is derived from the same immutable
 * D1 chart the backend already computes — nothing is re-calculated
 * astronomically on the client. The backend's `longitude_to_sub_lord`
 * (apps/api/services/ephemeris_wrapper.py) already stamps every planet,
 * the ascendant, and every house cusp with its Star Lord / Sub Lord /
 * Sub-Sub Lord; the Panchanga carries the weekday (Vara) lord; and the
 * dasha tree carries the currently-active period chain. This module is
 * purely the *analytical* layer on top of that real data.
 *
 * It deliberately reuses the existing house-significator grading
 * (A/B/C/D, see lib/kpSignificators.ts) rather than duplicating it, so
 * the significator logic stays in exactly one place.
 */

import {
  computeAllHouseSignificators,
  KP_EVENT_HOUSE_GROUPS,
  type HouseSignificators,
  type KPEventKey,
} from "@/lib/kpSignificators";
import { rashiLordFromApiName } from "@/lib/astro";
import type {
  D1ChartResponse,
  DashaPeriodResponse,
  DashaTreeResponse,
  PlanetPositionSchema,
} from "@/lib/types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface KPCusp {
  house_number: number;
  longitude: number;
  rashi: string;
  sign_lord: string | null;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
  /** Houses the cusp's Sub Lord (CSL) is a significator of. */
  csl_signifies: number[];
  /** All houses the cusp's Sub Lord is connected to (occupies/owns/stars). */
  csl_houses: number[];
  /** Cusps that share this cusp's Sub Lord (cuspal interlinks). */
  interlinked_cusps: number[];
}

export interface KPPlanetProfile {
  planet: string;
  rashi: string;
  house_number: number;
  rashi_house_number: number;
  longitude: number;
  sign_lord: string | null;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
  is_retrograde: boolean;
  is_combust: boolean;
  dignity: string | null;
  occupied_house: number;
  owned_houses: number[];
  star_lord_houses: number[];
  sub_lord_houses: number[];
  /** Houses this planet is a KP significator of (occupied + owned + star-connected). */
  signifies: number[];
  /** House numbers whose cusp this planet is the Sub Lord of (CSL for those cusps). */
  csl_of: number[];
}

export interface RulingPlanet {
  planet: string;
  source: string;
  priority: number;
}

export interface CSLVerdict {
  cusp: number;
  csl: string;
  csl_star_lord: string;
  csl_signifies: number[];
  required_houses: number[];
  prohibited_houses: number[];
  verdict: "STRONG" | "PARTIAL" | "WEAK";
  detail: string;
}

export interface EventPromise {
  eventKey: KPEventKey;
  label: string;
  houses: number[];
  primary_cusp: number;
  csl_verdict: CSLVerdict;
  significators: { planet: string; grade: string; housesSignified: number[] }[];
  promise: "POSITIVE" | "PARTIAL" | "WEAK";
}

export interface TimingWindow {
  eventKey: KPEventKey;
  label: string;
  significator: string;
  active_level: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface SpecialFactor {
  name: string;
  category: "CORE KP" | "EXTENDED KP" | "SUPPLEMENTARY";
  value: string;
  status: "positive" | "neutral" | "caution";
  evidence: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

export const DUSTHANA_HOUSES = [6, 8, 12];
export const KENDRA_HOUSES = [1, 4, 7, 10];
export const TRIKONA_HOUSES = [1, 5, 9];

/** Classical house lordships for natural significations (KP house meanings). */
export const HOUSE_SIGNIFICATIONS: Record<number, string> = {
  1: "Self, body, personality, life path",
  2: "Wealth, family, speech, savings",
  3: "Courage, siblings, communication, effort",
  4: "Home, mother, property, education",
  5: "Children, intelligence, creativity, romance",
  6: "Disease, debts, enemies, service",
  7: "Marriage, partnerships, spouse, business",
  8: "Longevity, occult, sudden events, inheritance",
  9: "Fortune, father, higher learning, dharma",
  10: "Career, profession, status, karma",
  11: "Gains, income, network, fulfillment",
  12: "Loss, foreign lands, isolation, expenditure",
};

/** Vara (weekday) lords — used for the day-lord ruling planet. */
export const VARA_LORDS: Record<string, string> = {
  Sunday: "Sun",
  Monday: "Moon",
  Tuesday: "Mars",
  Wednesday: "Mercury",
  Thursday: "Jupiter",
  Friday: "Venus",
  Saturday: "Saturn",
};

// ── Cusp Engine ───────────────────────────────────────────────────────────────

/**
 * Build the 12-cusp matrix. Each cusp's Star Lord / Sub Lord / Sub-Sub
 * Lord come from the chart's house cusps (computed backend-side). The
 * CSL's signified houses come from the shared significator engine.
 */
export function buildKPCusps(chart: D1ChartResponse): KPCusp[] {
  const allHouseSigs = computeAllHouseSignificators(chart);

  const cusps: KPCusp[] = chart.houses
    .slice()
    .sort((a, b) => a.house_number - b.house_number)
    .map((h) => {
      const signLord = rashiLordFromApiName(h.rashi);
      const csl = h.sub_lord || "";
      const cslSignifies = csl
        ? allHouseSigs
            .filter((hs) => hs.significators.some((s) => s.planet === csl))
            .map((hs) => hs.houseNumber)
        : [];
      return {
        house_number: h.house_number,
        longitude: h.sidereal_longitude,
        rashi: h.rashi,
        sign_lord: signLord,
        star_lord: h.nakshatra_lord,
        sub_lord: h.sub_lord,
        sub_sub_lord: h.sub_sub_lord,
        csl_signifies: cslSignifies,
        csl_houses: cslSignifies,
        interlinked_cusps: [],
      };
    });

  // Cuspal interlinks — cusps that share the same Sub Lord.
  for (const c of cusps) {
    if (!c.sub_lord) continue;
    c.interlinked_cusps = cusps
      .filter((o) => o.house_number !== c.house_number && o.sub_lord === c.sub_lord)
      .map((o) => o.house_number);
  }

  return cusps;
}

// ── Planet KP Profile Engine ──────────────────────────────────────────────────

/**
 * Build a reusable KP profile for every planet (9 bodies incl. Rahu/Ketu).
 * Owned houses come from the sign-lord mapping; star/sub-lord connected
 * houses come from cusps whose Star/Sub Lord equals this planet.
 */
export function buildKPPlanetProfiles(chart: D1ChartResponse): KPPlanetProfile[] {
  const cusps = buildKPCusps(chart);

  return chart.planets.map((p) => {
    const signLord = rashiLordFromApiName(p.rashi);
    const ownedHouses = cusps
      .filter((c) => c.sign_lord === p.planet)
      .map((c) => c.house_number);
    const starLordHouses = cusps
      .filter((c) => c.star_lord === p.planet)
      .map((c) => c.house_number);
    const subLordHouses = cusps
      .filter((c) => c.sub_lord === p.planet)
      .map((c) => c.house_number);

    const signifies = Array.from(
      new Set([p.house_number, ...ownedHouses, ...starLordHouses]),
    ).sort((a, b) => a - b);

    return {
      planet: p.planet,
      rashi: p.rashi,
      house_number: p.house_number,
      rashi_house_number: p.rashi_house_number || p.house_number,
      longitude: p.sidereal_longitude,
      sign_lord: signLord,
      star_lord: p.nakshatra_lord,
      sub_lord: p.sub_lord,
      sub_sub_lord: p.sub_sub_lord,
      is_retrograde: p.is_retrograde,
      is_combust: p.is_combust,
      dignity: p.dignity,
      occupied_house: p.house_number,
      owned_houses: ownedHouses,
      star_lord_houses: starLordHouses,
      sub_lord_houses: subLordHouses,
      signifies,
      csl_of: cusps.filter((c) => c.sub_lord === p.planet).map((c) => c.house_number),
    };
  });
}

// ── Significator access (reuses lib/kpSignificators.ts) ──────────────────────

export function getHouseSignificators(
  chart: D1ChartResponse,
): HouseSignificators[] {
  return computeAllHouseSignificators(chart);
}

// ── Ruling Planet Engine ──────────────────────────────────────────────────────

/**
 * Ruling Planets (RP) from the natal moment: Lagna sign lord, Lagna Star
 * Lord, Lagna Sub Lord, Moon sign lord, Moon Star Lord, Moon Sub Lord,
 * and the weekday (Vara) lord from the Panchanga. Deduplicated, with
 * source labels and a priority (founder's ordering: Lagna → Moon → Day).
 */
export function computeRulingPlanets(chart: D1ChartResponse): RulingPlanet[] {
  const asc = chart.ascendant;
  const moon = chart.planets.find((p) => p.planet === "Moon");
  const dayLord = VARA_LORDS[chart.panchanga.vara.name] ?? chart.panchanga.vara.lord;

  const candidates: RulingPlanet[] = [
    { planet: rashiLordFromApiName(asc.rashi) ?? "", source: "Lagna Sign Lord", priority: 1 },
    { planet: asc.nakshatra_lord, source: "Lagna Star Lord", priority: 2 },
    { planet: asc.sub_lord, source: "Lagna Sub Lord", priority: 3 },
    { planet: rashiLordFromApiName(moon?.rashi) ?? "", source: "Moon Sign Lord", priority: 4 },
    { planet: moon?.nakshatra_lord ?? "", source: "Moon Star Lord", priority: 5 },
    { planet: moon?.sub_lord ?? "", source: "Moon Sub Lord", priority: 6 },
    { planet: dayLord, source: "Day (Vara) Lord", priority: 7 },
  ];

  const seen = new Set<string>();
  return candidates.filter((c) => {
    if (!c.planet || seen.has(c.planet)) return false;
    seen.add(c.planet);
    return true;
  });
}

/**
 * Fruitful significators — the intersection of Ruling Planets and the
 * significators of a set of houses. A planet that is both an RP and a
 * house significator is classically read as the strongest candidate for
 * that house's matters.
 */
export function computeFruitfulSignificators(
  chart: D1ChartResponse,
  houses: number[],
): { planet: string; rpSource: string; housesSignified: number[] }[] {
  const rps = computeRulingPlanets(chart);
  const allHouseSigs = computeAllHouseSignificators(chart);

  const perPlanet = new Map<string, { rpSource: string; housesSignified: number[] }>();
  for (const houseNumber of houses) {
    const hs = allHouseSigs.find((h) => h.houseNumber === houseNumber);
    if (!hs) continue;
    for (const sig of hs.significators) {
      const entry = perPlanet.get(sig.planet) ?? { rpSource: "", housesSignified: [] };
      entry.housesSignified.push(houseNumber);
      perPlanet.set(sig.planet, entry);
    }
  }

  const fruitful: { planet: string; rpSource: string; housesSignified: number[] }[] = [];
  for (const rp of rps) {
    const sig = perPlanet.get(rp.planet);
    if (sig) {
      fruitful.push({
        planet: rp.planet,
        rpSource: rp.source,
        housesSignified: sig.housesSignified,
      });
    }
  }
  return fruitful;
}

// ── CSL Decision Engine ───────────────────────────────────────────────────────

/**
 * CSL verdict for one cusp: how strongly the cusp's Sub Lord (CSL) ties
 * to a set of required houses (and whether it also pulls in prohibited
 * houses). STRONG = CSL signifies every required house; PARTIAL = some;
 * WEAK = none.
 */
export function evaluateCuspCSL(
  chart: D1ChartResponse,
  cuspNumber: number,
  requiredHouses: number[],
  prohibitedHouses: number[] = DUSTHANA_HOUSES,
): CSLVerdict {
  const cusps = buildKPCusps(chart);
  const cusp = cusps.find((c) => c.house_number === cuspNumber);
  if (!cusp) {
    return {
      cusp: cuspNumber,
      csl: "",
      csl_star_lord: "",
      csl_signifies: [],
      required_houses: requiredHouses,
      prohibited_houses: prohibitedHouses,
      verdict: "WEAK",
      detail: "Cusp not found in chart.",
    };
  }

  const csl = cusp.sub_lord;
  const cslPlanet = chart.planets.find((p) => p.planet === csl);
  const cslStarLord = cslPlanet?.nakshatra_lord ?? "";

  const matched = requiredHouses.filter((h) => cusp.csl_signifies.includes(h));
  const violated = prohibitedHouses.filter((h) => cusp.csl_signifies.includes(h));

  const verdict: CSLVerdict["verdict"] =
    matched.length === requiredHouses.length
      ? "STRONG"
      : matched.length > 0
        ? "PARTIAL"
        : "WEAK";

  const detail =
    `${csl || "—"} (Star Lord: ${cslStarLord || "—"}) signifies ${matched.length ? matched.join(", ") : "no"} ` +
    `of the required house(s) [${requiredHouses.join(", ")}]` +
    (violated.length
      ? `, but also signifies dusthana house(s) [${violated.join(", ")}] — a caution flag.`
      : ".");

  return {
    cusp: cuspNumber,
    csl,
    csl_star_lord: cslStarLord,
    csl_signifies: cusp.csl_signifies,
    required_houses: requiredHouses,
    prohibited_houses: prohibitedHouses,
    verdict,
    detail,
  };
}

// ── Event Engine ──────────────────────────────────────────────────────────────

/** The primary cusp each event is classically read from. */
export const EVENT_PRIMARY_CUSP: Record<KPEventKey, number> = {
  marriage: 7,
  career: 10,
  childbirth: 5,
  disease: 6,
};

/**
 * Full event promise: CSL verdict on the event's primary cusp, plus the
 * ranked significator list for the event's house group.
 */
export function computeEventPromise(
  chart: D1ChartResponse,
  eventKey: KPEventKey,
): EventPromise {
  const group = KP_EVENT_HOUSE_GROUPS[eventKey];
  const primaryCusp = EVENT_PRIMARY_CUSP[eventKey];

  const cslVerdict = evaluateCuspCSL(chart, primaryCusp, group.houses);

  const allHouseSigs = computeAllHouseSignificators(chart);
  const perPlanet = new Map<string, { housesSignified: number[]; grades: string[] }>();
  for (const houseNumber of group.houses) {
    const hs = allHouseSigs.find((h) => h.houseNumber === houseNumber);
    if (!hs) continue;
    for (const sig of hs.significators) {
      const entry = perPlanet.get(sig.planet) ?? { housesSignified: [], grades: [] };
      entry.housesSignified.push(houseNumber);
      entry.grades.push(...sig.grades);
      perPlanet.set(sig.planet, entry);
    }
  }

  const significators = Array.from(perPlanet.entries())
    .map(([planet, v]) => ({
      planet,
      grade: v.grades.sort().join("/") || "—",
      housesSignified: v.housesSignified,
    }))
    .sort(
      (a, b) =>
        b.housesSignified.length - a.housesSignified.length ||
        b.grade.localeCompare(a.grade),
    );

  const promise: EventPromise["promise"] =
    cslVerdict.verdict === "STRONG"
      ? "POSITIVE"
      : cslVerdict.verdict === "PARTIAL"
        ? "PARTIAL"
        : "WEAK";

  return { eventKey, label: group.label, houses: group.houses, primary_cusp: primaryCusp, csl_verdict: cslVerdict, significators, promise };
}

// ── Timing Engine ─────────────────────────────────────────────────────────────

/**
 * KP timing windows: for each event, whether any of its strongest
 * significators' own Dasha/Bhukti period is running today (real data
 * from the chart's dasha tree — the same `getCurrentDashaChain` the
 * Prediction Chain Explorer uses).
 */
export function computeTimingWindows(
  chart: D1ChartResponse,
  dasha: DashaTreeResponse,
): TimingWindow[] {
  const now = Date.now();

  function activeLevelFor(planet: string): { level: string; start: string; end: string } | null {
    let candidates: DashaPeriodResponse[] | undefined = dasha.mahadashas;
    const levels = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"];
    let depth = 0;
    while (candidates && candidates.length > 0) {
      const active: DashaPeriodResponse | undefined = candidates.find((p) => {
        const start = new Date(p.start_date).getTime();
        const end = new Date(p.end_date).getTime();
        return now >= start && now <= end;
      });
      if (!active) break;
      if (active.lord === planet) {
        return { level: levels[depth] ?? `Level ${depth + 1}`, start: active.start_date, end: active.end_date };
      }
      candidates = active.sub_periods;
      depth++;
    }
    return null;
  }

  const windows: TimingWindow[] = [];
  for (const eventKey of Object.keys(KP_EVENT_HOUSE_GROUPS) as KPEventKey[]) {
    const promise = computeEventPromise(chart, eventKey);
    const topSignificator = promise.significators[0];
    if (!topSignificator) continue;
    const active = activeLevelFor(topSignificator.planet);
    windows.push({
      eventKey,
      label: promise.label,
      significator: topSignificator.planet,
      active_level: active?.level ?? null,
      start_date: active?.start ?? null,
      end_date: active?.end ?? null,
    });
  }
  return windows;
}

// ── Special Factors Engine ────────────────────────────────────────────────────

/**
 * Special factors (Fortuna, retrograde, combustion, Rahu/Ketu, dusthana
 * occupancy, cuspal interlinks, sub-sub lords, etc.) classified into
 * CORE / EXTENDED / SUPPLEMENTARY so the UI can present them with honest
 * authority levels.
 */
export function computeSpecialFactors(chart: D1ChartResponse): SpecialFactor[] {
  const factors: SpecialFactor[] = [];
  const cusps = buildKPCusps(chart);

  for (const p of chart.planets) {
    if (p.is_retrograde) {
      factors.push({
        name: `${p.planet} Retrograde`,
        category: "SUPPLEMENTARY",
        value: "Retrograde",
        status: "caution",
        evidence: `${p.planet} is retrograde — its significations are read with intensified but delayed effects.`,
      });
    }
    if (p.is_combust) {
      factors.push({
        name: `${p.planet} Combust`,
        category: "SUPPLEMENTARY",
        value: "Combust",
        status: "caution",
        evidence: `${p.planet} is within combustion orb of the Sun${p.combustion_orb ? ` (${p.combustion_orb.toFixed(1)}°)` : ""} — its strength is weakened.`,
      });
    }
  }

  for (const p of chart.planets) {
    if (p.planet === "Rahu" || p.planet === "Ketu") {
      const profile = buildKPPlanetProfiles(chart).find((pp) => pp.planet === p.planet);
      factors.push({
        name: `${p.planet} Node Analysis`,
        category: "EXTENDED KP",
        value: `In ${p.rashi} (house ${p.house_number}) · Star ${p.nakshatra_lord} · Sub ${p.sub_lord}`,
        status: "neutral",
        evidence: `${p.planet} behaves like its Star Lord ${p.nakshatra_lord || "—"} and signifies house(s) ${
          profile?.signifies.length ? profile.signifies.join(", ") : "—"
        }.`,
      });
    }
  }

  for (const c of cusps) {
    if (c.interlinked_cusps.length > 0) {
      factors.push({
        name: `Cuspal Interlink ${c.house_number}↔${c.interlinked_cusps.join("/")}`,
        category: "EXTENDED KP",
        value: `Shared Sub Lord: ${c.sub_lord}`,
        status: "neutral",
        evidence: `House ${c.house_number} and house(s) ${c.interlinked_cusps.join(", ")} share Sub Lord ${
          c.sub_lord
        }, linking their significations.`,
      });
    }
  }

  const kendraOccupants = chart.planets.filter((p) => KENDRA_HOUSES.includes(p.house_number));
  if (kendraOccupants.length > 0) {
    factors.push({
      name: "Kendra Occupancy",
      category: "CORE KP",
      value: kendraOccupants.map((p) => `${p.planet} (H${p.house_number})`).join(", "),
      status: "positive",
      evidence: `${kendraOccupants.length} planet(s) in kendra houses (1/4/7/10) strengthen the chart.`,
    });
  }

  const dusthanaOccupants = chart.planets.filter((p) => DUSTHANA_HOUSES.includes(p.house_number));
  if (dusthanaOccupants.length > 0) {
    factors.push({
      name: "Dusthana Occupancy",
      category: "CORE KP",
      value: dusthanaOccupants.map((p) => `${p.planet} (H${p.house_number})`).join(", "),
      status: "caution",
      evidence: `${dusthanaOccupants.length} planet(s) occupy dusthana houses (6/8/12) — houses of loss, obstacles and expense.`,
    });
  }

  // Fortuna (classical day formula: Asc + Moon − Sun). Night births would
  // use Asc + Sun − Moon, but determining Sun altitude client-side is not
  // reliable, so we apply the standard day formula and label it honestly.
  const asc = chart.ascendant.sidereal_longitude;
  const moon = chart.planets.find((p) => p.planet === "Moon")?.sidereal_longitude ?? 0;
  const sun = chart.planets.find((p) => p.planet === "Sun")?.sidereal_longitude ?? 0;
  const fortuna = ((asc + moon - sun) % 360 + 360) % 360;
  const fortunaRashiIdx = Math.floor(fortuna / 30);
  const RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
  ];
  factors.push({
    name: "Part of Fortune",
    category: "SUPPLEMENTARY",
    value: `${fortuna.toFixed(1)}° in ${RASHI_NAMES[fortunaRashiIdx]}`,
    status: "neutral",
    evidence: "Computed by the classical day formula (Asc + Moon − Sun).",
  });

  return factors;
}
