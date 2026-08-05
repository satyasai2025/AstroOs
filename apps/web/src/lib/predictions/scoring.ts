/**
 * AstroOS — Prediction Chain Explorer: scoring formulas
 *
 * Every entry in PREDICTION_FACTORS below is a self-contained, versioned
 * formula that reads real fields off WorkflowAnalysisResponse (plus, for
 * Digbala/Avastha, the two extra best-effort fetches wired into
 * ChainContext). Nothing here is fabricated — see each factor's comment
 * for exactly which real fields it uses. Weight constants are documented
 * "DEFAULT WEIGHT" the same way kpiScoring.ts documents its own default
 * heuristics: a transparent, tunable default, not a claim of classical
 * authority on the exact split.
 *
 * chainEngine.ts is the only consumer of this file — it iterates
 * PREDICTION_FACTORS and turns the results into a PredictionGraph. This
 * file has no knowledge of categories totals, confidence, or the UI.
 *
 * Adding a new factor later (Argala, a specific Varga, a KP rule) means
 * appending one more object to PREDICTION_FACTORS — no other file needs
 * to change.
 */

import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { ChainContext, LifeArea, PredictionFactor } from "./types";

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}

function findPlanetStrength(ctx: ChainContext, planet: string) {
  return ctx.result.chart.planet_strengths.find((p) => p.planet === planet) ?? null;
}

// ── Karakas (fixed classical significators) per life area ──────────────────
// Venus/Jupiter for marriage (spouse + marital-happiness significators) and
// Jupiter/Venus for wealth (fortune + material-comfort significators) are
// the same karaka choices already used by kpiScoring.ts's marriageIndex()/
// wealthPotential(). Career/health rely on their house lord alone — adding
// karakas there would mean inventing a less-agreed-upon significator.
const KARAKAS_BY_AREA: Record<LifeArea, string[]> = {
  career: [],
  marriage: ["Venus", "Jupiter"],
  wealth: ["Jupiter", "Venus"],
  health: [],
  education: ["Jupiter", "Mercury"],
  children: ["Jupiter", "Venus"],
  foreign: ["Rahu", "Saturn"],
  spirituality: ["Jupiter", "Ketu"],
};

// ── 1. House Strength ────────────────────────────────────────────────────────
// DEFAULT WEIGHT: dignity/placement flags from PlanetStrengthSchema, each a
// small fixed point value. Exaltation/own-sign are classically the
// strongest positive dignities; debilitation the strongest negative;
// kendra/trikona placement is classically favorable, dusthana placement
// unfavorable — hence the signs. Not mutually exclusive; a planet can
// collect several of these at once.
const HOUSE_STRENGTH_WEIGHTS = {
  exalted: 10,
  ownSign: 6,
  debilitated: -10,
  kendra: 4,
  trikona: 4,
  dusthana: -6,
};

