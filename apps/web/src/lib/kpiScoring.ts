/**
 * AstroOS — Dashboard KPI Scorecard Scoring
 *
 * ASTROOS_VISION_V3_ROADMAP.md, Phase 2, splits the KPI scorecard row into
 * two very different kinds of number:
 *
 *  - Strength Score, Current Dasha, Current Transit: pulled/derived directly
 *    from existing backend fields (Shadbala/planet_strengths, dasha tree,
 *    transits) — "cheap" per the roadmap, no synthesis needed.
 *  - Career Index, Marriage Index, Wealth Potential, Mental Stability,
 *    Health Risk: the roadmap is explicit that "Nothing in the backend
 *    today computes [these] as a single number — it would need a defined
 *    formula... domain design work" that the founder had not yet supplied
 *    at the time this file was written.
 *
 * Per the roadmap's own framing (compare to how AstroSage/AstroTalk define
 * proprietary index formulas), the five synthesized indices below use
 * DOCUMENTED DEFAULT HEURISTIC WEIGHTS chosen to be defensible and
 * transparent, not a claim of classical astrological authority. Every
 * function's doc-comment states exactly which real WorkflowAnalysisResponse
 * fields feed it. Nothing here uses random numbers, hard-coded fake scores,
 * or invented backend data — every input traces back to a field already
 * present in WorkflowAnalysisResponse (apps/web/src/lib/types.ts).
 *
 * All weights/thresholds are named constants at the top of each section so
 * they're easy to retune later once the founder defines her own formulas —
 * search for "DEFAULT WEIGHT" comments to find every tunable knob.
 */

import { rashiLordFromApiName } from "@/lib/astro";
import type {
  WorkflowAnalysisResponse,
  HouseCuspSchema,
  PlanetStrengthSchema,
  DashaPeriodResponse,
} from "@/lib/types";

// ── Shared helpers ──────────────────────────────────────────────────────────

export interface HouseLordStrength {
  houseNumber: number;
  rashi: string | null;
  lord: string | null;
  strength: PlanetStrengthSchema | null;
}

/**
 * Resolve a house's ruling lord and that lord's computed strength for THIS
 * chart. Same lookup pattern as HouseDependencyNetwork.tsx: house number ->
 * chart.houses[].rashi -> RASHI_LORDS (classical, fixed) -> the lord's entry
 * in chart.planet_strengths[]. Real per-chart data only; RASHI_LORDS is the
 * one fixed classical reference table involved (which planet rules which
 * sign never changes).
 */
export function getHouseLordStrength(
  houseNumber: number,
  houses: HouseCuspSchema[],
  planetStrengths: PlanetStrengthSchema[],
): HouseLordStrength {
  const house = houses.find((h) => h.house_number === houseNumber);
  const rashi = house?.rashi ?? null;
  const lord = rashiLordFromApiName(rashi);
  const strength = lord ? (planetStrengths.find((p) => p.planet === lord) ?? null) : null;
  return { houseNumber, rashi, lord, strength };
}

/** Convert a 0-10 strength_score to a 0-100 percentage. Returns null if no
 * strength entry exists (so callers can decide on a fallback rather than
 * silently scoring a missing planet as 0). */
export function strengthScorePercent(entry: PlanetStrengthSchema | null | undefined): number | null {
  if (!entry) return null;
  return (entry.strength_score / 10) * 100;
}

function clamp0to100(n: number): number {
  return Math.round(Math.min(100, Math.max(0, n)));
}

function findPlanetStrength(
  planetStrengths: PlanetStrengthSchema[],
  planet: string,
): PlanetStrengthSchema | undefined {
  return planetStrengths.find((p) => p.planet === planet);
}

/** Classical Parashari benefic/malefic classification — same grouping used
 * server-side (apps/api/services/yoga_predicates.py's NATURAL_BENEFICS/
 * NATURAL_MALEFICS), duplicated here since this module has no dependency
 * on backend code. Mercury/Moon are classically conditional; this is the
 * same simplified static default the backend uses. */
