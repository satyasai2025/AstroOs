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
 * DEFAULT WEIGHT: 10th-lord strength contributes 70% of the score, present
 * career-flavored yogas contribute up to +30 (10 points each, capped at 3
 * matches). Chosen because the 10th house (Karma Bhava) is the single most
 * classically-agreed house for career/profession, and yogas are a real
 * bonus signal but shouldn't dominate a house-lord-based score. This is a
 * documented default, not a claim of classical authority on the exact
 * split — retune CAREER_LORD_WEIGHT / CAREER_YOGA_BONUS_PER_MATCH freely.
 */
const CAREER_LORD_WEIGHT = 0.7;
const CAREER_YOGA_BONUS_PER_MATCH = 10;
const CAREER_YOGA_MAX_MATCHES = 3;

/** Case-insensitive substring keywords used to flag a present yoga as
 * "career-relevant" by scanning its category and name. Intentionally a
 * short, conservative list — false negatives (missing a relevant yoga) are
 * preferred over false positives (crediting an unrelated yoga). */
export const CAREER_YOGA_KEYWORDS = ["raja", "career", "success", "dharma-karmadhipati", "authority"];

/**
 * careerIndex — 0-100. Built from:
 *   1) the 10th house lord's strength_score (via getHouseLordStrength using
 *      chart.houses + RASHI_LORDS + chart.planet_strengths), and
 *   2) a bonus for any is_present yoga in yogas.results whose category or
 *      name matches CAREER_YOGA_KEYWORDS (case-insensitive substring).
 *
 * DEFAULT WEIGHTING — see constants above. Not a classical formula; a
 * transparent, tunable default until the founder supplies her own.
 */
export function careerIndex(result: WorkflowAnalysisResponse): number {
  const tenthLord = getHouseLordStrength(10, result.chart.houses, result.chart.planet_strengths);
  const basePercent = strengthScorePercent(tenthLord.strength) ?? 0;

  const matches = result.yogas.results.filter(
    (y) =>
      y.is_present &&
      CAREER_YOGA_KEYWORDS.some(
        (kw) => y.category.toLowerCase().includes(kw) || y.name.toLowerCase().includes(kw),
      ),
  );
  const yogaBonus = Math.min(matches.length, CAREER_YOGA_MAX_MATCHES) * CAREER_YOGA_BONUS_PER_MATCH;

  return clamp0to100(basePercent * CAREER_LORD_WEIGHT + yogaBonus);
}

// ── Marriage Index (synthesized default heuristic) ──────────────────────────

/**
 * DEFAULT WEIGHT: 7th-lord strength 50%, Venus strength 25%, Jupiter
 * strength 25%. The 7th house (Kalatra Bhava) is the classical marriage/
 * partnership house; Venus and Jupiter are the two planets most commonly
 * cited as marriage significators (Venus for spouse/romance, Jupiter for
 * marital happiness/dharma of the union) — hence a majority weight on the
 * house lord and a supporting split on the two karakas. Documented default,
 * retune MARRIAGE_* constants freely.
 */
const MARRIAGE_LORD_WEIGHT = 0.5;
const MARRIAGE_VENUS_WEIGHT = 0.25;
const MARRIAGE_JUPITER_WEIGHT = 0.25;

/**
 * marriageIndex — 0-100. Built from the 7th house lord's strength_score
 * (via getHouseLordStrength) plus Venus and Jupiter's strength_score
 * (chart.planet_strengths). DEFAULT WEIGHTING — see constants above.
 */
export function marriageIndex(result: WorkflowAnalysisResponse): number {
  const seventhLord = getHouseLordStrength(7, result.chart.houses, result.chart.planet_strengths);
  const lordPercent = strengthScorePercent(seventhLord.strength) ?? 0;
  const venusPercent = strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Venus")) ?? 0;
  const jupiterPercent =
    strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Jupiter")) ?? 0;

  return clamp0to100(
    lordPercent * MARRIAGE_LORD_WEIGHT +
      venusPercent * MARRIAGE_VENUS_WEIGHT +
      jupiterPercent * MARRIAGE_JUPITER_WEIGHT,
  );
}