const houseStrengthFactor: PredictionFactor = {
  id: "house-strength",
  label: "House & Sign Strength",
  category: "House Strength",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => !!ctx.lord && !!findPlanetStrength(ctx, ctx.lord),
  compute: (ctx) => {
    const lord = ctx.lord!;
    const ps = findPlanetStrength(ctx, lord)!;
    const w = HOUSE_STRENGTH_WEIGHTS;
    let delta = 0;
    const detail: string[] = [];
    const subFactors = [
      { name: "Exalted", weight: w.exalted, present: ps.is_exalted, contribution: ps.is_exalted ? w.exalted : 0, description: "Planet in its exaltation sign" },
      { name: "Own Sign", weight: w.ownSign, present: ps.is_in_own_sign, contribution: ps.is_in_own_sign ? w.ownSign : 0, description: "Planet in its own sign" },
      { name: "Debilitated", weight: w.debilitated, present: ps.is_debilitated, contribution: ps.is_debilitated ? w.debilitated : 0, description: "Planet in debilitation" },
      { name: "Kendra", weight: w.kendra, present: ps.is_in_kendra, contribution: ps.is_in_kendra ? w.kendra : 0, description: "Angular house (1,4,7,10)" },
      { name: "Trikona", weight: w.trikona, present: ps.is_in_trikona, contribution: ps.is_in_trikona ? w.trikona : 0, description: "Trine house (1,5,9)" },
      { name: "Dusthana", weight: w.dusthana, present: ps.is_in_dusthana, contribution: ps.is_in_dusthana ? w.dusthana : 0, description: "Difficult house (6,8,12)" },
    ];
    for (const sf of subFactors) {
      delta += sf.contribution;
      if (sf.present) detail.push(`${lord} ${sf.name.toLowerCase()} — Score: ${sf.contribution >= 0 ? "+" : ""}${sf.contribution}`);
    }
    if (detail.length === 0) detail.push(`${lord} has no special dignity or angular/trinal placement for this chart`);
    const maxPossible = subFactors.reduce((sum, sf) => sum + Math.abs(sf.weight), 0);
    return {
      delta,
      inputs: { planet: lord, dignity: ps.dignity, house_number: ps.house_number },
      raw: { ...ps },
      source: [
        `chart.planet_strengths[${lord}].is_exalted`,
        `chart.planet_strengths[${lord}].is_in_own_sign`,
        `chart.planet_strengths[${lord}].is_debilitated`,
        `chart.planet_strengths[${lord}].is_in_kendra`,
        `chart.planet_strengths[${lord}].is_in_trikona`,
        `chart.planet_strengths[${lord}].is_in_dusthana`,
      ],
      detail,
      subFactors,
      maxPossible,
    };
  },
};

// ── 2. Planet Strength (Shadbala total) ──────────────────────────────────────
// DEFAULT WEIGHT: 5.0 rupas is treated as a neutral baseline (a commonly
// cited rough minimum-strength benchmark), each rupa above/below shifts the
// score by 3 points, capped at ±15. Combustion (is_combust) is a near-
// universally agreed classical weakness, hence the flat -4.
const SHADBALA_NEUTRAL_RUPAS = 5;
const SHADBALA_POINTS_PER_RUPA = 3;
const SHADBALA_MAX_POINTS = 15;
const COMBUST_PENALTY = -4;

const planetStrengthFactor: PredictionFactor = {
  id: "planet-strength",
  label: "Shadbala (Total Strength)",
  category: "Planet Strength",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => !!ctx.lord && ctx.result.shadbala.some((s) => s.planet === ctx.lord),
  compute: (ctx) => {
    const lord = ctx.lord!;
    const sb = ctx.result.shadbala.find((s) => s.planet === lord)!;
    const ps = findPlanetStrength(ctx, lord);
    const shadbalaDelta = clamp(
      (sb.total_rupas - SHADBALA_NEUTRAL_RUPAS) * SHADBALA_POINTS_PER_RUPA,
      -SHADBALA_MAX_POINTS,
      SHADBALA_MAX_POINTS,
    );
    const combustDelta = ps?.is_combust ? COMBUST_PENALTY : 0;
    const detail = [
      `${lord}'s total Shadbala is ${sb.total_rupas.toFixed(2)} rupas (baseline ${SHADBALA_NEUTRAL_RUPAS.toFixed(1)}) — Score: ${shadbalaDelta >= 0 ? "+" : ""}${shadbalaDelta.toFixed(1)}`,
    ];
    if (ps) detail.push(`Combust: ${ps.is_combust ? "yes" : "no"} — Score: ${combustDelta >= 0 ? "+" : ""}${combustDelta}`);
    const subFactors = [
      { name: "Shadbala Rupas", weight: SHADBALA_MAX_POINTS, present: true, contribution: shadbalaDelta, description: `Strength in rupas (${sb.total_rupas.toFixed(2)})` },
      { name: "Combustion", weight: Math.abs(COMBUST_PENALTY), present: ps?.is_combust ?? false, contribution: combustDelta, description: "Planet near Sun" },
    ];
    const maxPossible = SHADBALA_MAX_POINTS + Math.abs(COMBUST_PENALTY);
    return {
      delta: Math.round((shadbalaDelta + combustDelta) * 10) / 10,
      inputs: { planet: lord, total_rupas: sb.total_rupas, is_combust: ps?.is_combust ?? null },
      raw: { ...sb, is_combust: ps?.is_combust ?? null },
      source: [`chart.shadbala[${lord}].total_rupas`, `chart.planet_strengths[${lord}].is_combust`],
      detail,
      subFactors,
      maxPossible,
    };
  },
};

