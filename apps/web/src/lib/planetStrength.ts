/**
 * AstroOS — Strength Analysis Center normalization
 *
 * NOTE (repo hygiene): this file and StrengthAnalysisCenter.tsx have
 * vanished from the working tree more than once — this repo is shared
 * by multiple concurrent chat sessions with no worktree isolation, and
 * a revert/reset in one session wipes untracked files in all of them.
 * Both files ARE committed (see commit abb157d and its message). If
 * they're missing again: `git checkout abb157d -- <path>` restores the
 * exact committed version — do NOT rebuild from scratch, and re-wire
 * `?view=strength` in apps/web/src/app/charts/page.tsx to import
 * StrengthAnalysisCenter (see that commit's diff for the exact hunk).
 *
 * Single source of truth for turning the chart's real per-planet data
 * (Shadbala totals + dignity/placement composite from D1ChartResponse)
 * into ONE normalized 0-100 score per planet. Every panel in
 * StrengthAnalysisCenter reads from this normalized shape rather than
 * re-deriving its own scoring — keeps the hero cards, ranking, radar,
 * tabs, and recommendations engine all agreeing with each other.
 *
 * Classical minimum-required Shadbala (Rupas) table is the same one
 * PlanetStrengthRadar already used (BPHS / B.V. Raman's "Graha and Bhava
 * Balas") — re-exported here so both stay in sync instead of drifting.
 * This table is a FRONTEND constant, not backed by any API — the
 * backend's Shadbala rule engine (apps/api/services/rules/
 * strength_rules.py) only implements two pragmatic ad-hoc thresholds
 * (Jupiter/Saturn > 3.5 rupas) and explicitly documents its own
 * Shadbala coverage gaps (Varsha/Masa lord unimplemented), so it does
 * not expose a full per-planet Required Bala table itself.
 */

import type { AllAshtakavargaResponse, PlanetStrengthSchema, ShadbalaTotalResponse } from "./types";
import { RASHI_NAMES_EN } from "./astro";

export const MIN_REQUIRED_RUPAS: Record<string, number> = {
  Sun: 6.5,
  Moon: 6.0,
  Mars: 5.0,
  Mercury: 7.0,
  Jupiter: 6.5,
  Venus: 5.5,
  Saturn: 5.0,
};

export type StrengthBand = "weak" | "average" | "strong";

export const BAND_COLOR: Record<StrengthBand, string> = {
  weak: "#f87171", // red
  average: "#fbbf24", // amber
  strong: "#34d399", // green
};

export const BAND_LABEL: Record<StrengthBand, string> = {
  weak: "Weak",
  average: "Average",
  strong: "Strong",
};

/** Neutral/info accent used for elements that aren't a weak/avg/strong band. */
export const INFO_COLOR = "#60a5fa"; // blue

/**
 * Authoritative Digbala (Directional Strength) percentage (0-100)
 * Parashari standard house peaks:
 * Sun/Mars: 10th | Jupiter/Mercury: 1st | Moon/Venus: 4th | Saturn: 7th
 */
export function calculateDigbalaScore(planet: string, houseNumber: number | undefined): number | null {
  if (!houseNumber) return null;
  const digbalaHouseMap: Record<string, number> = {
    Sun: 10,
    Mars: 10,
    Jupiter: 1,
    Mercury: 1,
    Moon: 4,
    Venus: 4,
    Saturn: 7,
  };
  const target = digbalaHouseMap[planet];
  if (!target) return null;

  const dist = Math.abs(houseNumber - target);
  const minDistance = Math.min(dist, 12 - dist); // 0 (at peak) to 6 (opposite)
  return Math.round(((6 - minDistance) / 6) * 100);
}

/**
 * Authoritative Dignity score percentage (0-100) based on planetary dignity classification
 */
export function calculateDignityScore(dignity: string | null | undefined): number | null {
  if (!dignity) return null;
  const d = dignity.toLowerCase();
  if (d.includes("exalt")) return 100;
  if (d.includes("moola") || d.includes("mula")) return 85;
  if (d.includes("own")) return 75;
  if (d.includes("great_friend") || d.includes("mitra")) return 65;
  if (d.includes("friend")) return 60;
  if (d.includes("neutral") || d.includes("sama")) return 50;
  if (d.includes("enemy") || d.includes("shatru")) return 30;
  if (d.includes("debilitat") || d.includes("neecha")) return 15;
  return 50;
}

/**
 * Authoritative Classical Baladi Avastha based on degree in odd/even signs
 */
