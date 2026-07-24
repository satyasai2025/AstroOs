/**
 * AstroOS — KP (Krishnamurti Paddhati) Significator Engine
 *
 * Built from real per-chart data only:
 *   - chart.planets[].house_number  — Bhava Chalit (cuspal) house placement
 *   - chart.planets[].nakshatra_lord — each planet's Star Lord
 *   - chart.houses[].rashi           — each house's sign, via rashiLordFromApiName()
 *     to get that sign's ruling planet (the house's Sign Lord)
 *   - chart.planets[].sub_lord       — each planet's KP Sub Lord
 *
 * Classical rules implemented (per K.S. Krishnamurti's Sub Lord theory —
 * see also ephemeris_wrapper.py's longitude_to_sub_lord for the underlying
 * Sub Lord computation):
 *
 * A house's SIGNIFICATORS are graded in four tiers, strongest to weakest:
 *   A — planets in the Nakshatra (Star) of a planet OCCUPYING the house
 *   B — planets OCCUPYING the house
 *   C — planets in the Nakshatra (Star) of the house's Sign Lord
 *   D — the house's Sign Lord itself
 * A single planet can hold more than one grade for the same house.
 *
 * Certain LIFE EVENTS are classically read off fixed house groupings (the
 * ones below are the four the founder specified — this list is
 * deliberately not exhaustive; add more only against a cited source, not
 * by guessing). A planet that signifies MORE of an event's houses, and at
 * a STRONGER grade, is a stronger candidate significator for that event.
 *
 * IMPORTANT SCOPING NOTE: classical KP also checks whether a planet's Sub
 * Lord "vetoes" a specific promised outcome by signifying the houses that
 * would negate it (e.g. the 12th-from-the-relevant-house for loss). That
 * full negation logic depends on which specific outcome is being asked
 * about and isn't implemented here — what IS implemented
 * (subLordDusthanaCheck) is a simpler, honestly-labeled heuristic: does a
 * significator's own Sub Lord ALSO signify one of the three dusthana
 * houses (6th/8th/12th, classically houses of loss/obstruction/expense)
 * in general. Treat it as a caution flag, not a full verdict.
 *
 * Ruling Planets (RP) — the Ascendant/Moon's sign+star lords and the
 * weekday lord AT THE MOMENT of a question — are deliberately not
 * included here. RP is fundamentally a horary (Prashna) concept tied to
 * the moment of judgment, not the natal chart; it belongs with the
 * Prashna chart feature when that's built, not bolted onto natal
 * analysis with a fabricated "moment."
 */

import { rashiLordFromApiName } from "@/lib/astro";
import type { D1ChartResponse, PlanetPositionSchema } from "@/lib/types";

export type SignificatorGrade = "A" | "B" | "C" | "D";

const GRADE_RANK: Record<SignificatorGrade, number> = { A: 4, B: 3, C: 2, D: 1 };

export const GRADE_LABELS: Record<SignificatorGrade, string> = {
  A: "Grade A — in the Star of a house occupant",
  B: "Grade B — occupies the house",
  C: "Grade C — in the Star of the house's Sign Lord",
  D: "Grade D — is the house's Sign Lord",
};

function strongestGrade(grades: SignificatorGrade[]): SignificatorGrade {
  return grades.reduce((best, g) => (GRADE_RANK[g] > GRADE_RANK[best] ? g : best), grades[0]);
}

export interface PlanetSignificator {
  planet: string;
  grades: SignificatorGrade[];
}

export interface HouseSignificators {
  houseNumber: number;
  rashi: string | null;
  lord: string | null;
  occupants: string[];
  /** Sorted strongest grade first. */
  significators: PlanetSignificator[];
}

/**
 * Significators for every house (1-12) of the current chart, per the
 * classical A/B/C/D grading above.
 */
export function computeAllHouseSignificators(chart: D1ChartResponse): HouseSignificators[] {
  const results: HouseSignificators[] = [];

  for (let houseNumber = 1; houseNumber <= 12; houseNumber++) {
    const houseCusp = chart.houses.find((h) => h.house_number === houseNumber);
    const rashi = houseCusp?.rashi ?? null;
    const lord = rashiLordFromApiName(rashi);
    const occupants = chart.planets
      .filter((p) => p.house_number === houseNumber)
      .map((p) => p.planet);

    const significators: PlanetSignificator[] = [];
    for (const p of chart.planets) {
      const grades: SignificatorGrade[] = [];
      if (p.nakshatra_lord && occupants.includes(p.nakshatra_lord)) grades.push("A");
      if (p.house_number === houseNumber) grades.push("B");
      if (lord && p.nakshatra_lord === lord) grades.push("C");
      if (lord && p.planet === lord) grades.push("D");
      if (grades.length > 0) significators.push({ planet: p.planet, grades });
    }

    significators.sort(
      (a, b) => GRADE_RANK[strongestGrade(b.grades)] - GRADE_RANK[strongestGrade(a.grades)],
    );

    results.push({ houseNumber, rashi, lord, occupants, significators });
  }

  return results;
}

