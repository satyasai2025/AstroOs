/**
 * AstroOS — Shared TypeScript Types
 *
 * Mirror of the FastAPI response schemas.
 * Keep in sync with apps/api/schemas/*.py manually until an
 * OpenAPI codegen step is added in a later module.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "guest" | "researcher" | "admin";
  status: "active" | "suspended" | "pending_verification";
  created_at: string;
  last_login_at: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface RegisterPayload {
  email: string;
  display_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

// ── API Error ─────────────────────────────────────────────────────────────────

export interface ApiErrorBody {
  detail: string;
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
}
