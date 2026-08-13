/**
 * AstroOS — Shared Planet-Relationship Graph Link Builder
 *
 * Single source of truth for every real, computable planet-relationship
 * edge in a chart: classical friend/enemy (fixed), aspect/mutual-aspect,
 * dispositor, nakshatra lord, conjunction (same house), parivartana
 * (mutual sign exchange), graha yuddha (<1° orb war), yoga participation
 * (real yoga-engine output), and dasha-chain relationship (currently
 * running MD -> AD -> ... links).
 *
 * Previously duplicated across PlanetRelationshipGraph.tsx and
 * PlanetRelationshipGraph2.tsx — the second copy only computed 6 of the
 * 11 edge kinds despite its own UI (filter buttons, edge colors) already
 * declaring support for all 11. This is that missing logic, merged in.
 */

import { NATURAL_RELATIONSHIPS, rashiLordFromApiName } from "@/lib/astro";
import type {
  AspectSchema,
  DashaPeriodResponse,
  PlanetPositionSchema,
  YogaResultResponse,
} from "@/lib/types";

export type LinkKind =
  | "aspect"
  | "mutualAspect"
  | "friend"
  | "enemy"
  | "dispositor"
  | "nakshatraLord"
  | "conjunction"
  | "parivartana"
  | "yuddha"
  | "yoga"
  | "dasha";

export interface GraphLink {
  source: string;
  target: string;
  kind: LinkKind;
  label: string;
}

export const ALL_LINK_KINDS: LinkKind[] = [
  "aspect",
  "mutualAspect",
  "friend",
  "enemy",
  "dispositor",
  "nakshatraLord",
  "conjunction",
  "parivartana",
  "yuddha",
  "yoga",
  "dasha",
];

