/**
 * AstroOS — Astrological Constants
 *
 * Canonical reference data for the 12 rashis, 27 nakshatras, 108 padas,
 * planet symbols, and chart geometry helpers. Used by D3 chart components
 * and lookup selectors.
 */

// ── Rashis (Zodiac Signs) ──────────────────────────────────────────────────────

export const RASHIS = [
  "Mesha",
  "Vrishabha",
  "Mithuna",
  "Karka",
  "Simha",
  "Kanya",
  "Tula",
  "Vrischika",
  "Dhanu",
  "Makara",
  "Kumbha",
  "Meena",
] as const;

export type RashiName = (typeof RASHIS)[number];

/** Rashi index 0-11 from a sidereal longitude in degrees (0-360). */
export function rashiIndexFromLongitude(siderealDeg: number): number {
  return Math.floor(((siderealDeg % 360) + 360) % 360 / 30);
}

/** Rashi lord (planet) for each sign. */
export const RASHI_LORDS: Record<RashiName, string> = {
  Mesha: "Mars",
  Vrishabha: "Venus",
  Mithuna: "Mercury",
  Karka: "Moon",
  Simha: "Sun",
  Kanya: "Mercury",
  Tula: "Venus",
  Vrischika: "Mars",
  Dhanu: "Jupiter",
  Makara: "Saturn",
  Kumbha: "Saturn",
  Meena: "Jupiter",
};

/**
 * The backend's Rashi enum (packages/shared/enums.py) has Sanskrit
 * *names* but English *values* — Rashi.MESHA.value == "aries" — and it's
 * the English value that actually gets serialized into every API
 * response (chart.houses[].rashi, chart.ascendant.rashi, etc.), Title-
 * Cased by lib/api.ts's casing normalization ("Aries", not "aries" or
 * "Mesha"). RASHI_LORDS above, and the RASHIS array, are both keyed with
 * Sanskrit names for display purposes throughout this file. That means
 * `RASHI_LORDS[someRealChart.rashi]` has always silently resolved to
 * undefined for every real chart — found 2026-07-24 while debugging
 * "Health Risk: Unknown" (kpiScoring.ts's getHouseLordStrength, and by
 * extension every KPI built on it — Career/Marriage/Wealth/Mental
 * Stability/Prediction Chain Explorer — plus HouseDependencyNetwork.tsx
 * and the Ascendant-lord line on /charts, all depend on this lookup).
 *
 * This map + rashiLordFromApiName() below is the fix: anywhere you have
 * a rashi string that came from the API (not from this file's own
 * RASHIS array), look up its lord through rashiLordFromApiName(), not
 * RASHI_LORDS[...] directly.
 */
const _ENGLISH_TO_SANSKRIT_RASHI: Record<string, RashiName> = {
  aries: "Mesha",
  taurus: "Vrishabha",
  gemini: "Mithuna",
  cancer: "Karka",
  leo: "Simha",
  virgo: "Kanya",
  libra: "Tula",
  scorpio: "Vrischika",
  sagittarius: "Dhanu",
  capricorn: "Makara",
  aquarius: "Kumbha",
  pisces: "Meena",
};

/**
 * Look up a sign's ruling lord from a rashi string as it actually comes
 * back from the API — English, any casing ("Aries", "aries", "ARIES").
 * Falls back to treating the input as already-Sanskrit (a RashiName) so
 * this is also safe to call with values sourced from this file's own
 * RASHIS array. Returns null if the input matches neither.
 */
export function rashiLordFromApiName(rashi: string | null | undefined): string | null {
  if (!rashi) return null;
  const sanskritKey = _ENGLISH_TO_SANSKRIT_RASHI[rashi.toLowerCase()] ?? (rashi as RashiName);
  return RASHI_LORDS[sanskritKey] ?? null;
}

// ── Nakshatras ─────────────────────────────────────────────────────────────────

