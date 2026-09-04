/**
 * AstroOS — Timezone-aware wall-clock conversions.
 *
 * `Date` only ever parses/formats in the *browser's* local timezone (or
 * UTC with a 'Z'/offset suffix) — there's no built-in "parse this
 * wall-clock string as if it were in timezone X" function. These
 * implement that using the standard Intl.DateTimeFormat round-trip
 * trick (the same technique libraries like date-fns-tz use internally),
 * so a user's saved account timezone (Settings > Profile) can be honored
 * instead of silently assuming the browser's timezone.
 */

/**
 * Interpret a "YYYY-MM-DDTHH:mm" wall-clock string as a moment in
 * `timeZone`, returning the equivalent UTC ISO string.
 */
export function zonedDatetimeLocalToUtcIso(datetimeLocal: string, timeZone: string): string {
  const [datePart, timePart] = datetimeLocal.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  const [hh = 0, mm = 0] = (timePart ?? "").split(":").map(Number);

  // First guess: treat the wall-clock numbers as if they were UTC.
  const guessMs = Date.UTC(y, m - 1, d, hh, mm);

  // Find what that guessed instant reads as inside `timeZone`, then use
  // the difference to correct the guess — this naturally accounts for
  // DST since it's evaluated at the guessed instant, not "now".
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts = Object.fromEntries(dtf.formatToParts(new Date(guessMs)).map((p) => [p.type, p.value]));
  const readingAsUtcMs = Date.UTC(
    Number(parts.year),
    Number(parts.month) - 1,
    Number(parts.day),
    Number(parts.hour === "24" ? "0" : parts.hour),
    Number(parts.minute),
    Number(parts.second),
  );
  const offsetMs = readingAsUtcMs - guessMs;
  return new Date(guessMs - offsetMs).toISOString();
}

/** ISO UTC string → "YYYY-MM-DDTHH:mm" wall-clock string as it reads in `timeZone`. */
export function utcIsoToZonedDatetimeLocalValue(iso: string, timeZone: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  const parts = Object.fromEntries(dtf.formatToParts(d).map((p) => [p.type, p.value]));
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour === "24" ? "00" : parts.hour}:${parts.minute}`;
}

/** ISO UTC string → "YYYY-MM-DD" date-only string as it reads in `timeZone`. */
export function utcIsoToZonedDateValue(iso: string, timeZone: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const parts = Object.fromEntries(dtf.formatToParts(d).map((p) => [p.type, p.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}