const YUDDHA_ELIGIBLE = new Set(["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]);
const YUDDHA_ORB_DEGREES = 1;

/** MD -> AD -> PD -> ... — same depth getCurrentDashaChain() walks. */
export const DASHA_LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"];

export interface BuildGraphLinksParams {
  /** Full positions, not just names — dispositor/parivartana/yuddha
   * detection needs each planet's rashi and longitude. */
  planets: PlanetPositionSchema[];
  aspects: AspectSchema[];
  /** Active/present yogas for this chart — used for Yoga Participation
   * edges. Optional; omitting it just loses that one edge kind. */
  yogas?: YogaResultResponse[];
  /** Already-resolved currently-running dasha chain (MD -> AD -> ...),
   * e.g. from getCurrentDashaChain(mahadashas). Optional; omitting it
   * just loses Dasha Relationship edges. */
  dashaChain?: { lord: string }[];
}

export function buildGraphLinks({
  planets,
  aspects,
  yogas,
  dashaChain,
}: BuildGraphLinksParams): GraphLink[] {
  const out: GraphLink[] = [];
  const planetNames = planets.map((p) => p.planet);
  const planetSet = new Set(planetNames);

  // Real aspects for this chart, split into one-way "aspect" edges and
  // "mutualAspect" edges (both planets aspect each other). Drawn once per
  // unordered pair either way (from_planet < to_planet for the mutual
  // case, to avoid double-drawing the same pair from both directions).
  const aspectPairKeys = new Set(
    aspects
      .filter((a) => planetSet.has(a.from_planet) && planetSet.has(a.to_planet) && a.from_planet !== a.to_planet)
      .map((a) => `${a.from_planet}|${a.to_planet}`),
  );
  for (const a of aspects) {
    if (!planetSet.has(a.from_planet) || !planetSet.has(a.to_planet) || a.from_planet === a.to_planet) continue;
    const isMutual = aspectPairKeys.has(`${a.to_planet}|${a.from_planet}`);
    if (isMutual) {
      if (a.from_planet < a.to_planet) {
        out.push({ source: a.from_planet, target: a.to_planet, kind: "mutualAspect", label: `Mutual Aspect (${a.aspect_type})` });
      }
    } else {
      out.push({ source: a.from_planet, target: a.to_planet, kind: "aspect", label: a.aspect_type });
    }
  }

  // Classical friend/enemy pairs, deduped (only add each unordered pair once).
  const relSeen = new Set<string>();
  for (const planet of planetNames) {
    const rel = NATURAL_RELATIONSHIPS[planet];
    if (!rel) continue;
    for (const friend of rel.friends) {
      if (!planetSet.has(friend)) continue;
      const key = [planet, friend].sort().join("|friend|");
      if (relSeen.has(key)) continue;
      relSeen.add(key);
      out.push({ source: planet, target: friend, kind: "friend", label: "Friend" });
    }
    for (const enemy of rel.enemies) {
      if (!planetSet.has(enemy)) continue;
      const key = [planet, enemy].sort().join("|enemy|");
      if (relSeen.has(key)) continue;
      relSeen.add(key);
      out.push({ source: planet, target: enemy, kind: "enemy", label: "Enemy" });
    }
  }

  // Dispositor — each planet points to the lord of the sign it occupies.
  // Only drawn when the dispositor is itself one of the displayed planets.
  const dispositorOf = new Map<string, string>();
  for (const p of planets) {
    const lord = rashiLordFromApiName(p.rashi);
    if (lord && planetSet.has(lord) && lord !== p.planet) {
      dispositorOf.set(p.planet, lord);
      out.push({ source: p.planet, target: lord, kind: "dispositor", label: `${p.planet} is disposed by ${lord}` });
    }
  }

  // Nakshatra (Star) Lord — links a planet to the ruler of the NAKSHATRA
  // it occupies (13°20' slice), distinct from Dispositor's 30° sign rule.
  for (const p of planets) {
    const starLord = p.nakshatra_lord;
    if (starLord && planetSet.has(starLord) && starLord !== p.planet) {
      out.push({ source: p.planet, target: starLord, kind: "nakshatraLord", label: `${p.planet}'s Star Lord is ${starLord}` });
    }
  }

  // Conjunction — planets sharing the same (cuspal/Chalit) house.
  const byHouse = new Map<number, string[]>();
  for (const p of planets) {
    if (!byHouse.has(p.house_number)) byHouse.set(p.house_number, []);
    byHouse.get(p.house_number)!.push(p.planet);
  }
  for (const group of byHouse.values()) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        out.push({ source: group[i], target: group[j], kind: "conjunction", label: "Conjunction (same house)" });
      }
    }
  }

  // Parivartana (mutual sign exchange) — A is disposed by B AND B is
  // disposed by A.
  const parivartanaSeen = new Set<string>();
  for (const [planet, lord] of dispositorOf) {
    if (dispositorOf.get(lord) === planet) {
      const key = [planet, lord].sort().join("|pariv|");
      if (parivartanaSeen.has(key)) continue;
      parivartanaSeen.add(key);
      out.push({ source: planet, target: lord, kind: "parivartana", label: "Parivartana (mutual exchange)" });
    }
  }

  // Graha Yuddha (planetary war) — two war-eligible grahas conjunct
  // within 1° of longitude. Computed from real sidereal_longitude.
  const yuddhaCandidates = planets.filter((p) => YUDDHA_ELIGIBLE.has(p.planet));
  for (let i = 0; i < yuddhaCandidates.length; i++) {
    for (let j = i + 1; j < yuddhaCandidates.length; j++) {
      const a = yuddhaCandidates[i];
      const b = yuddhaCandidates[j];
      const diff = Math.abs(a.sidereal_longitude - b.sidereal_longitude);
      const orb = Math.min(diff, 360 - diff);
      if (orb <= YUDDHA_ORB_DEGREES) {
        out.push({ source: a.planet, target: b.planet, kind: "yuddha", label: `Graha Yuddha (${orb.toFixed(2)}° orb)` });
      }
    }
  }

  // Yoga Participation — connect every pair of planets both named as
  // involved_planets on the SAME currently-present yoga (real yoga-engine
  // output, not inferred).
  if (yogas) {
    for (const y of yogas) {
      if (!y.is_present) continue;
      const involved = y.involved_planets.filter((p) => planetSet.has(p));
      for (let i = 0; i < involved.length; i++) {
        for (let j = i + 1; j < involved.length; j++) {
          out.push({ source: involved[i], target: involved[j], kind: "yoga", label: y.name });
        }
      }
    }
  }

  // Dasha Relationship — link consecutive levels of the dasha chain
  // that's actually running right now (MD lord -> AD lord -> ...).
  if (dashaChain && dashaChain.length > 1) {
    for (let i = 0; i < dashaChain.length - 1; i++) {
      const a = dashaChain[i].lord;
      const b = dashaChain[i + 1].lord;
      if (a !== b && planetSet.has(a) && planetSet.has(b)) {
        out.push({
          source: a,
          target: b,
          kind: "dasha",
          label: `${DASHA_LEVEL_NAMES[i] ?? "Level " + (i + 1)} (${a}) running under ${DASHA_LEVEL_NAMES[i + 1] ?? "Level " + (i + 2)} (${b})`,
        });
      }
    }
  }

  return out;
}

/** Type re-exported for callers that need the richer DashaPeriodResponse
 * shape rather than the minimal {lord} used internally above. */
export type { DashaPeriodResponse };