const NATURAL_MALEFICS = new Set(["Sun", "Mars", "Saturn", "Rahu", "Ketu"]);
const NATURAL_BENEFICS = new Set(["Jupiter", "Venus", "Mercury", "Moon"]);

/** Whether `planet` is conjunct (same house_number, via planet_strengths) or
 * aspects/is-aspected-by `other` (chart.aspects, either direction). Shared
 * by the Raja Yoga check (careerIndex) and the Dhana Yoga check
 * (wealthPotential) — both are "are these two house-lords linked" checks
 * differing only in which lords they compare. */
function isLinked(result: WorkflowAnalysisResponse, planetA: string | null, planetB: string | null): boolean {
  if (!planetA || !planetB || planetA === planetB) return false;
  const a = findPlanetStrength(result.chart.planet_strengths, planetA);
  const b = findPlanetStrength(result.chart.planet_strengths, planetB);
  const conjunct = !!a && !!b && a.house_number === b.house_number;
  const aspecting = result.chart.aspects.some(
    (asp) =>
      (asp.from_planet === planetA && asp.to_planet === planetB) ||
      (asp.from_planet === planetB && asp.to_planet === planetA),
  );
  return conjunct || aspecting;
}

/** Planets occupying `houseNumber` (via chart.planet_strengths), split by
 * natural benefic/malefic — used by the 7th-house-occupancy check
 * (marriageIndex) and the 10th-house-occupancy check (careerIndex). A
 * malefic occupant only counts as afflicting if no benefic aspects it. */
function occupantsOfHouse(
  result: WorkflowAnalysisResponse,
  houseNumber: number,
): { benefics: string[]; unaspectedMalefics: string[] } {
  const occupants = result.chart.planet_strengths.filter((p) => p.house_number === houseNumber);
  const benefics = occupants.filter((p) => NATURAL_BENEFICS.has(p.planet)).map((p) => p.planet);
  const malefics = occupants.filter((p) => NATURAL_MALEFICS.has(p.planet)).map((p) => p.planet);
  const unaspectedMalefics = malefics.filter(
    (m) => !result.chart.aspects.some((asp) => NATURAL_BENEFICS.has(asp.from_planet) && asp.to_planet === m),
  );
  return { benefics, unaspectedMalefics };
}

/** Dignity swing shared by every index that scores a single house-lord's
 * strength: +10 exalted, +5 own sign, -15 debilitated, -10 combust. */
function dignitySwing(strength: PlanetStrengthSchema | null | undefined): number {
  if (!strength) return 0;
  let swing = 0;
  if (strength.is_exalted) swing += 10;
  if (strength.is_in_own_sign) swing += 5;
  if (strength.is_debilitated) swing -= 15;
  if (strength.is_combust) swing -= 10;
  return swing;
}

// ── Overall Strength Score ──────────────────────────────────────────────────

/**
 * overallStrengthScore — average of chart.planet_strengths[].strength_score
 * (each 0-10), presented as a 0-100 percentage.
 *
 * Real fields used: chart.planet_strengths[].strength_score (all 9 planets).
 * No synthesis/weighting involved — this is a direct average of a backend-
 * computed field, not a designed index.
 */
export function overallStrengthScore(result: WorkflowAnalysisResponse): number {
  const scores = result.chart.planet_strengths.map((p) => p.strength_score);
  if (scores.length === 0) return 0;
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
  return clamp0to100((avg / 10) * 100);
}

// ── Current Dasha ────────────────────────────────────────────────────────────

/**
 * Walk down the dasha tree from the mahadasha list, collecting every level
 * that is currently active (start_date/end_date brackets "now"). This is
 * the exact same "find active period" pattern already implemented as
 * getCurrentPeriodChain() in apps/web/src/components/charts/TransitTimeline.tsx
 * — duplicated here (rather than imported from a component file) so this
 * lib module has no dependency on a client component.
 */
