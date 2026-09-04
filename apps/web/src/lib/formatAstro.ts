/**
 * AstroOS — Astrological Formatting Helpers
 *
 * Shared, app-wide formatting for sidereal longitudes and sign/nakshatra
 * names, matching the conventional Classical Vedic-style output:
 *
 *   Body    Longitude            Nakshatra Pada Rasi Navamsa
 *   Lagna   29 Ta 49' 17.89"     Mrig      2    Ta   Vi
 *
 * Every component that renders a planet/ascendant position should use
 * these helpers so the whole app stays consistent.
 */

// ── Sign abbreviations (Classical Vedic style) ─────────────────────────────────────────

export const RASHI_ABBREV: Record<string, string> = {
  aries: "Ar",
  taurus: "Ta",
  gemini: "Ge",
  cancer: "Cn",
  leo: "Le",
  virgo: "Vi",
  libra: "Li",
  scorpio: "Sc",
  sagittarius: "Sg",
  capricorn: "Cp",
  aquarius: "Aq",
  pisces: "Pi",
};

/** Short 2-letter sign abbreviation from a rashi string of any casing. */
export function rashiAbbrev(rashi: string | null | undefined): string {
  if (!rashi) return "—";
  return RASHI_ABBREV[rashi.toLowerCase()] ?? rashi;
}

// ── Nakshatra abbreviations (Classical Vedic style) ─────────────────────────────────────

export const NAKSHATRA_ABBREV: Record<string, string> = {
  ashwini: "Aswi",
  bharani: "Bhar",
  krittika: "Krit",
  rohini: "Rohi",
  mrigashira: "Mrig",
  ardra: "Ardr",
  punarvasu: "Puna",
  pushya: "Push",
  ashlesha: "Asle",
  magha: "Magh",
  purva_phalguni: "PPh",
  uttara_phalguni: "UPh",
  hasta: "Hast",
  chitra: "Chit",
  swati: "Swat",
  vishakha: "Visa",
  anuradha: "Anu",
  jyeshtha: "Jye",
  mula: "Mool",
  purva_ashadha: "PAs",
  uttara_ashadha: "UAs",
  shravana: "Srav",
  dhanishtha: "Dhan",
  shatabhisha: "Shat",
  purva_bhadrapada: "PBha",
  uttara_bhadrapada: "UBha",
  revati: "Reva",
};

/** Short nakshatra abbreviation (e.g. "Mrig", "Ardr") from any casing. */
export function nakshatraAbbrev(nakshatra: string | null | undefined): string {
  if (!nakshatra) return "—";
  return NAKSHATRA_ABBREV[nakshatra.toLowerCase()] ?? nakshatra;
}

// ── Longitude formatting ──────────────────────────────────────────────────────

/**
 * Format a full sidereal longitude (0–360°) in Classical Vedic's DMS form:
 *
 *   29 Ta 49' 17.89"
 *
 * Whole degrees within the sign (0–29), then the sign's 2-letter
 * abbreviation, then arcminutes and arcseconds. This is the canonical
 * planet-position format used across the app (chart detail tables,
 * workflow panels, etc.).
 */
export function formatLongitude(lonDeg: number | null | undefined): string {
  if (lonDeg === null || lonDeg === undefined || !isFinite(lonDeg)) return "—";
  const lon = ((lonDeg % 360) + 360) % 360;
  const deg = Math.floor(lon % 30);
  const fracMin = (lon - Math.floor(lon)) * 60;
  const min = Math.floor(fracMin);
  const sec = (fracMin - min) * 60;
  const signIndex = Math.floor(lon / 30) % 12;
  const rashi = Object.keys(RASHI_ABBREV)[signIndex];
  return `${deg} ${RASHI_ABBREV[rashi]} ${min}' ${sec.toFixed(2)}"`;
}

/**
 * Same as formatLongitude but from a longitude already expressed as
 * "degrees within a sign" (0–30) plus the sign name, which is what most
 * API position payloads carry (rashi_degree + rashi). Falls back to the
 * absolute-longitude formatter when the sign is unknown.
 */
export function formatPosition(
  rashi: string | null | undefined,
  rashiDegree: number | null | undefined,
): string {
  if (!rashi || rashiDegree === null || rashiDegree === undefined) return "—";
  const deg = Math.floor(rashiDegree);
  const fracMin = (rashiDegree - deg) * 60;
  const min = Math.floor(fracMin);
  const sec = (fracMin - min) * 60;
  return `${deg} ${rashiAbbrev(rashi)} ${min}' ${sec.toFixed(2)}"`;
}

// ── Combined rows for the Classical Vedic-style position table ──────────────────────────

export interface PositionTableRow {
  /** Body name — "Lagna", planet names, etc. */
  body: string;
  /** Display longitude, e.g. "29 Ta 49' 17.89\"" */
  longitude: string;
  /** Display nakshatra abbreviation */
  nakshatra: string;
  pada: number;
  /** Display rashi (D1 sign) abbreviation */
  rashi: string;
  /** Display navamsa (D9 sign) abbreviation */
  navamsa: string;
}
