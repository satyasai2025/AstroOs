/**
 * AstroOS API Client
 *
 * Thin wrapper around fetch that:
 * - Prepends the API base URL
 * - Attaches the Authorization header from the token store
 * - Handles 401 → token refresh → retry (once)
 * - Normalises errors into ApiError instances
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

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
  return undefined;
}

// ── Token storage (client-side only) ─────────────────────────────────────────

const TOKEN_KEY = "astro_access_token";
const REFRESH_KEY = "astro_refresh_token";

export const tokenStore = {
  getAccess: (): string | null =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null,

  getRefresh: (): string | null =>
    typeof window !== "undefined" ? localStorage.getItem(REFRESH_KEY) : null,

  set: (access: string, refresh: string): void => {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },

  clear: (): void => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
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

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  // Attempt token refresh on first 401
  if (res.status === 401 && _retry) {
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
  return res.json() as Promise<T>;
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