// ── 3. Digbala (directional strength) ────────────────────────────────────────
// DEFAULT WEIGHT: 30 shashtiamsas (half of the 60-shashtiamsa maximum) is
// the midpoint; the full 0-60 range is scaled to ±5 points around that
// midpoint. Requires the separate /api/v1/shadbala/all fetch — marked
// unavailable (not a fabricated 0) if that hasn't resolved.
const DIGBALA_MAX_SHASHTIAMSAS = 60;
const DIGBALA_MAX_POINTS = 5;

const digbalaFactor: PredictionFactor = {
  id: "digbala",
  label: "Digbala (Directional Strength)",
  category: "Planet Strength",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => !!ctx.lord && !!ctx.shadbalaAll?.phase1.dig_bala.some((c) => c.planet === ctx.lord),
  compute: (ctx) => {
    const lord = ctx.lord!;
    const comp = ctx.shadbalaAll!.phase1.dig_bala.find((c) => c.planet === lord)!;
    const midpoint = DIGBALA_MAX_SHASHTIAMSAS / 2;
    const delta = clamp(((comp.value_shashtiamsas - midpoint) / midpoint) * DIGBALA_MAX_POINTS, -DIGBALA_MAX_POINTS, DIGBALA_MAX_POINTS);
    const detail = [
      `${lord}'s Digbala is ${comp.value_shashtiamsas.toFixed(1)} shashtiamsas out of ${DIGBALA_MAX_SHASHTIAMSAS} (full directional strength) — Score: ${delta >= 0 ? "+" : ""}${delta.toFixed(1)}`,
      ...comp.trace,
    ];
    const subFactors = [
      { name: "Digbala Value", weight: DIGBALA_MAX_POINTS, present: true, contribution: delta, description: `Directional strength (${comp.value_shashtiamsas.toFixed(1)} shashtiamsas)` },
    ];
    const maxPossible = DIGBALA_MAX_POINTS;
    return {
      delta: Math.round(delta * 10) / 10,
      inputs: { planet: lord, value_shashtiamsas: comp.value_shashtiamsas },
      raw: { ...comp },
      source: [`shadbala/all.phase1.dig_bala[${lord}].value_shashtiamsas`],
      detail,
      subFactors,
      maxPossible,
    };
  },
};

// ── 4. Aspects ────────────────────────────────────────────────────────────────
// DEFAULT WEIGHT: natural benefic/malefic classification is a fixed
// classical fact (which planets are inherently benefic vs malefic), not a
// per-chart invention. Tighter orb = stronger influence, on a documented
// 3-tier scale.
const NATURAL_BENEFICS = ["Jupiter", "Venus", "Moon"];
const NATURAL_MALEFICS = ["Saturn", "Mars", "Sun", "Rahu", "Ketu"];
const ASPECT_TIGHT_ORB = 2;
const ASPECT_MODERATE_ORB = 6;
const ASPECT_WEIGHTS = { tight: 6, moderate: 3, wide: 1 };