// ── Wealth Potential (synthesized default heuristic) ─────────────────────────

/**
 * DEFAULT WEIGHT: 2nd-lord 30%, 11th-lord 30%, Jupiter 20%, Venus 20%. The
 * 2nd house (Dhana Bhava, accumulated wealth) and 11th house (Labha Bhava,
 * gains/income) are the two classical wealth houses, weighted equally and
 * given the majority share; Jupiter (karaka for wealth/fortune) and Venus
 * (karaka for material comforts/luxury) contribute the remainder equally.
 * Documented default, retune WEALTH_* constants freely.
 */
const WEALTH_SECOND_LORD_WEIGHT = 0.3;
const WEALTH_ELEVENTH_LORD_WEIGHT = 0.3;
const WEALTH_JUPITER_WEIGHT = 0.2;
const WEALTH_VENUS_WEIGHT = 0.2;

/**
 * wealthPotential — 0-100. Built from the 2nd and 11th house lords'
 * strength_score (via getHouseLordStrength) plus Jupiter and Venus's
 * strength_score (chart.planet_strengths). DEFAULT WEIGHTING — see
 * constants above.
 */
export function wealthPotential(result: WorkflowAnalysisResponse): number {
  const secondLord = getHouseLordStrength(2, result.chart.houses, result.chart.planet_strengths);
  const eleventhLord = getHouseLordStrength(11, result.chart.houses, result.chart.planet_strengths);
  const secondPercent = strengthScorePercent(secondLord.strength) ?? 0;
  const eleventhPercent = strengthScorePercent(eleventhLord.strength) ?? 0;
  const jupiterPercent =
    strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Jupiter")) ?? 0;
  const venusPercent = strengthScorePercent(findPlanetStrength(result.chart.planet_strengths, "Venus")) ?? 0;

  return clamp0to100(
    secondPercent * WEALTH_SECOND_LORD_WEIGHT +
      eleventhPercent * WEALTH_ELEVENTH_LORD_WEIGHT +
      jupiterPercent * WEALTH_JUPITER_WEIGHT +
      venusPercent * WEALTH_VENUS_WEIGHT,
  );
}

// ── Mental Stability (synthesized default heuristic) ─────────────────────────

/**
 * DEFAULT WEIGHT / ADJUSTMENTS: base = Moon's strength_score as a
 * percentage; +10 if exalted, +5 if in own sign, -20 if debilitated, -15 if
 * in a dusthana (6/8/12), -15 if Rahu or Ketu occupies the same house as
 * Moon (conjunction), -10 if chart.aspects records a Moon-Rahu or Moon-Ketu
 * aspect. The Moon is the universally-cited significator of mind/mentality
 * in Vedic astrology, and Rahu/Ketu are classically associated with
 * mental disturbance/obsession when afflicting the Moon — hence the
 * penalties. These are documented default point-adjustments, not a
 * calibrated classical scale; retune the MENTAL_* constants freely.
 */
const MENTAL_EXALTED_BONUS = 10;
const MENTAL_OWN_SIGN_BONUS = 5;
const MENTAL_DEBILITATED_PENALTY = -20;
const MENTAL_DUSTHANA_PENALTY = -15;
const MENTAL_RAHU_KETU_CONJUNCTION_PENALTY = -15;
const MENTAL_RAHU_KETU_ASPECT_PENALTY = -10;

/**
 * mentalStability — 0-100. Built from Moon's strength_score and dignity
 * flags (chart.planet_strengths), reduced if Moon is in a dusthana
 * (is_in_dusthana), and reduced further if Rahu/Ketu conjoin Moon (same
 * chart.planets[].house_number) or aspect Moon (chart.aspects[] entries
 * naming Moon and Rahu/Ketu in either from/to direction). DEFAULT
 * WEIGHTING — see constants above.
 */
