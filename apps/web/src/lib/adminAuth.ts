/**
 * AstroOS — Admin Authentication API (TanStack Query)
 *
 * Separate from user auth (lib/auth.ts) — uses its own token
 * store (astro_admin_token) and calls /api/v1/admin/* endpoints.
 * The admin JWT token has an `admin: true` claim that the backend
 * verifies via the require_admin_user dependency.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "./api";
import type { AuthResponse, User } from "./types";

// ── Admin Token Store ────────────────────────────────────────────

const ADMIN_TOKEN_KEY = "astro_admin_token";
const ADMIN_REFRESH_KEY = "astro_admin_refresh";

/**
 * Separate token store for admin sessions.
 * Completely isolated from the user-facing tokenStore in lib/api.ts.
 */
export const adminTokenStore = {
  getAccess(): string | null {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem(ADMIN_TOKEN_KEY);
    } catch {
      return null; // storage access blocked by browser/privacy settings
    }
  },

  getRefresh(): string | null {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem(ADMIN_REFRESH_KEY);
    } catch {
      return null;
    }
  },

  set(access: string, refresh: string) {
    if (typeof window === "undefined") return;
    try {
      localStorage.setItem(ADMIN_TOKEN_KEY, access);
      localStorage.setItem(ADMIN_REFRESH_KEY, refresh);
    } catch {
      // storage access blocked — session won't persist across reloads
    }
  },

  clear() {
    if (typeof window === "undefined") return;
    try {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      localStorage.removeItem(ADMIN_REFRESH_KEY);
    } catch {
      // ignore
    }
  },
};

// ── API helper with admin token ──────────────────────────────────

async function adminApiRequest<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "";
  const token = adminTokenStore.getAccess();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${base}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(body.detail || `HTTP ${res.status}`, res.status);
  }

  return res.json();
}

// ── Admin API Client ──────────────────────────────────────────────

export const adminApi = {
  get: <T>(path: string) => adminApiRequest<T>("GET", path),
  post: <T>(path: string, body?: unknown) => adminApiRequest<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => adminApiRequest<T>("PATCH", path, body),
};

// ── Query Keys ───────────────────────────────────────────────────

export const adminAuthKeys = {
  me: ["admin-auth", "me"] as const,
};

// ── Admin Login ──────────────────────────────────────────────────

interface AdminLoginPayload {
  email: string;
  password: string;
  mfa_code?: string;
}

interface AdminLoginResponse {
  user: User;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  };
}

export function useAdminLogin() {
  const queryClient = useQueryClient();

  return useMutation<AdminLoginResponse, ApiError, AdminLoginPayload>({
    mutationFn: (payload) =>
      adminApiRequest<AdminLoginResponse>("POST", "/api/v1/admin/auth/login", payload),
    onSuccess: (data) => {
      adminTokenStore.set(data.tokens.access_token, data.tokens.refresh_token);
      queryClient.setQueryData(adminAuthKeys.me, data.user);
    },
  });
}

// ── Admin Logout ─────────────────────────────────────────────────

export function useAdminLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      try {
        await adminApiRequest("POST", "/api/v1/admin/auth/logout");
      } catch {
        // Logout is best-effort — clear tokens regardless
      }
    },
    onSettled: () => {
      adminTokenStore.clear();
      queryClient.removeQueries({ queryKey: adminAuthKeys.me });
    },
  });
}

// ── Current Admin User ───────────────────────────────────────────

export function useAdminCurrentUser() {
  return useQuery<User>({
    queryKey: adminAuthKeys.me,
    queryFn: () => adminApiRequest<User>("GET", "/api/v1/admin/auth/me"),
    enabled: !!adminTokenStore.getAccess(),
    retry: false,
  });
}