const aspectsFactor: PredictionFactor = {
  id: "aspects",
  label: "Aspects Received",
  category: "Aspects",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => !!ctx.lord,
  compute: (ctx) => {
    const lord = ctx.lord!;
    const incoming = ctx.result.chart.aspects.filter((a) => a.to_planet === lord);
    let delta = 0;
    const detail: string[] = [];
    const source: string[] = [];
    for (const a of incoming) {
      const isBenefic = NATURAL_BENEFICS.includes(a.from_planet);
      const isMalefic = NATURAL_MALEFICS.includes(a.from_planet);
      const sign = isBenefic ? 1 : isMalefic ? -1 : 0;
      const magnitude =
        a.orb_degrees <= ASPECT_TIGHT_ORB ? ASPECT_WEIGHTS.tight : a.orb_degrees <= ASPECT_MODERATE_ORB ? ASPECT_WEIGHTS.moderate : ASPECT_WEIGHTS.wide;
      const points = sign * magnitude;
      delta += points;
      detail.push(
        `${a.from_planet} (${isBenefic ? "natural benefic" : isMalefic ? "natural malefic" : "neutral"}) aspects ${lord}, orb ${a.orb_degrees.toFixed(1)}° — Score: ${points >= 0 ? "+" : ""}${points}`,
      );
      source.push(`chart.aspects[${a.from_planet}→${a.to_planet}]`);
    }
    if (incoming.length === 0) detail.push(`No aspects onto ${lord} found in this chart`);
    const aspectSubFactors = incoming.map((a) => {
      const isBenefic = NATURAL_BENEFICS.includes(a.from_planet);
      const isMalefic = NATURAL_MALEFICS.includes(a.from_planet);
      const sign = isBenefic ? 1 : isMalefic ? -1 : 0;
      const magnitude = a.orb_degrees <= ASPECT_TIGHT_ORB ? ASPECT_WEIGHTS.tight : a.orb_degrees <= ASPECT_MODERATE_ORB ? ASPECT_WEIGHTS.moderate : ASPECT_WEIGHTS.wide;
      const points = sign * magnitude;
      return {
        name: `${a.from_planet} Aspect`,
        weight: magnitude,
        present: true,
        contribution: points,
        description: `${isBenefic ? "Benefic" : isMalefic ? "Malefic" : "Neutral"} aspect, orb ${a.orb_degrees.toFixed(1)}°`,
      };
    });
    const maxPossible = incoming.length > 0 ? Math.max(...incoming.map((a) => (a.orb_degrees <= ASPECT_TIGHT_ORB ? ASPECT_WEIGHTS.tight : a.orb_degrees <= ASPECT_MODERATE_ORB ? ASPECT_WEIGHTS.moderate : ASPECT_WEIGHTS.wide))) : 0;
    return { delta, inputs: { planet: lord, aspect_count: incoming.length }, raw: { aspects: incoming }, source, detail, subFactors: aspectSubFactors, maxPossible };
  },
};

// ── 5. Yogas ──────────────────────────────────────────────────────────────────
// DEFAULT WEIGHT: +5 per structurally-relevant present yoga, capped at 3
// matches (15 max) — relevance is a real structural match (the yoga's
// involved_houses/involved_planets actually includes this area's house or
// lord), not keyword text matching.
const YOGA_BONUS_PER_MATCH = 5;
const YOGA_MAX_MATCHES = 3;