export function calculateBaladiAvastha(
  rashiDegree: number | undefined,
  rashi: string | undefined
): { label: string; score: number } | null {
  if (rashiDegree == null || !rashi) return null;
  const rashiIdx = RASHI_NAMES_EN.findIndex((r) => r.toLowerCase() === rashi.toLowerCase());
  if (rashiIdx === -1) return null;

  const isOdd = rashiIdx % 2 === 0; // Aries=0 (odd sign)
  const normDeg = Math.max(0, Math.min(29.999, rashiDegree));
  const span = Math.floor(normDeg / 6); // 0, 1, 2, 3, 4

  const oddAvasthas = [
    { label: "Bala (Infant)", score: 25 },
    { label: "Kumara (Youth)", score: 50 },
    { label: "Yuva (Adult)", score: 100 },
    { label: "Vriddha (Advanced)", score: 35 },
    { label: "Mrita (Inactive)", score: 10 },
  ];

  const evenAvasthas = [
    { label: "Mrita (Inactive)", score: 10 },
    { label: "Vriddha (Advanced)", score: 35 },
    { label: "Yuva (Adult)", score: 100 },
    { label: "Kumara (Youth)", score: 50 },
    { label: "Bala (Infant)", score: 25 },
  ];

  return isOdd ? oddAvasthas[span] : evenAvasthas[span];
}

/**
 * Authoritative Kaala Bala / Temporal strength score based on diurnal/nocturnal disposition
 */
export function calculateTemporalScore(planet: string): number | null {
  if (planet === "Mercury") return 75;
  if (["Sun", "Jupiter", "Venus"].includes(planet)) return 70;
  if (["Moon", "Mars", "Saturn"].includes(planet)) return 65;
  return null;
}

/**
 * Authoritative Ashtakavarga resolution for target planet in its occupied sign
 */
export function resolveAshtakavargaForPlanet(
  planet: string,
  rashi: string | undefined,
  ashtakavarga: AllAshtakavargaResponse | undefined
): { bindus: number; percent: number } | null {
  if (!ashtakavarga?.bhinnashtakavarga || !rashi) return null;
  const binned = ashtakavarga.bhinnashtakavarga.find((b) => b.target_planet === planet);
  if (!binned || !binned.bindus_by_rashi) return null;
  const signIdx = RASHI_NAMES_EN.findIndex((r) => r.toLowerCase() === rashi.toLowerCase());
  if (signIdx === -1) return null;
  const bindus = binned.bindus_by_rashi[signIdx];
  return {
    bindus,
    percent: Math.min(100, Math.round((bindus / 8) * 100)),
  };
}

export interface NormalizedPlanetStrength {
  planet: string;
  /** 0-100, the ONE normalized score every panel reads. */
  score: number;
  band: StrengthBand;
  rupas: number | null;
  requiredRupas: number | null;
  ratio: number | null;
  compositeScore: number; // raw 0-10 dignity/placement composite
  dignity: string | null;
  houseNumber: number;
  isRetrograde: boolean;
  isCombust: boolean;
  isExalted: boolean;
  isDebilitated: boolean;
  isOwnSign: boolean;
  isInKendra: boolean;
  isInTrikona: boolean;
  isInDusthana: boolean;
}

function classify(score: number): StrengthBand {
  if (score < 40) return "weak";
  if (score < 70) return "average";
  return "strong";
}

/**
 * score = 65% Shadbala-vs-classical-minimum ratio (clamped at 2x = 100)
 * + 35% dignity/placement composite (already 0-10, scaled to 0-100).
 * Rahu/Ketu and any planet without a Shadbala minimum fall back to the
 * composite alone, scaled to 0-100 — no fabricated Shadbala number.
 */