export function getCurrentDashaChain(mahadashas: DashaPeriodResponse[]): DashaPeriodResponse[] {
  const now = Date.now();
  const chain: DashaPeriodResponse[] = [];
  let candidates = mahadashas;

  while (candidates && candidates.length > 0) {
    const active = candidates.find((p) => {
      const start = new Date(p.start_date).getTime();
      const end = new Date(p.end_date).getTime();
      return now >= start && now <= end;
    });
    if (!active) break;
    chain.push(active);
    candidates = active.sub_periods;
  }

  return chain;
}

/**
 * currentDasha — "Mahadasha / Antardasha" label for whichever periods
 * bracket today's date.
 *
 * Real fields used: dasha.mahadashas[] and their nested sub_periods[]
 * (lord/start_date/end_date), walked via getCurrentDashaChain(). No
 * synthesis — this reports exactly what the backend's dasha tree says is
 * active right now, formatted for the scorecard.
 */
export function currentDasha(result: WorkflowAnalysisResponse): string {
  const chain = getCurrentDashaChain(result.dasha.mahadashas);
  if (chain.length === 0) return "No active period found";
  const labels = chain.slice(0, 2).map((p) => p.lord);
  return labels.join(" / ");
}

// ── Current Transit ──────────────────────────────────────────────────────────

/**
 * currentTransitSummary — a short, honest one-line summary of the current
 * transit snapshot. Deliberately NOT a fabricated "Strong/Weak" verdict —
 * it reports what the backend actually flags: how many planets are
 * currently transiting a "good house" from natal Moon, plus any active
 * Sade Sati / Ashtama Shani flags (Saturn-specific classical afflictions
 * the backend already computes).
 *
 * Real fields used: transits.planets[].is_favorable_house, .is_sade_sati,
 * .is_ashtama_shani, .planet. No weighting or synthesis — a plain count
 * and flag readout.
 *
 * Fixed 2026-07-23: this previously read `.is_good_house`, a field name
 * that doesn't exist on TransitPlanetResponse (the real field is
 * `is_favorable_house`) — so withGoodHouseData was always empty and this
 * summary silently never reported the good-house count.
 */
export function currentTransitSummary(result: WorkflowAnalysisResponse): string {
  const planets = result.transits.planets;
  if (planets.length === 0) return "No transit data available";

  const withGoodHouseData = planets.filter((p) => p.is_favorable_house !== null);
  const goodCount = withGoodHouseData.filter((p) => p.is_favorable_house === true).length;
  const sadeSati = planets.filter((p) => p.is_sade_sati).map((p) => p.planet);
  const ashtamaShani = planets.filter((p) => p.is_ashtama_shani).map((p) => p.planet);

  const parts: string[] = [];
  if (withGoodHouseData.length > 0) {
    parts.push(`${goodCount}/${withGoodHouseData.length} planets in good transit houses`);
  }
  if (sadeSati.length > 0) parts.push(`Sade Sati active (${sadeSati.join(", ")})`);
  if (ashtamaShani.length > 0) parts.push(`Ashtama Shani active (${ashtamaShani.join(", ")})`);

  return parts.length > 0 ? parts.join("; ") : "No notable transit flags active";
}

// ── Career Index (synthesized default heuristic) ────────────────────────────

/**
 * DEFAULT WEIGHT: 10th-lord strength 35%, Saturn 20%, Sun 15% (70% total
 * from weighted strength), plus additive adjustments up to the remaining
 * 30 points of headroom. The 10th house (Karma Bhava) is the classical
 * career house; Saturn is the *naisargika karaka* (natural significator)
 * for profession/service/discipline in classical texts, and Sun is karaka
 * for authority/status/government — both are real significators the prior
 * version omitted entirely. Documented default, retune freely.
 */
const CAREER_LORD_WEIGHT = 0.35;
const CAREER_SATURN_WEIGHT = 0.2;
const CAREER_SUN_WEIGHT = 0.15;
const CAREER_YOGA_BONUS_PER_MATCH = 10;
const CAREER_YOGA_MAX_MATCHES = 3;
const CAREER_RAJA_YOGA_BONUS = 15;
const CAREER_MALEFIC_OCCUPANT_PENALTY = -10;