const yogasFactor: PredictionFactor = {
  id: "yogas",
  label: "Relevant Yogas",
  category: "Yogas",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: () => true,
  compute: (ctx) => {
    const lord = ctx.lord;
    const matched = ctx.result.yogas.results.filter(
      (y) => y.is_present && (y.involved_houses.includes(ctx.houseNumber) || (lord ? y.involved_planets.includes(lord) : false)),
    );
    const counted = matched.slice(0, YOGA_MAX_MATCHES);
    const delta = counted.length * YOGA_BONUS_PER_MATCH;
    const detail =
      matched.length > 0
        ? matched.map((y, i) => `${y.name} (${y.category}) is present${i < YOGA_MAX_MATCHES ? ` — Score: +${YOGA_BONUS_PER_MATCH}` : " — beyond the counted cap, no additional score"}`)
        : [`No present yoga references house ${ctx.houseNumber} or ${lord ?? "the house lord"}`];
    const yogaSubFactors = counted.map((y) => ({
      name: y.name,
      weight: YOGA_BONUS_PER_MATCH,
      present: true,
      contribution: YOGA_BONUS_PER_MATCH,
      description: `${y.category} — Present`,
    }));
    const maxPossible = YOGA_MAX_MATCHES * YOGA_BONUS_PER_MATCH;
    return {
      delta,
      inputs: { house_number: ctx.houseNumber, planet: lord, matched_count: matched.length },
      raw: { matched },
      source: matched.map((y) => `yogas.results[${y.yoga_id}]`),
      detail,
      subFactors: yogaSubFactors,
      maxPossible,
    };
  },
};

// ── 6. Dasha Influence ───────────────────────────────────────────────────────
// DEFAULT WEIGHT: +7 if the current Mahadasha lord matches the area's house
// lord, +4 if the current Antardasha lord matches — a currently-running
// dasha of the relevant lord is classically read as "activating" that
// house's results.
const MAHADASHA_MATCH_BONUS = 7;
const ANTARDASHA_MATCH_BONUS = 4;

const dashaInfluenceFactor: PredictionFactor = {
  id: "dasha-influence",
  label: "Dasha Activation",
  category: "Dasha",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => ctx.result.dasha.mahadashas.length > 0,
  compute: (ctx) => {
    const chain = getCurrentDashaChain(ctx.result.dasha.mahadashas);
    const mahaLord = chain[0]?.lord ?? null;
    const antarLord = chain[1]?.lord ?? null;
    const lord = ctx.lord;
    const mahaMatch = !!lord && mahaLord === lord;
    const antarMatch = !!lord && antarLord === lord;
    const delta = (mahaMatch ? MAHADASHA_MATCH_BONUS : 0) + (antarMatch ? ANTARDASHA_MATCH_BONUS : 0);
    const detail = [
      `Current Mahadasha: ${mahaLord ?? "none active"}${mahaMatch ? ` — activates ${lord} — Score: +${MAHADASHA_MATCH_BONUS}` : ""}`,
      `Current Antardasha: ${antarLord ?? "none active"}${antarMatch ? ` — activates ${lord} — Score: +${ANTARDASHA_MATCH_BONUS}` : ""}`,
    ];
    const subFactors = [
      { name: "Mahadasha Match", weight: MAHADASHA_MATCH_BONUS, present: mahaMatch, contribution: mahaMatch ? MAHADASHA_MATCH_BONUS : 0, description: `Current MD: ${mahaLord ?? "none"}` },
      { name: "Antardasha Match", weight: ANTARDASHA_MATCH_BONUS, present: antarMatch, contribution: antarMatch ? ANTARDASHA_MATCH_BONUS : 0, description: `Current AD: ${antarLord ?? "none"}` },
    ];
    const maxPossible = MAHADASHA_MATCH_BONUS + ANTARDASHA_MATCH_BONUS;
    return {
      delta,
      inputs: { mahadasha_lord: mahaLord, antardasha_lord: antarLord, house_lord: lord },
      raw: { chain },
      source: ["dasha.mahadashas"],
      detail,
      subFactors,
      maxPossible,
    };
  },
};

// ── 7. Transit Influence ─────────────────────────────────────────────────────
// DEFAULT WEIGHT: the lord's current transit flags, read as-is from the
// backend's own favorable/afflicted classifications — no re-derivation.
const TRANSIT_FAVORABLE_BONUS = 4;
const TRANSIT_UNFAVORABLE_PENALTY = -2;
const SADE_SATI_PENALTY = -5;
const ASHTAMA_SHANI_PENALTY = -4;