export const NAKSHATRAS = [
  "Ashwini",
  "Bharani",
  "Krittika",
  "Rohini",
  "Mrigashira",
  "Ardra",
  "Punarvasu",
  "Pushya",
  "Ashlesha",
  "Magha",
  "Purva Phalguni",
  "Uttara Phalguni",
  "Hasta",
  "Chitra",
  "Swati",
  "Vishakha",
  "Anuradha",
  "Jyeshtha",
  "Mula",
  "Purva Ashadha",
  "Uttara Ashadha",
  "Shravana",
  "Dhanishta",
  "Shatabhisha",
  "Purva Bhadrapada",
  "Uttara Bhadrapada",
  "Revati",
] as const;

export type NakshatraName = (typeof NAKSHATRAS)[number];

/** Nakshatra lord for each of the 27 nakshatras. */
export const NAKSHATRA_LORDS: Record<NakshatraName, string> = {
  Ashwini: "Ketu",
  Bharani: "Venus",
  Krittika: "Sun",
  Rohini: "Moon",
  "Mrigashira": "Mars",
  Ardra: "Rahu",
  Punarvasu: "Jupiter",
  Pushya: "Saturn",
  Ashlesha: "Mercury",
  Magha: "Ketu",
  "Purva Phalguni": "Venus",
  "Uttara Phalguni": "Sun",
  Hasta: "Moon",
  Chitra: "Mars",
  Swati: "Rahu",
  Vishakha: "Jupiter",
  Anuradha: "Saturn",
  Jyeshtha: "Mercury",
  Mula: "Ketu",
  "Purva Ashadha": "Venus",
  "Uttara Ashadha": "Sun",
  Shravana: "Moon",
  Dhanishta: "Mars",
  Shatabhisha: "Rahu",
  "Purva Bhadrapada": "Jupiter",
  "Uttara Bhadrapada": "Saturn",
  Revati: "Mercury",
};

/** Nakshatra padas: each nakshatra has 4 padas (total 108 padas). */
export function getAllPadas(): { nakshatra: NakshatraName; pada: number }[] {
  const result: { nakshatra: NakshatraName; pada: number }[] = [];
  for (const nak of NAKSHATRAS) {
    for (let p = 1; p <= 4; p++) {
      result.push({ nakshatra: nak, pada: p });
    }
  }
  return result;
}

/** Find the nakshatra from a sidereal longitude (each is 13°20'). */
export function nakshatraFromLongitude(siderealDeg: number): {
  nakshatra: NakshatraName;
  pada: number;
  degreeInNakshatra: number;
} {
  const deg = ((siderealDeg % 360) + 360) % 360;
  const nakWidth = 360 / 27; // 13.333...
  const nakIndex = Math.floor(deg / nakWidth);
  const degreeInNak = deg - nakIndex * nakWidth;
  const pada = Math.min(4, Math.floor(degreeInNak / (nakWidth / 4)) + 1);
  return {
    nakshatra: NAKSHATRAS[nakIndex],
    pada,
    degreeInNakshatra: degreeInNak,
  };
}

// ── Planets ────────────────────────────────────────────────────────────────────

/** Canonical planet names as used in API responses. */
export const PLANETS = [
  "Sun",
  "Moon",
  "Mars",
  "Mercury",
  "Jupiter",
  "Venus",
  "Saturn",
  "Rahu",
  "Ketu",
] as const;

export type PlanetName = (typeof PLANETS)[number];

/** Abbreviated labels for chart rendering. */
export const PLANET_ABBREV: Record<string, string> = {
  Sun: "Su",
  Moon: "Mo",
  Mars: "Ma",
  Mercury: "Me",
  Jupiter: "Ju",
  Venus: "Ve",
  Saturn: "Sa",
  Rahu: "Ra",
  Ketu: "Ke",
};

/** Unicode / traditional symbols for planets. */
export const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉",
  Moon: "☽",
  Mars: "♂",
  Mercury: "☿",
  Jupiter: "♃",
  Venus: "♀",
  Saturn: "♄",
  Rahu: "☊",
  Ketu: "☋",
};

// ── Dasha System Constants ─────────────────────────────────────────────────────

export const VIMSHOTTARI_LORDS: string[] = [
  "Ketu",
  "Venus",
  "Sun",
  "Moon",
  "Mars",
  "Rahu",
  "Jupiter",
  "Saturn",
  "Mercury",
];

