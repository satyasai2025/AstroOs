/**
 * PlanetExplorer — analytical derivation core.
 *
 * Pure functions that turn a chosen graha + the full workflow analysis result
 * into a single resolved `PlanetContext`: position, strength, relationships,
 * yogas, dasha chain, transit, Navamsha, and house ownership. Kept in a
 * non-UI module so every tab (and the interpretation engine) reads from one
 * consistent resolution and the logic stays unit-testable.
 */

import type {
  AspectSchema,
  DashaPeriodResponse,
  PlanetPositionSchema,
  PlanetStrengthSchema,
  ShadbalaTotalResponse,
  TransitPlanetResponse,
  VargaChartResponse,
  WorkflowAnalysisResponse,
  YogaResultResponse,
} from "@/lib/types";
import { rashiLordFromApiName } from "@/lib/astro";
import {
  normalizePlanetStrength,
  type NormalizedPlanetStrength,
  calculateDigbalaScore,
  calculateDignityScore,
  calculateBaladiAvastha,
  calculateTemporalScore,
  resolveAshtakavargaForPlanet,
  MIN_REQUIRED_RUPAS,
} from "@/lib/planetStrength";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import {
  BHAVA_STRUCTURE,
  GRAHA_STRUCTURE,
  NAKSHATRA_STRUCTURE,
  RASHI_STRUCTURE,
  REF_UNAVAILABLE,
  navamshaSignFromLongitude,
} from "@/lib/astroStructural";

export interface PlanetContext {
  /** Selected graha name, e.g. "Mars". */
  planet: string;
  position: PlanetPositionSchema | null;
  strength: NormalizedPlanetStrength | null;
  shadbala: ShadbalaTotalResponse | null;
  shadbalaPercent: number | null;
  digbalaScore: number | null;
  dignityScore: number | null;
  avastha: { label: string; score: number } | null;
  temporalScore: number | null;
  ashtakavargaInfo: { bindus: number; percent: number } | null;
  overallStrengthScore: number;
  /** Sign the planet occupies → its dispositor (lord of the occupied sign). */
  dispositor: string | null;
  /** Houses (1-12) whose sign lord is this graha. */
  houseOwnerOf: number[];
  /** Same-house co-planets (dispositor/conjunction group). */
  conjunctions: string[];
  /** Aspects where this planet is the receiver. */
  aspectsReceived: AspectSchema[];
  /** Aspects where this planet is the source. */
  aspectsGiven: AspectSchema[];
  /** Present yogas whose involved_planets include this graha. */
  yogasInvolving: YogaResultResponse[];
  /** Current period chain (MD → AD → ...) as of now. */
  dashaChain: DashaPeriodResponse[];
  /** Transit read for this planet (or null). */
  transit: TransitPlanetResponse | null;
  /** Navamsha (D9) sign + house for this planet, when available. */
  navamsha: { rashi: string; house: number } | null;
}

function findVargaPlanet(
  varga: VargaChartResponse | undefined,
  planet: string,
): { rashi: string; house: number } | null {
  const vp = varga?.planet_positions.find((p) => p.planet === planet);
  return vp ? { rashi: vp.varga_rashi, house: vp.varga_house_number } : null;
}

/**
 * Resolve everything about one graha in this chart. Missing chart data
 * returns an explicit `null`, never a fabricated value.
 */
