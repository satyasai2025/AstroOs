/**
 * AstroOS API Client
 *
 * Thin wrapper around fetch that:
 * - Prepends the API base URL
 * - Attaches the Authorization header from the token store
 * - Handles 401 → token refresh → retry (once)
 * - Normalises errors into ApiError instances
 * - Normalises planet/sign/nakshatra casing (see _normalizeAstroCasing below)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * The backend's internal domain layer uses lowercase tokens for grahas and
 * rashis throughout (apps/api/services/ephemeris_wrapper.py's GRAHA_ORDER
 * etc. — confirmed by reading the code: "sun", "moon", "mesha", ...), and
 * nothing capitalizes them before they're serialized into API responses.
 * Every frontend component (old and new) that displays these values or
 * matches them against the capitalized constants in lib/astro.ts (e.g.
 * PLANET_SYMBOLS["Sun"], RASHI_LORDS["Mesha"]) was written assuming
 * Title-Case input. Rather than patch every consumer individually — and
 * definitely rather than touch the backend's internal lowercase-keyed
 * lookups (dignity tables, combustion checks, etc. all depend on the raw
 * lowercase values staying exactly as-is internally) — this normalizes
 * casing ONCE, generically, at the one place every response passes
 * through: right after JSON parsing, before any component sees the data.
 *
 * Deliberately scoped to a fixed, explicit list of field names that are
 * known to carry a single planet/rashi/nakshatra token (or a short
 * space-separated one, e.g. "purva phalguni" -> "Purva Phalguni"). Fields
 * NOT in this list are left untouched — notably "graha" (the Karakatva
 * Explorer's lib/karakatva.ts already expects the DB's lowercase enum
 * values there), "role", "status", "category", and every enum-code field
 * (ayanamsa, house_system, dasha_system) that other code matches exactly
 * against its lowercase/coded form.
 */
const _ASTRO_CASING_KEYS = new Set([
  "planet",
  "from_planet",
  "to_planet",
  "lord",
  "trigger_planet",
  "vedha_planet",
  "rashi",
  "varga_rashi",
  "d1_rashi",
  "natal_moon_rashi",
  "transit_rashi",
  "lagna_rashi",
  "navamsa_rashi",
  "nakshatra",
  "moon_nakshatra",
  "trigger_nakshatra",
  "nakshatra_lord",
  "sub_lord",
  "sub_sub_lord",
  // Added after the retroactive domain-correctness review (2026-07-23)
  // found these two: YogaResultResponse.involved_planets (string[]) and
  // BhinnashtakavargaResponse.target_planet (string) both carry lowercase
  // planet tokens from the backend and were silently missed by the
  // original casing fix — involved_planets in particular caused
  // PlanetDetailPanel's "yogas involving this planet" cross-reference to
  // always return empty, since it compared a normalized (capitalized)
  // planet name against un-normalized lowercase array entries.
  "involved_planets",
  "target_planet",
  // Added for Nakshatra Vedha / Sarvatobhadra Chakra (2026-07-23) — same
  // lowercase-token issue, on 3 new TransitPlanetResponse fields.
  "nakshatra_vedha_planet",
  "nakshatra_vedha_target",
  "transit_nakshatra_sbc",
  // Added for /transit/patterns (TransitAspectResponse) — same lowercase-
  // token issue, on the two planet fields of each detected aspect.
  "transiting_planet",
  "natal_planet",
  // Added for the Transit Analysis console's detailed positions table
  // (2026-07-30) — same lowercase-token issue, on the standard 27-system
  // nakshatra field (distinct from transit_nakshatra_sbc above).
  "transit_nakshatra",
  // Added for the Jaimini router (routers/jaimini.py) — same lowercase-
  // token issue, on every rashi/planet-array field the bundle/argala
  // responses carry that isn't already covered above. Deliberately NOT
  // adding the bare "planets" key here (KarakamsaHouseEntrySchema) since
  // that generic a name risks colliding with an unrelated field
  // elsewhere expecting different casing; JaiminiPanel normalizes that
  // one locally instead.
  "from_rashi",
  "to_rashi",
  "raw_rashi",
  "lord_rashi",
  "karakamsa_rashi",
  "swamsa_rashi",
  "d1_atmakaraka_rashi",
  "d1_lagna_rashi",
  "argala_rashi",
  "virodhargala_rashi",
  "reference_rashi",
  "aspecting_planets",
  "aspected_planets",
  "argala_planets",
  "virodhargala_planets",
  // Added for the backend KP Analysis engine (POST /api/v1/kp/analyze,
  // 2026-08-11) — the KP response carries the same lowercase planet tokens
  // in its cusp/planet lord fields, the CSL decision chain, the ruling
  // planet triggers, the transit trigger fields, and the evidence
  // top-significator / RP-intersection fields. All of them feed displays
  // that match against the Title-Case constants in lib/astro.ts, so they
  // must be normalized here exactly like the other planet-bearing keys.
  "sign_lord",
  "star_lord",
  "transit_star_lord",
  "transit_sub_lord",
  "transit_planet",
  "csl",
  "csl_star_lord",
  "rp",
  "matched_significator",
  "top_significator",
  "activated",
  "occupants",
  "significators",
  "fruitful_rp_intersection",
]);