export function mentalStability(result: WorkflowAnalysisResponse): number {
  const moonStrength = findPlanetStrength(result.chart.planet_strengths, "Moon");
  let score = strengthScorePercent(moonStrength) ?? 50; // neutral fallback if Moon data is missing

  if (moonStrength?.is_exalted) score += MENTAL_EXALTED_BONUS;
  if (moonStrength?.is_in_own_sign) score += MENTAL_OWN_SIGN_BONUS;
  if (moonStrength?.is_debilitated) score += MENTAL_DEBILITATED_PENALTY;
  if (moonStrength?.is_in_dusthana) score += MENTAL_DUSTHANA_PENALTY;

  const moonPosition = result.chart.planets.find((p) => p.planet === "Moon");
  const rahuKetuConjunct = moonPosition
    ? result.chart.planets.some(
        (p) => (p.planet === "Rahu" || p.planet === "Ketu") && p.house_number === moonPosition.house_number,
      )
    : false;
  if (rahuKetuConjunct) score += MENTAL_RAHU_KETU_CONJUNCTION_PENALTY;

  const rahuKetuAspecting = result.chart.aspects.some(
    (a) =>
      (a.from_planet === "Moon" && (a.to_planet === "Rahu" || a.to_planet === "Ketu")) ||
      (a.to_planet === "Moon" && (a.from_planet === "Rahu" || a.from_planet === "Ketu")),
  );
  if (rahuKetuAspecting) score += MENTAL_RAHU_KETU_ASPECT_PENALTY;

  return clamp0to100(score);
}

// ── Health Risk (synthesized default heuristic, returned as a label) ────────

/**
 * DEFAULT THRESHOLDS: average of the 6th house lord's and 1st house
 * (Ascendant) lord's raw strength_score (0-10 scale each). >= 7 => "Low"
 * risk, >= 4 => "Medium", below 4 => "High". The 6th house (Roga Bhava) is
 * the classical house of disease/injury, and the 1st house (Tanu Bhava)
 * represents the physical body itself — a weak lord for either is
 * classically read as a vulnerability. Returned as a LABEL rather than a
 * percentage deliberately: a risk framing implying false precision (e.g.
 * "Health Risk: 63%") is more misleading than useful for a health-adjacent
 * KPI. Documented default thresholds, retune HEALTH_RISK_* freely.
 */
const HEALTH_RISK_LOW_THRESHOLD = 7; // avg strength_score >= this => "Low"
const HEALTH_RISK_MEDIUM_THRESHOLD = 4; // avg strength_score >= this (and < LOW) => "Medium"

export type HealthRiskLabel = "Low" | "Medium" | "High" | "Unknown";

/**
 * healthRisk — a risk LABEL, not a percentage. Built from the 6th house
 * lord's and 1st house (Ascendant) lord's strength_score (via
 * getHouseLordStrength using chart.houses + RASHI_LORDS +
 * chart.planet_strengths). Higher combined weakness maps to higher risk.
 * DEFAULT THRESHOLDS — see constants above.
 */
export function healthRisk(result: WorkflowAnalysisResponse): HealthRiskLabel {
  const sixthLord = getHouseLordStrength(6, result.chart.houses, result.chart.planet_strengths);
  const firstLord = getHouseLordStrength(1, result.chart.houses, result.chart.planet_strengths);

  if (!sixthLord.strength && !firstLord.strength) return "Unknown";

  const scores = [sixthLord.strength?.strength_score, firstLord.strength?.strength_score].filter(
    (s): s is number => typeof s === "number",
  );
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length;

  if (avg >= HEALTH_RISK_LOW_THRESHOLD) return "Low";
  if (avg >= HEALTH_RISK_MEDIUM_THRESHOLD) return "Medium";
  return "High";
}