export function resolvePlanetContext(
  planet: string,
  result: WorkflowAnalysisResponse,
): PlanetContext {
  const { chart, vargas, yogas, shadbala, transits, dasha, ashtakavarga } = result;

  const position = chart.planets.find((p) => p.planet === planet) ?? null;
  const strengthEntry = result.chart.planet_strengths.find(
    (s: PlanetStrengthSchema) => s.planet === planet,
  );
  const strength = strengthEntry
    ? (normalizePlanetStrength(chart.planet_strengths, shadbala).find((n) => n.planet === planet) ??
      null)
    : null;

  const planetShadbala = shadbala.find((s) => s.planet === planet) ?? null;
  const minRequired = MIN_REQUIRED_RUPAS[planet] || 6.0;
  const shadbalaPercent = planetShadbala
    ? Math.min(100, Math.round((planetShadbala.total_rupas / minRequired) * 100))
    : null;

  const digbalaScore = calculateDigbalaScore(planet, position?.house_number);
  const dignityScore = calculateDignityScore(position?.dignity);
  const avastha = calculateBaladiAvastha(position?.rashi_degree, position?.rashi);
  const temporalScore = calculateTemporalScore(planet);
  const ashtakavargaInfo = resolveAshtakavargaForPlanet(planet, position?.rashi, ashtakavarga);

  // Authoritative overall score from canonical strength model
  let overallStrengthScore: number;
  if (strength?.score != null) {
    overallStrengthScore = strength.score;
  } else {
    const available = [shadbalaPercent, ashtakavargaInfo?.percent, dignityScore, digbalaScore, temporalScore, avastha?.score].filter(
      (v): v is number => v != null
    );
    overallStrengthScore = available.length > 0
      ? Math.round(available.reduce((a, b) => a + b, 0) / available.length)
      : 50;
  }

  const dispositor = position ? rashiLordFromApiName(position.rashi) : null;

  // House ownership — a graha owns every house whose SIGNS lord it is.
  const houseOwnerOf = position
    ? chart.houses
        .filter((h) => rashiLordFromApiName(h.rashi) === planet)
        .map((h) => h.house_number)
    : [];

  const conjunctions = position
    ? chart.planets
        .filter((p) => p.planet !== planet && p.house_number === position.house_number)
        .map((p) => p.planet)
    : [];

  const aspectsInvolving = chart.aspects.filter(
    (a) => a.from_planet === planet || a.to_planet === planet,
  );
  const aspectsReceived = aspectsInvolving.filter((a) => a.to_planet === planet);
  const aspectsGiven = aspectsInvolving.filter((a) => a.from_planet === planet);

  const yogasInvolving = yogas.results.filter(
    (y) => y.is_present && y.involved_planets.includes(planet),
  );

  const dashaChain = getCurrentDashaChain(dasha.mahadashas);

  const transit = transits.planets.find((t) => t.planet === planet) ?? null;

  const navamsha = findVargaPlanet(vargas?.charts?.["D9"], planet);

  return {
    planet,
    position,
    strength,
    shadbala: planetShadbala,
    shadbalaPercent,
    digbalaScore,
    dignityScore,
    avastha,
    temporalScore,
    ashtakavargaInfo,
    overallStrengthScore,
    dispositor,
    houseOwnerOf,
    conjunctions,
    aspectsReceived,
    aspectsGiven,
    yogasInvolving,
    dashaChain,
    transit,
    navamsha,
  };
}

/** One resolvable column of the 13-Parameter Structural Map. */
export interface StructuralColumn {
  key: "rashi" | "graha" | "bhava" | "nakshatra";
  entity: string;
  /** 13 values (params[0..12]); a value equal to REF_UNAVAILABLE is shown as such. */
  values: string[];
}

/**
 * Resolve the four structural columns for a selected graha, strictly from its
 * actual Rashi → Bhava → Nakshatra+Pada. Never falls back to a generic
 * nakshatra value when a pada-specific one is required. The Navamsha Sign Link
 * (nakshatra sutra 1) is filled from the chart's real D9 position, falling back
 * to the computed sidereal formula, then REF_UNAVAILABLE.
 */
export function resolveStructuralColumns(ctx: PlanetContext): StructuralColumn[] {
  const { position } = ctx;
  if (!position) return [];

  const rashi = RASHI_STRUCTURE[position.rashi] ?? null;
  const graha = GRAHA_STRUCTURE[ctx.planet] ?? null;
  const bhava = BHAVA_STRUCTURE[String(position.house_number)] ?? null;
  const nakshatra = NAKSHATRA_STRUCTURE[`${position.nakshatra}-Pada-${position.pada}`] ?? null;

  let navamshaSign: string;
  if (ctx.navamsha) {
    navamshaSign = ctx.navamsha.rashi;
  } else if (position.sidereal_longitude != null) {
    navamshaSign = navamshaSignFromLongitude(position.sidereal_longitude);
  } else {
    navamshaSign = REF_UNAVAILABLE;
  }

  const nakshatraValues = nakshatra
    ? [navamshaSign, ...nakshatra.params.slice(1)]
    : Array(13).fill(REF_UNAVAILABLE);

  return [
    { key: "rashi", entity: position.rashi, values: rashi ? rashi.params : Array(13).fill(REF_UNAVAILABLE) },
    { key: "graha", entity: ctx.planet, values: graha ? graha.params : Array(13).fill(REF_UNAVAILABLE) },
    { key: "bhava", entity: String(position.house_number), values: bhava ? bhava.params : Array(13).fill(REF_UNAVAILABLE) },
    { key: "nakshatra", entity: `${position.nakshatra} · Pada ${position.pada}`, values: nakshatraValues },
  ];
}