export const DASHA_SYSTEM_LABELS: Record<string, string> = {
  vimshottari: "Vimshottari",
  yogini: "Yogini",
  ashtottari: "Ashtottari",
  kalachakra: "Kalachakra",
  chara: "Chara",
  narayana: "Narayana",
};

// ── Chart Geometry (North Indian / Diamond style) ─────────────────────────────

/**
 * The 12 house positions for the North Indian diamond chart.
 * Each position is named for its relative position in the diamond.
 *
 * The North Indian chart is a fixed-layout diamond with the Ascendant
 * house at the top center. Houses are numbered 1-12 going clockwise
 * from the ascendant house.
 */
export const NORTH_INDIAN_HOUSE_POSITIONS = [
  { house: 1, x: 0, y: -1 },    // top center
  { house: 2, x: 0.5, y: -0.5 },  // top-right
  { house: 3, x: 1, y: 0 },     // right
  { house: 4, x: 0.5, y: 0.5 },  // bottom-right
  { house: 5, x: 0, y: 1 },     // bottom center
  { house: 6, x: -0.5, y: 0.5 }, // bottom-left
  { house: 7, x: -1, y: 0 },    // left
  { house: 8, x: -0.5, y: -0.5 },// top-left
  { house: 9, x: 0, y: -0.75 },  // inner top
  { house: 10, x: 0.75, y: 0 },  // inner right
  { house: 11, x: 0, y: 0.75 },  // inner bottom
  { house: 12, x: -0.75, y: 0 }, // inner left
] as const;

/** Map a rashi name to a 0-11 index for house placement. Sanskrit-keyed — see
 * rashiIndexFromApiName() below for the version that also accepts real API
 * (English) rashi names. */
export const RASHI_TO_INDEX: Record<string, number> = Object.fromEntries(
  RASHIS.map((r, i) => [r, i])
);

/**
 * Same Sanskrit-vs-English problem as rashiLordFromApiName() above, but for
 * RASHI_TO_INDEX: real chart data (chart.planets[].rashi, chart.ascendant.rashi)
 * is English ("Aries"), RASHI_TO_INDEX is Sanskrit-keyed ("Mesha"). Looking
 * real data up directly in RASHI_TO_INDEX silently resolved to undefined →
 * `?? 0` for every planet AND the ascendant alike, which put every single
 * planet in the same house (house 1) — found 2026-07-23 from a chart
 * screenshot showing every graha stacked in one row under Lagna. Use this
 * anywhere a rashi string came from the API; RASHI_TO_INDEX directly is only
 * safe for this file's own Sanskrit RASHIS array.
 */
export function rashiIndexFromApiName(rashi: string | null | undefined): number {
  if (!rashi) return 0;
  const sanskritKey = _ENGLISH_TO_SANSKRIT_RASHI[rashi.toLowerCase()] ?? (rashi as RashiName);
  return RASHI_TO_INDEX[sanskritKey] ?? 0;
}

/** Color palette for chart rendering in both themes. */
export const CHART_COLORS = {
  rashiBackgrounds: [
    "#1e3a5f", "#2a1a4a", "#1a3a2a", "#4a2a1a",
    "#3a1a3a", "#1a2a4a", "#4a3a1a", "#2a3a1a",
    "#1a4a3a", "#3a2a4a", "#4a1a2a", "#2a4a3a",
  ],
  planetText: "#fbbf24",
  ascendantText: "#f87171",
  houseBorder: "rgba(255,255,255,0.2)",
  retrogradeColor: "#ef4444",
  aspectColors: {
    conjunction: "#fbbf24",
    trine: "#34d399",
    square: "#f87171",
    opposition: "#a78bfa",
    sextile: "#38bdf8",
  },
} as const;

// ── Classical Reference Data (static, not computed) ────────────────────────────
//
// These two tables are fixed classical astrological reference data (BPHS-derived),
// not anything the backend calculates per-chart. They're shown in the Interactive
// Kundli's side panel alongside real computed data (house, sign, aspects, strength,
// etc.) — kept clearly separate so it's obvious what's "this chart's computed data"
// vs. "general classical reference for this planet."

/** Natural (permanent) friend / enemy / neutral relationships — classical, fixed. */
export const NATURAL_RELATIONSHIPS: Record<
  string,
  { friends: string[]; enemies: string[]; neutrals: string[] }