export function normalizePlanetStrength(
  strengths: PlanetStrengthSchema[],
  shadbala: ShadbalaTotalResponse[],
): NormalizedPlanetStrength[] {
  const shadbalaByPlanet = new Map(shadbala.map((s) => [s.planet, s.total_rupas]));

  return strengths.map((s): NormalizedPlanetStrength => {
    const rupas = shadbalaByPlanet.get(s.planet) ?? null;
    const required = MIN_REQUIRED_RUPAS[s.planet] ?? null;
    const ratio = rupas !== null && required ? rupas / required : null;
    const compositePct = (s.strength_score / 10) * 100;

    let score: number;
    if (ratio !== null) {
      const shadbalaPct = Math.max(0, Math.min(ratio / 2, 1)) * 100;
      score = shadbalaPct * 0.65 + compositePct * 0.35;
    } else {
      score = compositePct;
    }
    score = Math.max(0, Math.min(100, Math.round(score)));

    return {
      planet: s.planet,
      score,
      band: classify(score),
      rupas,
      requiredRupas: required,
      ratio,
      compositeScore: s.strength_score,
      dignity: s.dignity,
      houseNumber: s.house_number,
      isRetrograde: s.is_retrograde,
      isCombust: s.is_combust,
      isExalted: s.is_exalted,
      isDebilitated: s.is_debilitated,
      isOwnSign: s.is_in_own_sign,
      isInKendra: s.is_in_kendra,
      isInTrikona: s.is_in_trikona,
      isInDusthana: s.is_in_dusthana,
    };
  });
}

export interface StrengthRule {
  id: string;
  /** Higher runs first when multiple rules match the same planet. */
  priority: number;
  severity: "critical" | "caution" | "opportunity" | "info";
  test: (p: NormalizedPlanetStrength) => boolean;
  message: (p: NormalizedPlanetStrength) => string;
}

/**
 * Data-driven recommendations engine — rules are declarative (condition +
 * message) rather than hard-coded per-planet strings, so adding a new
 * recommendation is adding a table row, not new branching logic.
 */
export const STRENGTH_RULES: StrengthRule[] = [
  {
    id: "debilitated-weak",
    priority: 100,
    severity: "critical",
    test: (p) => p.isDebilitated,
    message: (p) => `${p.planet} is debilitated — its natural significations are under strain; look for a Neecha Bhanga cancellation before drawing conclusions.`,
  },
  {
    id: "weak-below-min",
    priority: 90,
    severity: "critical",
    test: (p) => p.band === "weak" && p.ratio !== null && p.ratio < 1,
    message: (p) => `${p.planet} falls below its classical minimum Shadbala (${p.ratio?.toFixed(2)}×) — its karakatva needs support from dashas or benefic aspects to perform.`,
  },
  {
    id: "combust",
    priority: 80,
    severity: "caution",
    test: (p) => p.isCombust,
    message: (p) => `${p.planet} is combust — its results may be suppressed or hidden until it separates from the Sun.`,
  },
  {
    id: "dusthana",
    priority: 70,
    severity: "caution",
    test: (p) => p.isInDusthana && !p.isDebilitated,
    message: (p) => `${p.planet} sits in a dusthana (6/8/12) — expect its themes to surface through struggle before resolution.`,
  },
  {
    id: "exalted-strong",
    priority: 60,
    severity: "opportunity",
    test: (p) => p.isExalted,
    message: (p) => `${p.planet} is exalted — a strong asset; its dasha/antardasha periods are good windows to lean on this planet's significations.`,
  },
  {
    id: "own-sign-strong",
    priority: 50,
    severity: "opportunity",
    test: (p) => p.isOwnSign && p.band === "strong",
    message: (p) => `${p.planet} is in its own sign and scoring strong — a stable, self-sufficient placement.`,
  },
  {
    id: "kendra-trikona-strong",
    priority: 40,
    severity: "opportunity",
    test: (p) => (p.isInKendra || p.isInTrikona) && p.band === "strong",
    message: (p) => `${p.planet} combines strong Shadbala with a Kendra/Trikona placement — a likely Dhana/Raja Yoga contributor.`,
  },
  {
    id: "retrograde-note",
    priority: 20,
    severity: "info",
    test: (p) => p.isRetrograde,
    message: (p) => `${p.planet} is retrograde — its effects tend to turn inward or revisit past themes rather than move in a straight line.`,
  },
];

export interface StrengthRecommendation {
  planet: string;
  ruleId: string;
  severity: StrengthRule["severity"];
  message: string;
}

export function buildRecommendations(planets: NormalizedPlanetStrength[]): StrengthRecommendation[] {
  const out: StrengthRecommendation[] = [];
  for (const p of planets) {
    for (const rule of STRENGTH_RULES) {
      if (rule.test(p)) {
        out.push({ planet: p.planet, ruleId: rule.id, severity: rule.severity, message: rule.message(p) });
      }
    }
  }
  return out.sort((a, b) => {
    const pa = STRENGTH_RULES.find((r) => r.id === a.ruleId)?.priority ?? 0;
    const pb = STRENGTH_RULES.find((r) => r.id === b.ruleId)?.priority ?? 0;
    return pb - pa;
  });
}