const transitInfluenceFactor: PredictionFactor = {
  id: "transit-influence",
  label: "Current Transit",
  category: "Transit",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => !!ctx.lord && ctx.result.transits.planets.some((p) => p.planet === ctx.lord),
  compute: (ctx) => {
    const lord = ctx.lord!;
    const t = ctx.result.transits.planets.find((p) => p.planet === lord)!;
    const favDelta = t.is_favorable_house === true ? TRANSIT_FAVORABLE_BONUS : t.is_favorable_house === false ? TRANSIT_UNFAVORABLE_PENALTY : 0;
    const sadeDelta = t.is_sade_sati ? SADE_SATI_PENALTY : 0;
    const ashtamaDelta = t.is_ashtama_shani ? ASHTAMA_SHANI_PENALTY : 0;
    const detail = [
      `${lord} is transiting ${t.transit_rashi} — favorable house from Moon: ${t.is_favorable_house === null ? "unknown" : t.is_favorable_house ? "yes" : "no"} — Score: ${favDelta >= 0 ? "+" : ""}${favDelta}`,
    ];
    if (t.is_sade_sati) detail.push(`Sade Sati active — Score: ${SADE_SATI_PENALTY}`);
    if (t.is_ashtama_shani) detail.push(`Ashtama Shani active — Score: ${ASHTAMA_SHANI_PENALTY}`);
    const subFactors = [
      { name: "Favorable House", weight: TRANSIT_FAVORABLE_BONUS, present: t.is_favorable_house === true, contribution: favDelta, description: `Transiting ${t.transit_rashi}` },
      { name: "Sade Sati", weight: Math.abs(SADE_SATI_PENALTY), present: t.is_sade_sati, contribution: sadeDelta, description: "Saturn's 7.5 year cycle" },
      { name: "Ashtama Shani", weight: Math.abs(ASHTAMA_SHANI_PENALTY), present: t.is_ashtama_shani, contribution: ashtamaDelta, description: "Saturn in 8th house from Moon" },
    ];
    const maxPossible = TRANSIT_FAVORABLE_BONUS + Math.abs(SADE_SATI_PENALTY) + Math.abs(ASHTAMA_SHANI_PENALTY);
    return {
      delta: favDelta + sadeDelta + ashtamaDelta,
      inputs: { planet: lord, is_favorable_house: t.is_favorable_house, is_sade_sati: t.is_sade_sati, is_ashtama_shani: t.is_ashtama_shani },
      raw: { ...t },
      source: [`transits.planets[${lord}].is_favorable_house`, `transits.planets[${lord}].is_sade_sati`, `transits.planets[${lord}].is_ashtama_shani`],
      detail,
      subFactors,
      maxPossible,
    };
  },
};

// ── 8. Avastha (Deeptadi dignity-state) ──────────────────────────────────────
// DEFAULT WEIGHT: Deeptadi (dignity-based) avastha mapped to a small
// documented scale, from most auspicious (Deepta) to least (Kopa). Baladi
// (age-based) avastha is shown as an informational line only — no
// established scoring convention exists for it in this codebase, so it
// isn't scored rather than inventing one.
const DEEPTADI_POINTS: Record<string, number> = {
  Deepta: 3,
  Swastha: 2,
  Pramudita: 1,
  Shanta: 0,
  Sama: 0,
  Dukhita: -1,
  Vikala: -2,
  Kopa: -3,
};