> = {
  Sun: { friends: ["Moon", "Mars", "Jupiter"], enemies: ["Venus", "Saturn"], neutrals: ["Mercury"] },
  Moon: { friends: ["Sun", "Mercury"], enemies: [], neutrals: ["Mars", "Jupiter", "Venus", "Saturn"] },
  Mars: { friends: ["Sun", "Moon", "Jupiter"], enemies: ["Mercury"], neutrals: ["Venus", "Saturn"] },
  Mercury: { friends: ["Sun", "Venus"], enemies: ["Moon"], neutrals: ["Mars", "Jupiter", "Saturn"] },
  Jupiter: { friends: ["Sun", "Moon", "Mars"], enemies: ["Mercury", "Venus"], neutrals: ["Saturn"] },
  Venus: { friends: ["Mercury", "Saturn"], enemies: ["Sun", "Moon"], neutrals: ["Mars", "Jupiter"] },
  Saturn: { friends: ["Mercury", "Venus"], enemies: ["Sun", "Moon", "Mars"], neutrals: ["Jupiter"] },
  Rahu: { friends: ["Venus", "Saturn", "Mercury"], enemies: ["Sun", "Moon", "Mars"], neutrals: ["Jupiter"] },
  Ketu: { friends: ["Mars", "Venus", "Saturn"], enemies: ["Sun", "Moon"], neutrals: ["Mercury", "Jupiter"] },
};

/** A short list of classical significations (karakatva) per planet — a small
 * hand-picked reference set, not the full 25,000+ karakatva database planned
 * for the dedicated Karakatva Explorer module (that's a separate, much larger
 * content workstream — see ASTROOS_VISION_V3_ROADMAP.md Phase 5). */
export const KARAKATVA_BASIC: Record<string, string[]> = {
  Sun: ["Soul", "Father", "Authority", "Government", "Health", "Vitality", "Ego"],
  Moon: ["Mind", "Mother", "Emotions", "Public", "Comfort", "Fluids", "Nurturing"],
  Mars: ["Courage", "Siblings", "Land", "Energy", "Conflict", "Surgery", "Sports"],
  Mercury: ["Intellect", "Communication", "Business", "Education", "Speech", "Analysis"],
  Jupiter: ["Wisdom", "Wealth", "Children", "Guru", "Spirituality", "Expansion", "Fortune"],
  Venus: ["Marriage", "Love", "Luxury", "Art", "Beauty", "Vehicles", "Comforts"],
  Saturn: ["Career", "Discipline", "Longevity", "Delays", "Labor", "Old Age", "Structure"],
  Rahu: ["Obsession", "Foreign", "Illusion", "Ambition", "Technology", "Sudden Events"],
  Ketu: ["Detachment", "Spirituality", "Past Karma", "Isolation", "Moksha", "Intuition"],
};

// ── Varga Divisors ─────────────────────────────────────────────────────────────

export const VARGA_DIVISORS: Record<string, { label: string; divisor: number }> = {
  D1: { label: "Rashi (D1)", divisor: 1 },
  D2: { label: "Hora (D2)", divisor: 2 },
  D3: { label: "Drekkana (D3)", divisor: 3 },
  D4: { label: "Chaturthamsha (D4)", divisor: 4 },
  D7: { label: "Saptamamsha (D7)", divisor: 7 },
  D9: { label: "Navamsha (D9)", divisor: 9 },
  D10: { label: "Dashamsha (D10)", divisor: 10 },
  D12: { label: "Dvadashamsha (D12)", divisor: 12 },
  D16: { label: "Shodashamsha (D16)", divisor: 16 },
  D20: { label: "Vimshamsha (D20)", divisor: 20 },
  D24: { label: "Siddhamsha (D24)", divisor: 24 },
  D27: { label: "Saptavimshamsha (D27)", divisor: 27 },
  D30: { label: "Trimshamsha (D30)", divisor: 30 },
  D40: { label: "Khavedamsha (D40)", divisor: 40 },
  D45: { label: "Akshavedamsha (D45)", divisor: 45 },
  D60: { label: "Shastyamsha (D60)", divisor: 60 },
};