/** Case-insensitive substring keywords used to flag a present yoga as
 * "career-relevant" by scanning its category and name. Intentionally a
 * short, conservative list — false negatives (missing a relevant yoga) are
 * preferred over false positives (crediting an unrelated yoga). */
export const CAREER_YOGA_KEYWORDS = ["raja", "career", "success", "dharma-karmadhipati", "authority"];

/**
 * careerIndex — 0-100. Built from:
 *   1) 10th-lord / Saturn / Jupiter weighted strength (chart.planet_strengths),
 *   2) the 10th-lord's own dignity swing (dignitySwing),
 *   3) a bonus for any is_present yoga whose category/name matches
 *      CAREER_YOGA_KEYWORDS,
 *   4) a Kendra-Trikona Raja Yoga bonus if the 10th-lord is conjunct or
 *      aspecting the 1st, 5th, or 9th house's lord (isLinked), and
 *   5) a penalty if an unaspected natural malefic occupies the 10th house
 *      (occupantsOfHouse).
 *
 * DEFAULT WEIGHTING — see constants above. Not a classical formula; a
 * transparent, tunable default until the founder supplies her own.
 */
export function careerIndex(result: WorkflowAnalysisResponse): number {
  const tenthLord = getHouseLordStrength(10, result.chart.houses, result.chart.planet_strengths);
  const lordPercent = strengthScorePercent(tenthLord.strength) ?? 0;
  const saturnPercent = strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Saturn")) ?? 0;
  const sunPercent = strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Sun")) ?? 0;

  let score =
    lordPercent * CAREER_LORD_WEIGHT + saturnPercent * CAREER_SATURN_WEIGHT + sunPercent * CAREER_SUN_WEIGHT;
  score += dignitySwing(tenthLord.strength);

  const matches = result.yogas.results.filter(
    (y) =>
      y.is_present &&
      CAREER_YOGA_KEYWORDS.some(
        (kw) => y.category.toLowerCase().includes(kw) || y.name.toLowerCase().includes(kw),
      ),
  );
  score += Math.min(matches.length, CAREER_YOGA_MAX_MATCHES) * CAREER_YOGA_BONUS_PER_MATCH;

  const rajaYoga = [1, 5, 9].some((h) => {
    const houseLord = getHouseLordStrength(h, result.chart.houses, result.chart.planet_strengths).lord;
    return isLinked(result, tenthLord.lord, houseLord);
  });
  if (rajaYoga) score += CAREER_RAJA_YOGA_BONUS;

  if (occupantsOfHouse(result, 10).unaspectedMalefics.length > 0) score += CAREER_MALEFIC_OCCUPANT_PENALTY;

  return clamp0to100(score);
}

// ── Marriage Index (synthesized default heuristic) ──────────────────────────

/**
 * DEFAULT WEIGHT: 7th-lord strength 40%, Venus 25%, Jupiter 20%, plus
 * additive Manglik Dosha penalty and 7th-house-occupancy adjustment. The
 * 7th house (Kalatra Bhava) is the classical marriage/partnership house;
 * Venus and Jupiter are the two most-cited marriage significators. Manglik
 * (Kuja) Dosha — Mars in the 1st/4th/7th/8th/12th house counted by SIGN
 * from the Ascendant, the same classical counting the app's own Ashtakoota
 * engine uses for this exact check — was a glaring omission in the prior
 * version given how central it is to marriage-timing readings. Documented
 * default, retune MARRIAGE_* constants freely.
 */
const MARRIAGE_LORD_WEIGHT = 0.4;
const MARRIAGE_VENUS_WEIGHT = 0.25;
const MARRIAGE_JUPITER_WEIGHT = 0.2;
const MARRIAGE_MANGLIK_PENALTY = -20;
const MARRIAGE_BENEFIC_OCCUPANT_BONUS = 10;
const MARRIAGE_MALEFIC_OCCUPANT_PENALTY = -10;

const MANGLIK_HOUSES = new Set([1, 4, 7, 8, 12]);