const avasthaFactor: PredictionFactor = {
  id: "avastha",
  label: "Avastha (Planetary State)",
  category: "Avastha",
  formulaVersion: "v1",
  appliesTo: () => true,
  isAvailable: (ctx) => !!ctx.lord && !!ctx.avastha?.avasthas.some((a) => a.planet === ctx.lord),
  compute: (ctx) => {
    const lord = ctx.lord!;
    const a = ctx.avastha!.avasthas.find((x) => x.planet === lord)!;
    const delta = DEEPTADI_POINTS[a.deeptadi_avastha] ?? 0;
    const detail = [
      `${lord} is in ${a.deeptadi_avastha} (dignity-state) — Score: ${delta >= 0 ? "+" : ""}${delta}`,
      `${lord} is in ${a.baladi_avastha} (age-state) — informational only, not scored`,
    ];
    const subFactors = [
      { name: a.deeptadi_avastha, weight: Math.abs(DEEPTADI_POINTS[a.deeptadi_avastha] ?? 0), present: true, contribution: delta, description: "Deeptadi (dignity-based) state" },
    ];
    const maxPossible = 3;
    return {
      delta,
      inputs: { planet: lord, deeptadi_avastha: a.deeptadi_avastha, baladi_avastha: a.baladi_avastha },
      raw: { ...a },
      source: [`avastha/all[${lord}].deeptadi_avastha`],
      detail,
      subFactors,
      maxPossible,
    };
  },
};

// ── 9. Karaka Strength (marriage/wealth only) ────────────────────────────────
// DEFAULT WEIGHT: each area-relevant karaka's strength_score (0-10) shifted
// around a neutral 5.0 baseline, ±5 points per karaka. Only applies where
// KARAKAS_BY_AREA defines karakas for the area (marriage, wealth).
const KARAKA_NEUTRAL_SCORE = 5;
const KARAKA_MAX_POINTS = 5;

const karakaStrengthFactor: PredictionFactor = {
  id: "karaka-strength",
  label: "Karaka Strength",
  category: "Karakas",
  formulaVersion: "v1",
  appliesTo: (area) => KARAKAS_BY_AREA[area].length > 0,
  isAvailable: (ctx) => KARAKAS_BY_AREA[ctx.area].some((k) => findPlanetStrength(ctx, k)),
  compute: (ctx) => {
    const karakas = KARAKAS_BY_AREA[ctx.area];
    let delta = 0;
    const detail: string[] = [];
    const source: string[] = [];
    const raw: Record<string, unknown> = {};
    for (const k of karakas) {
      const ps = findPlanetStrength(ctx, k);
      if (!ps) { detail.push(`${k}: no strength data for this chart`); continue; }
      const points = clamp((ps.strength_score - KARAKA_NEUTRAL_SCORE) * 1, -KARAKA_MAX_POINTS, KARAKA_MAX_POINTS);
      delta += points;
      detail.push(`${k} (karaka) strength ${ps.strength_score.toFixed(1)}/10 — Score: ${points >= 0 ? "+" : ""}${points.toFixed(1)}`);
      source.push(`chart.planet_strengths[${k}].strength_score`);
      raw[k] = ps;
    }
    const karakaSubFactors = karakas.map((k) => {
      const ps = findPlanetStrength(ctx, k);
      if (!ps) return { name: `${k} (karaka)`, weight: KARAKA_MAX_POINTS, present: false, contribution: 0, description: "No strength data" };
      const points = clamp((ps.strength_score - KARAKA_NEUTRAL_SCORE) * 1, -KARAKA_MAX_POINTS, KARAKA_MAX_POINTS);
      return { name: `${k} (karaka)`, weight: KARAKA_MAX_POINTS, present: true, contribution: points, description: `Strength ${ps.strength_score.toFixed(1)}/10` };
    });
    const maxPossible = karakas.length * KARAKA_MAX_POINTS;
    return { delta: Math.round(delta * 10) / 10, inputs: { karakas }, raw, source, detail, subFactors: karakaSubFactors, maxPossible };
  },
};

export const PREDICTION_FACTORS: PredictionFactor[] = [
  houseStrengthFactor,
  planetStrengthFactor,
  digbalaFactor,
  aspectsFactor,
  yogasFactor,
  dashaInfluenceFactor,
  transitInfluenceFactor,
  avasthaFactor,
  karakaStrengthFactor,
];