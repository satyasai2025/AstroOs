import type { WorkflowAnalysisRequest } from "@/lib/types";

/**
 * Jagannatha Hora (.jhd) import.
 *
 * The .jhd birth file (in JHora's default text mode) is CRLF-separated lines:
 *
 *   1. Month        (1-12)
 *   2. Day          (1-31)
 *   3. Year         (4-digit)
 *   4. Birth time   decimal hours, e.g. 1.3283333 = 01:19:42
 *   5. TimeZone     signed hours ADDED to local time to get UTC (negative for
 *                   East longitudes, e.g. India -5.3).
 *   6. Longitude    signed, stored WEST-positive — so East is negative.
 *                   Standard longitude = NEGATE the stored value.
 *   7. Latitude     signed, North-positive (standard, used as-is).
 *   8.  (optional)  DST correction hours.
 *   9+  (optional)  place codes, name fields — ignored but tolerated.
 *
 * Convention verified against shipped files: Gandhi (Porbandar 69.6E → stored
 * -69.49, lat 21.37), Meena (Taloda 74.1E → -74.13, lat 21.34), Aurobindo
 * (Calcutta ~88E → -88.20, lat 22.30).
 *
 * The parsed birth data is submitted as a normal birth-chart request, so the
 * backend recomputes the chart with this app's engine. Defaults mirror the
 * classic JHora setting: Lahiri ayanamsa, whole-sign houses.
 */

export interface JhdParsePreview {
  subject_name: string;
  birth_local: string;
  latitude: number;
  longitude: number;
  place_name: string | null;
  ayanamsa: string;
  house_system: string;
}

export interface JhdParseResult {
  request: WorkflowAnalysisRequest | null;
  preview: JhdParsePreview | null;
  error: string | null;
}

function readLines(bytes: Uint8Array): string[] {
  const text = new TextDecoder("ascii").decode(bytes);
  return text
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

function fail(error: string): JhdParseResult {
  return { request: null, preview: null, error };
}

/** Decimal hours → [hours, minutes, seconds]. */
function hoursToHms(v: number): [number, number, number] {
  const totalSec = Math.round(v * 3600);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return [h, m, s];
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export function parseJhdFile(fileName: string, bytes: Uint8Array): JhdParseResult {
  let lines: string[];
  try {
    lines = readLines(bytes);
  } catch {
    return fail("Could not decode this file as text.");
  }
  if (lines.length < 7) {
    return fail(
      `This .jhd file has ${lines.length} line(s) — expected at least 7 (date, time, timezone, coordinates).`,
    );
  }

  const num = (idx: number, what: string): number => {
    const v = Number.parseFloat(lines[idx]);
    if (Number.isNaN(v)) throw new Error(`${what} in this file is not a number ("${lines[idx]}").`);
    return v;
  };

  let month: number, day: number, year: number, timeHours: number;
  let utcOffset: number, lonDeg: number, latDeg: number;
  try {
    month = num(0, "Month");
    day = num(1, "Day");
    year = num(2, "Year");
    timeHours = num(3, "Birth time");
    utcOffset = num(4, "TimeZone");
    lonDeg = num(5, "Longitude");
    latDeg = num(6, "Latitude");
  } catch (err) {
    return fail(err instanceof Error ? err.message : "Could not parse the numeric fields.");
  }

  if (!Number.isInteger(month) || month < 1 || month > 12) return fail(`Invalid month: ${month}`);
  if (!Number.isInteger(day) || day < 1 || day > 31) return fail(`Invalid day: ${day}`);
  if (!Number.isInteger(year) || year < 1 || year > 9999) return fail(`Invalid year: ${year}`);
  if (Math.abs(latDeg) > 90) return fail(`Invalid latitude: ${latDeg}`);
  if (Math.abs(lonDeg) > 180) return fail(`Invalid longitude: ${lonDeg}`);
  if (Math.abs(utcOffset) > 24) return fail(`Invalid timezone offset: ${utcOffset}`);

  // File stores longitude WEST-positive → East is negative. Standard longitude
  // (East positive) is the negation. Latitude is already standard.
  const longitude = -lonDeg;
  const latitude = latDeg;

  const [h, m, s] = hoursToHms(timeHours);
  // Local wall-clock as a pure UTC-math instant (Date.UTC treats parts literally).
  const localMs = Date.UTC(year, month - 1, day, h, m, s);
  if (Number.isNaN(localMs)) return fail("The file's date/time could not be turned into a valid instant.");

  // Optional line 8 = DST correction hours (0 when absent, as in our samples).
  let dstHours = 0;
  if (lines.length > 7) {
    const d = Number.parseFloat(lines[7]);
    if (!Number.isNaN(d)) dstHours = d;
  }

  // UTC = local wall-clock + timezone offset (+ optional DST correction).
  const birthUtcMs = localMs + Math.round((utcOffset + dstHours) * 3_600_000);
  const birthDatetimeUtc = new Date(birthUtcMs).toISOString();

  const subjectName = fileName.replace(/\.jhd$/i, "").trim() || "Imported chart";
  const birthLocal = `${year}-${pad(month)}-${pad(day)} ${pad(h)}:${pad(m)}`;

  const preview: JhdParsePreview = {
    subject_name: subjectName,
    birth_local: birthLocal,
    latitude,
    longitude,
    place_name: null,
    ayanamsa: "lahiri",
    house_system: "W",
  };

  const request: WorkflowAnalysisRequest = {
    birth_datetime_utc: birthDatetimeUtc,
    latitude,
    longitude,
    ayanamsa: "lahiri",
    house_system: "W",
    dasha_system: "vimshottari",
    include_vargas: true,
    subject_name: subjectName,
    place_name: null,
  };

  return { request, preview, error: null };
}