// ── Event house groupings ────────────────────────────────────────────────────
// Deliberately only the four the founder specified. Extend only against a
// cited classical source, not by guessing plausible-looking house numbers.

export const KP_EVENT_HOUSE_GROUPS: Record<string, { label: string; houses: number[] }> = {
  marriage: { label: "Marriage", houses: [2, 7, 11] },
  career: { label: "Career / Job", houses: [2, 6, 10, 11] },
  childbirth: { label: "Childbirth", houses: [2, 5, 11] },
  disease: { label: "Disease / Problems", houses: [6, 8, 12] },
};

export type KPEventKey = keyof typeof KP_EVENT_HOUSE_GROUPS;

export interface EventSignificator {
  planet: string;
  /** Which of the event's houses this planet signifies. */
  housesSignified: number[];
  strongestGrade: SignificatorGrade;
}

export interface EventSignificatorResult {
  eventKey: KPEventKey;
  label: string;
  houses: number[];
  /** Sorted: most houses signified first, then strongest grade. */
  planets: EventSignificator[];
}

/**
 * Combined significators for one of the fixed event-house-groupings — the
 * planets most likely to "carry" that event, per classical KP's own
 * framing (a planet that signifies MORE of the group's houses, at a
 * STRONGER grade, is read as a stronger candidate).
 */
export function computeEventSignificators(
  chart: D1ChartResponse,
  eventKey: KPEventKey,
  allHouseSignificators?: HouseSignificators[],
): EventSignificatorResult {
  const group = KP_EVENT_HOUSE_GROUPS[eventKey];
  const allHouseSigs = allHouseSignificators ?? computeAllHouseSignificators(chart);

  const perPlanet = new Map<string, { housesSignified: number[]; grades: SignificatorGrade[] }>();

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

  const planets: EventSignificator[] = Array.from(perPlanet.entries()).map(([planet, v]) => ({
    planet,
    housesSignified: v.housesSignified,
    strongestGrade: strongestGrade(v.grades),
  }));

  planets.sort((a, b) => {
    if (b.housesSignified.length !== a.housesSignified.length) {
      return b.housesSignified.length - a.housesSignified.length;
    }
    return GRADE_RANK[b.strongestGrade] - GRADE_RANK[a.strongestGrade];
  });

  return { eventKey, label: group.label, houses: group.houses, planets };
}

// ── Sub Lord caution check ───────────────────────────────────────────────────

const DUSTHANA_HOUSES = [6, 8, 12];

export interface SubLordCaution {
  planet: string;
  subLord: string | null;
  /** True if the significator's own Sub Lord also signifies a dusthana
   * house (6th/8th/12th) — a simplified caution flag, see file header. */
  cautionFlag: boolean;
  dusthanaHousesSignified: number[];
}

/**
 * For a given significator planet, check whether its own Sub Lord also
 * signifies a dusthana house — see the "IMPORTANT SCOPING NOTE" in this
 * file's header for what this does and doesn't claim to determine.
 */
export function subLordDusthanaCheck(
  chart: D1ChartResponse,
  planet: string,
  allHouseSignificators?: HouseSignificators[],
): SubLordCaution | null {
  const p = chart.planets.find((pp: PlanetPositionSchema) => pp.planet === planet);
  if (!p) return null;
  const subLord = p.sub_lord || null;
  if (!subLord) {
    return { planet, subLord: null, cautionFlag: false, dusthanaHousesSignified: [] };
  }

  const allHouseSigs = allHouseSignificators ?? computeAllHouseSignificators(chart);
  const dusthanaHousesSignified = DUSTHANA_HOUSES.filter((houseNumber) =>
    allHouseSigs
      .find((hs) => hs.houseNumber === houseNumber)
      ?.significators.some((s) => s.planet === subLord),
  );

  return {
    planet,
    subLord,
    cautionFlag: dusthanaHousesSignified.length > 0,
    dusthanaHousesSignified,
  };
}