/**
 * Fixed 2026-07-23 (found while wiring Nakshatra Vedha, which passes
 * multi-word nakshatra tokens like "purva_phalguni" through this same
 * path): the backend's Nakshatra enum values are snake_case
 * ("purva_phalguni"), not space-separated ("purva phalguni") like this
 * function originally assumed — splitting only on " " left the
 * underscore in place, producing "Purva_phalguni" instead of "Purva
 * Phalguni" for all 12 of the 27 nakshatras that are two words. That
 * silently broke any exact-match lookup keyed by the properly-spaced
 * name (e.g. lib/astro.ts's karakatva/nakshatra-lord tables) for those
 * 12 nakshatras specifically — single-word nakshatras were unaffected,
 * which is presumably why it went unnoticed. Now replaces underscores
 * with spaces before splitting.
 *
 * Exported as the one canonical title-casing helper — several
 * components independently reimplemented a near-identical version of
 * this before consolidating onto it (see e.g. ChartDetailPanel.tsx,
 * EventTimelineChart.tsx, research/import/page.tsx's git history).
 */
export function titleCaseToken(value: string): string {
  return value
    .replace(/_/g, " ")
    .split(" ")
    .map((word) => (word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase() : word))
    .join(" ");
}

const _titleCaseToken = titleCaseToken;

/**
 * keyHint carries the object key this value was found under, one level
 * up. It's needed because arrays of strings (e.g. involved_planets:
 * string[]) don't carry their own "key" once you're inside
 * Array.prototype.map — without threading the parent key through, an
 * array field in _ASTRO_CASING_KEYS would only ever recurse into
 * _normalizeAstroCasing(item) for each string item with no key context,
 * hit the plain-string fallback at the bottom, and return unchanged.
 * (Found in the 2026-07-23 domain review — involved_planets was added to
 * the key set in an earlier pass but never actually took effect because
 * of this gap.)
 */
function _normalizeAstroCasing(value: unknown, keyHint?: string): unknown {
  if (Array.isArray(value)) {
    if (keyHint && _ASTRO_CASING_KEYS.has(keyHint)) {
      return value.map((item) => (typeof item === "string" ? _titleCaseToken(item) : _normalizeAstroCasing(item)));
    }
    return value.map((item) => _normalizeAstroCasing(item));
  }
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, v] of Object.entries(value as Record<string, unknown>)) {
      out[key] = typeof v === "string" && _ASTRO_CASING_KEYS.has(key) ? _titleCaseToken(v) : _normalizeAstroCasing(v, key);
    }
    return out;
  }
  return value;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

/**
 * FastAPI's error response `detail` field has two possible shapes:
 *  - A plain string, for hand-raised HTTPException(detail="...") errors
 *    (e.g. "Email already registered").
 *  - An array of Pydantic validation error objects, for automatic 422
 *    responses: [{ type, loc, msg, input, ctx }, ...].
 *
 * Components must only ever receive a string — rendering the array form
 * directly as a React child throws "Objects are not valid as a React
 * child". This normalises both shapes into one human-readable string.
 */
function _normaliseErrorDetail(detail: unknown): string | undefined {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : null,
      )
      .filter((msg): msg is string => Boolean(msg));
    return messages.length > 0 ? messages.join(" ") : undefined;
  }
  if (detail && typeof detail === "object") {
    if ("message" in detail && typeof (detail as { message: unknown }).message === "string") {
      return (detail as { message: string }).message;
    }
    if ("detail" in detail && typeof (detail as { detail: unknown }).detail === "string") {
      return (detail as { detail: string }).detail;
    }
  }
  return undefined;
}

// ── Token storage (client-side only) ─────────────────────────────────────────

const TOKEN_KEY = "astro_access_token";
const REFRESH_KEY = "astro_refresh_token";

export const tokenStore = {
  getAccess: (): string | null => {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null; // storage access blocked by browser/privacy settings
    }
  },

  getRefresh: (): string | null => {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem(REFRESH_KEY);
    } catch {
      return null;
    }
  },

  set: (access: string, refresh: string): void => {
    if (typeof window === "undefined") return;
    try {
      localStorage.setItem(TOKEN_KEY, access);
      localStorage.setItem(REFRESH_KEY, refresh);
    } catch {
      // storage access blocked — session won't persist across reloads
    }
  },

  clear: (): void => {
    if (typeof window === "undefined") return;
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      // ignore
    }
  },
};

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function _fetch<T>(
  path: string,
  init: RequestInit = {},
  _retry = true,
): Promise<T> {
  const access = tokenStore.getAccess();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (access) {
    headers["Authorization"] = `Bearer ${access}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    // fetch() itself threw — the server was unreachable (down, restarting,
    // offline), not an HTTP error response. Surface this distinctly so
    // callers don't fall through to a generic "unexpected error" branch.
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }

  // Attempt token refresh on first 401
  if (res.status === 401 && _retry) {
    if (path.includes("/auth/login") || path.includes("/auth/register") || path.includes("/auth/refresh")) {
      let detail = "Invalid email or password.";
      try {
        const body = await res.json();
        detail = _normaliseErrorDetail(body.detail) ?? detail;
      } catch {
        // ignore JSON parse errors
      }
      throw new ApiError(401, detail);
    }

    const refreshed = await _tryRefresh();
    if (refreshed) {
      return _fetch<T>(path, init, false);
    }
    tokenStore.clear();
    window.location.href = "/login";
    throw new ApiError(401, "Session expired.");
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = _normaliseErrorDetail(body.detail) ?? detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text || text.trim() === "") return undefined as T;
  try {
    const json = JSON.parse(text);
    return _normalizeAstroCasing(json) as T;
  } catch {
    return text as unknown as T;
  }
}

async function _tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return false;
  try {
    const data = await _fetch<{ access_token: string; refresh_token: string }>(
      "/api/v1/auth/refresh",
      {
        method: "POST",
        body: JSON.stringify({ refresh_token: refresh }),
      },
      false, // no retry loop on refresh itself
    );
    tokenStore.set(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ── Public API methods ────────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string) => _fetch<T>(path, { method: "GET" }),
  post: <T>(path: string, body: unknown) =>
    _fetch<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    _fetch<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    _fetch<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => _fetch<T>(path, { method: "DELETE" }),
} as const;