/**
 * marriageIndex — 0-100. Built from the 7th house lord's strength_score
 * (via getHouseLordStrength) plus Venus and Jupiter's strength_score
 * (chart.planet_strengths), a Manglik Dosha penalty if Mars's
 * rashi_house_number (sign-counted from Lagna, via chart.planets — not the
 * bhava-chalit house_number on planet_strengths) falls in
 * {1,4,7,8,12}, and a 7th-house-occupancy adjustment (occupantsOfHouse).
 * DEFAULT WEIGHTING — see constants above.
 */
export function marriageIndex(result: WorkflowAnalysisResponse): number {
  const seventhLord = getHouseLordStrength(7, result.chart.houses, result.chart.planet_strengths);
  const lordPercent = strengthScorePercent(seventhLord.strength) ?? 0;
  const venusPercent = strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Venus")) ?? 0;
  const jupiterPercent =
    strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Jupiter")) ?? 0;

  let score =
    lordPercent * MARRIAGE_LORD_WEIGHT +
    venusPercent * MARRIAGE_VENUS_WEIGHT +
    jupiterPercent * MARRIAGE_JUPITER_WEIGHT;

  const mars = result.chart.planets.find((p) => p.planet === "Mars");
  if (mars && MANGLIK_HOUSES.has(mars.rashi_house_number)) score += MARRIAGE_MANGLIK_PENALTY;

  const occupants = occupantsOfHouse(result, 7);
  if (occupants.benefics.length > 0) score += MARRIAGE_BENEFIC_OCCUPANT_BONUS;
  if (occupants.unaspectedMalefics.length > 0) score += MARRIAGE_MALEFIC_OCCUPANT_PENALTY;

  return clamp0to100(score);
}

// ── Wealth Potential (synthesized default heuristic) ─────────────────────────

/**
 * DEFAULT WEIGHT: 2nd-lord 25%, 11th-lord 25%, Jupiter 20%, Venus 15%
 * (85% from weighted strength), plus an additive Dhana Yoga bonus and
 * debilitation penalties. The 2nd house (Dhana Bhava, accumulated wealth)
 * and 11th house (Labha Bhava, gains/income) are the two classical wealth
 * houses; Jupiter and Venus are wealth/comfort karakas. Dhana Yoga — the
 * 2nd and 11th lords conjunct or mutually aspecting — is a real classical
 * wealth-combination signal the prior version didn't check for at all.
 * Documented default, retune WEALTH_* constants freely.
 */
const WEALTH_SECOND_LORD_WEIGHT = 0.25;
const WEALTH_ELEVENTH_LORD_WEIGHT = 0.25;
const WEALTH_JUPITER_WEIGHT = 0.2;
const WEALTH_VENUS_WEIGHT = 0.15;
const WEALTH_DHANA_YOGA_BONUS = 15;
const WEALTH_DEBILITATION_PENALTY = -10;

/**
 * wealthPotential — 0-100. Built from the 2nd and 11th house lords'
 * strength_score (via getHouseLordStrength) plus Jupiter and Venus's
 * strength_score (chart.planet_strengths), a Dhana Yoga bonus if the 2nd
 * and 11th lords are conjunct or mutually aspecting (isLinked), and a
 * penalty for each of those two lords that is debilitated. DEFAULT
 * WEIGHTING — see constants above.
 */
export function wealthPotential(result: WorkflowAnalysisResponse): number {
  const secondLord = getHouseLordStrength(2, result.chart.houses, result.chart.planet_strengths);
  const eleventhLord = getHouseLordStrength(11, result.chart.houses, result.chart.planet_strengths);
  const secondPercent = strengthScorePercent(secondLord.strength) ?? 0;
  const eleventhPercent = strengthScorePercent(eleventhLord.strength) ?? 0;
  const jupiterPercent =
    strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Jupiter")) ?? 0;
  const venusPercent = strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Venus")) ?? 0;

  let score =
    secondPercent * WEALTH_SECOND_LORD_WEIGHT +
    eleventhPercent * WEALTH_ELEVENTH_LORD_WEIGHT +
    jupiterPercent * WEALTH_JUPITER_WEIGHT +
    venusPercent * WEALTH_VENUS_WEIGHT;

  if (isLinked(result, secondLord.lord, eleventhLord.lord)) score += WEALTH_DHANA_YOGA_BONUS;
  if (secondLord.strength?.is_debilitated) score += WEALTH_DEBILITATION_PENALTY;
  if (eleventhLord.strength?.is_debilitated) score += WEALTH_DEBILITATION_PENALTY;

  return clamp0to100(score);
}

