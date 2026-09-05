import type { WorkflowAnalysisRequest } from "@/lib/types";

/**
 * Classical Vedic System (.jhd) import.
 *
 * The .jhd birth file (in Jagannatha Hora / Classical Vedic format) is CRLF-separated lines:
 *
 *   1. Month        (1-12)
 *   2. Day          (1-31)
 *   3. Year         (4-digit)
 *   4. Birth time   HH.MMSSssss format (e.g. 1.3283333 = 1 hr, 32 min, 50 sec = 01:32:50)
 *   5. TimeZone     HH.MMSS format, signed hours ADDED to local time to get UTC
 *                   (negative for East longitudes, e.g. -5.300000 = -5h 30m).
 *   6. Longitude    DEG.MMSS format, stored WEST-positive (so East is negative).
 *                   Standard longitude = NEGATE the stored value and convert from DEG.MMSS.
 *   7. Latitude     DEG.MMSS format, North-positive (convert from DEG.MMSS).
 *   8.  (optional)  DST correction hours.
 *   9.  (optional)  Decimal timezone offset (e.g. -5.500000).
 *   13. (optional)  City name (e.g. Taloda).
 *   14. (optional)  Country name (e.g. India).
 *
 * Convention verified against standard Jagannatha Hora shipped charts:
 * Gandhi (Porbandar -69.49 -> 69°49'E, 21.37 -> 21°37'N, 7.20 -> 07:20:00)
 * Meena (Taloda -74.13 -> 74°13'E, 21.34 -> 21°34'N, 1.328333 -> 01:32:50)
 * Raman (Bangalore -77.35 -> 77°35'E, 12.59 -> 12°59'N, 19.38 -> 19:38:00)
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

/** Decode JHora HH.MMSSssss format into [hours, minutes, seconds]. */
function decodeJhdTime(val: number): [number, number, number] {
  let hours = Math.floor(val);
  const remMinutes = (val - hours) * 100;
  let minutes = Math.floor(remMinutes + 1e-7);
  let seconds = Math.round((remMinutes - minutes) * 60);

  if (seconds >= 60) {
    seconds -= 60;
    minutes += 1;
  }
  if (minutes >= 60) {
    minutes -= 60;
    hours += 1;
  }
  return [hours, minutes, seconds];
}

/** Decode JHora DEG.MMSSssss format into standard decimal degrees. */
function decodeJhdDegrees(val: number): number {
  const sign = val < 0 ? -1 : 1;
  const absVal = Math.abs(val);
  const deg = Math.floor(absVal);
  const rem = (absVal - deg) * 100;
  const minutes = Math.floor(rem + 1e-7);
  const seconds = (rem - minutes) * 60;
  const decimal = deg + minutes / 60.0 + seconds / 3600.0;
  return sign * Number(decimal.toFixed(6));
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

  let month: number, day: number, year: number, rawTime: number;
  let rawTz: number, rawLon: number, rawLat: number;
  try {
    month = num(0, "Month");
    day = num(1, "Day");
    year = num(2, "Year");
    rawTime = num(3, "Birth time");
    rawTz = num(4, "TimeZone");
    rawLon = num(5, "Longitude");
    rawLat = num(6, "Latitude");
  } catch (err) {
    return fail(err instanceof Error ? err.message : "Could not parse the numeric fields.");
  }

  if (!Number.isInteger(month) || month < 1 || month > 12) return fail(`Invalid month: ${month}`);
  if (!Number.isInteger(day) || day < 1 || day > 31) return fail(`Invalid day: ${day}`);
  if (!Number.isInteger(year) || year < 1 || year > 9999) return fail(`Invalid year: ${year}`);

  // Decode JHora coordinates (DEG.MMSS format, West is stored positive so negate for standard East-positive)
  const longitude = decodeJhdDegrees(-rawLon);
  const latitude = decodeJhdDegrees(rawLat);

  if (Math.abs(latitude) > 90) return fail(`Invalid latitude: ${latitude}`);
  if (Math.abs(longitude) > 180) return fail(`Invalid longitude: ${longitude}`);

  // Decode TimeZone: line 9 if present is often already decimal timezone (e.g. -5.500000).
  // Otherwise line 5 is in HH.MMSS format (e.g. -5.300000 -> -5h 30m = -5.5 hours).
  let tzHours: number;
  if (lines.length > 8 && !Number.isNaN(Number.parseFloat(lines[8])) && Math.abs(Number.parseFloat(lines[8])) <= 14) {
    tzHours = Number.parseFloat(lines[8]);
  } else {
    tzHours = decodeJhdDegrees(rawTz);
  }

  if (Math.abs(tzHours) > 24) return fail(`Invalid timezone offset: ${tzHours}`);

  const [h, m, s] = decodeJhdTime(rawTime);
  // Local wall-clock as a pure UTC-math instant (Date.UTC treats parts literally).
  const localMs = Date.UTC(year, month - 1, day, h, m, s);
  if (Number.isNaN(localMs)) return fail("The file's date/time could not be turned into a valid instant.");

  // Optional line 8 = DST correction hours (0 when absent).
  let dstHours = 0;
  if (lines.length > 7) {
    const d = Number.parseFloat(lines[7]);
    if (!Number.isNaN(d)) dstHours = d;
  }

  // UTC = local wall-clock + timezone offset (+ optional DST correction).
  const birthUtcMs = localMs + Math.round((tzHours + dstHours) * 3_600_000);
  const birthDatetimeUtc = new Date(birthUtcMs).toISOString();

  const subjectName = fileName.replace(/\.jhd$/i, "").trim() || "Imported chart";
  const birthLocal = `${year}-${pad(month)}-${pad(day)} ${pad(h)}:${pad(m)}${s > 0 ? `:${pad(s)}` : ""}`;

  // Extract optional place name from lines 13 and 14 if available
  let placeName: string | null = null;
  if (lines.length > 13) {
    const city = lines[12]?.trim();
    const country = lines[13]?.trim();
    const parts = [city, country].filter(
      (s) => s && !/^[\d.\-+]+$/.test(s) && s.toLowerCase() !== "unknown"
    );
    if (parts.length > 0) {
      placeName = parts.join(", ");
    }
  }

  const preview: JhdParsePreview = {
    subject_name: subjectName,
    birth_local: birthLocal,
    latitude,
    longitude,
    place_name: placeName,
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
    place_name: placeName,
  };

  return { request, preview, error: null };
}