// ── Mental Stability (synthesized default heuristic) ─────────────────────────

/**
 * DEFAULT WEIGHT / ADJUSTMENTS: base = Moon's strength_score as a
 * percentage; +10 if exalted, +5 if in own sign, -20 if debilitated, -15 if
 * in a dusthana (6/8/12), -15 if Rahu/Ketu/Saturn occupies the same house
 * as Moon (conjunction), -10 if chart.aspects records a Moon-Rahu,
 * Moon-Ketu, or Moon-Saturn aspect, and a small Paksha Bala adjustment
 * (+5 waxing / -5 waning). The Moon is the universally-cited significator
 * of mind/mentality; Rahu/Ketu are classically tied to mental disturbance/
 * obsession, and Moon-Saturn conjunction specifically is Vish Yoga — one of
 * the most-cited classical combinations for melancholy/mental distress,
 * which the prior version omitted despite checking Rahu/Ketu for the same
 * effect. These are documented default point-adjustments, not a calibrated
 * classical scale; retune the MENTAL_* constants freely.
 */
const MENTAL_EXALTED_BONUS = 10;
const MENTAL_OWN_SIGN_BONUS = 5;
const MENTAL_DEBILITATED_PENALTY = -20;
const MENTAL_DUSTHANA_PENALTY = -15;
const MENTAL_AFFLICTION_CONJUNCTION_PENALTY = -15;
const MENTAL_AFFLICTION_ASPECT_PENALTY = -10;
const MENTAL_PAKSHA_WAXING_BONUS = 5;
const MENTAL_PAKSHA_WANING_PENALTY = -5;

/** Rahu/Ketu (classical mental-disturbance significators) + Saturn (Vish
 * Yoga when conjunct Moon) — the three planets whose affliction of the
 * Moon this index penalizes. */
const MENTAL_AFFLICTING_PLANETS = new Set(["Rahu", "Ketu", "Saturn"]);

/**
 * mentalStability — 0-100. Built from Moon's strength_score and dignity
 * flags (chart.planet_strengths), reduced if Moon is in a dusthana
 * (is_in_dusthana), reduced further if Rahu/Ketu/Saturn conjoin Moon (same
 * chart.planets[].house_number) or aspect Moon (chart.aspects[] entries
 * naming Moon and one of those three in either from/to direction), and
 * adjusted by Paksha Bala (panchanga.tithi.paksha: "shukla" waxing = +5,
 * "krishna" waning = -5). DEFAULT WEIGHTING — see constants above.
 */
export function mentalStability(result: WorkflowAnalysisResponse): number {
  const moonStrength = findPlanetStrength(result.chart.planet_strengths, "Moon");
  let score = strengthScorePercent(moonStrength) ?? 50; // neutral fallback if Moon data is missing

  if (moonStrength?.is_exalted) score += MENTAL_EXALTED_BONUS;
  if (moonStrength?.is_in_own_sign) score += MENTAL_OWN_SIGN_BONUS;
  if (moonStrength?.is_debilitated) score += MENTAL_DEBILITATED_PENALTY;
  if (moonStrength?.is_in_dusthana) score += MENTAL_DUSTHANA_PENALTY;

  const moonPosition = result.chart.planets.find((p) => p.planet === "Moon");
  const afflictionConjunct = moonPosition
    ? result.chart.planets.some(
        (p) => MENTAL_AFFLICTING_PLANETS.has(p.planet) && p.house_number === moonPosition.house_number,
      )
    : false;
  if (afflictionConjunct) score += MENTAL_AFFLICTION_CONJUNCTION_PENALTY;

  const afflictionAspecting = result.chart.aspects.some(
    (a) =>
      (a.from_planet === "Moon" && MENTAL_AFFLICTING_PLANETS.has(a.to_planet)) ||
      (a.to_planet === "Moon" && MENTAL_AFFLICTING_PLANETS.has(a.from_planet)),
  );
  if (afflictionAspecting) score += MENTAL_AFFLICTION_ASPECT_PENALTY;

  const paksha = result.chart.panchanga.tithi.paksha;
  if (paksha === "shukla") score += MENTAL_PAKSHA_WAXING_BONUS;
  else if (paksha === "krishna") score += MENTAL_PAKSHA_WANING_PENALTY;

  return clamp0to100(score);
}

// ── Health Risk (synthesized default heuristic, returned as a label) ────────

/**
 * DEFAULT THRESHOLDS: weighted average of the 6th, 1st, and 8th house
 * lords' raw strength_score (0-10 scale each) — 40% 6th-lord, 40%
 * 1st-lord, 20% 8th-lord. >= 7 => "Low" risk, >= 4 => "Medium", below 4 =>
 * "High". The 6th house (Roga Bhava) is the classical house of disease/
 * injury, the 1st house (Tanu Bhava) the physical body itself, and the 8th
 * house (Ayur Bhava) longevity/chronic conditions — added here since the
 * prior version had no longevity input at all, only acute/constitutional
 * signals. A weak lord for any is classically read as a vulnerability.
 * Returned as a LABEL rather than a percentage deliberately: a risk framing
 * implying false precision (e.g. "Health Risk: 63%") is more misleading
 * than useful for a health-adjacent KPI. Documented default thresholds,
 * retune HEALTH_RISK_* freely.
 */
const HEALTH_RISK_LOW_THRESHOLD = 7; // weighted avg strength_score >= this => "Low"
const HEALTH_RISK_MEDIUM_THRESHOLD = 4; // weighted avg strength_score >= this (and < LOW) => "Medium"
const HEALTH_RISK_SIXTH_LORD_WEIGHT = 0.4;
const HEALTH_RISK_FIRST_LORD_WEIGHT = 0.4;
const HEALTH_RISK_EIGHTH_LORD_WEIGHT = 0.2;

export type HealthRiskLabel = "Low" | "Medium" | "High" | "Unknown";

/**
 * healthRisk — a risk LABEL, not a percentage. Built from the 6th, 1st
 * (Ascendant), and 8th house lords' strength_score (via
 * getHouseLordStrength using chart.houses + RASHI_LORDS +
 * chart.planet_strengths), weighted per the constants above. Higher
 * combined weakness maps to higher risk. Returns "Unknown" only if none of
 * the three lords have strength data at all.
 */
export function healthRisk(result: WorkflowAnalysisResponse): HealthRiskLabel {
  const sixthLord = getHouseLordStrength(6, result.chart.houses, result.chart.planet_strengths);
  const firstLord = getHouseLordStrength(1, result.chart.houses, result.chart.planet_strengths);
  const eighthLord = getHouseLordStrength(8, result.chart.houses, result.chart.planet_strengths);

  const candidates: Array<{ score: number | undefined; weight: number }> = [
    { score: sixthLord.strength?.strength_score, weight: HEALTH_RISK_SIXTH_LORD_WEIGHT },
    { score: firstLord.strength?.strength_score, weight: HEALTH_RISK_FIRST_LORD_WEIGHT },
    { score: eighthLord.strength?.strength_score, weight: HEALTH_RISK_EIGHTH_LORD_WEIGHT },
  ];
  const weighted = candidates.filter(
    (c): c is { score: number; weight: number } => typeof c.score === "number",
  );

  if (weighted.length === 0) return "Unknown";

  const totalWeight = weighted.reduce((sum, c) => sum + c.weight, 0);
  const avg = weighted.reduce((sum, c) => sum + c.score * c.weight, 0) / totalWeight;

  if (avg >= HEALTH_RISK_LOW_THRESHOLD) return "Low";
  if (avg >= HEALTH_RISK_MEDIUM_THRESHOLD) return "Medium";
  return "High";
}
