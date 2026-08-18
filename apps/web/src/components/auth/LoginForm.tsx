"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useLogin } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { SHOW_BETA_FEATURES } from "@/config/navConfig";

export function LoginForm() {
  const router = useRouter();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldError(null);

    try {
      await login.mutateAsync({ email: email.trim().toLowerCase(), password });
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldError(err.detail);
      } else {
        setFieldError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="field-label mb-1 block text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
          Email address
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="field-input w-full rounded-lg border px-3 py-2 text-sm transition focus:outline-none"
          style={{
            borderColor: "var(--border-secondary, var(--border-primary))",
            backgroundColor: "var(--bg-primary)",
            color: "var(--text-primary)",
          }}
          placeholder="researcher@astroos.org"
          disabled={login.isPending}
        />
      </div>

      <div>
        <label htmlFor="password" className="field-label mb-1 block text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="field-input w-full rounded-lg border px-3 py-2 text-sm transition focus:outline-none"
          style={{
            borderColor: "var(--border-secondary, var(--border-primary))",
            backgroundColor: "var(--bg-primary)",
            color: "var(--text-primary)",
          }}
          placeholder="••••••••"
          disabled={login.isPending}
        />
      </div>

      {fieldError && (
        <div
          className="rounded-lg border p-2.5 text-xs animate-fade-in"
          style={{
            borderColor: "var(--error, #ef4444)",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            color: "var(--error, #ef4444)",
          }}
        >
          {fieldError}
        </div>
      )}

      <button
        type="submit"
        disabled={login.isPending}
        className="btn-primary w-full py-2.5 text-sm font-semibold transition"
      >
        {login.isPending ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-t-transparent" />
            Signing in…
          </span>
        ) : (
          "Sign in"
        )}
      </button>

      {/* ── Centered Forgot password link below button (matching reference) ── */}
      <div className="text-center pt-0.5">
        <Link
          href="/forgot-password"
          className="text-xs transition hover:underline font-medium text-cyan-700 dark:text-cyan-400"
        >
          Forgot password?
        </Link>
      </div>

      {/* ── Divider ── */}
      <div className="flex items-center gap-3 py-1" aria-hidden="true">
        <span className="h-px flex-1" style={{ background: "var(--border-primary)" }} />
        <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          or
        </span>
        <span className="h-px flex-1" style={{ background: "var(--border-primary)" }} />
      </div>

      {/* ── Create New Account CTA Button ── */}
      <Link
        href="/register"
        className="flex w-full items-center justify-center rounded-lg border py-2.5 text-xs font-semibold shadow-sm transition hover:bg-[var(--border-primary)]"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-primary)",
          color: "var(--text-primary)",
        }}
      >
        Create new account
      </Link>

      {/* ── Feature Flagged Google Sign In ── */}
      {SHOW_BETA_FEATURES && (
        <button
          type="button"
          disabled
          title="Google sign-in isn't available yet"
          className="flex w-full items-center justify-center gap-2 rounded-lg border py-2 text-xs font-medium opacity-60 cursor-not-allowed mt-2"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-primary)",
            color: "var(--text-secondary)",
          }}
        >
          <GoogleIcon />
          <span>Sign in with Google</span>
          <span
            className="ml-1 rounded px-1.5 py-0.5 text-[9px] uppercase tracking-wide border"
            style={{ borderColor: "var(--border-primary)" }}
          >
            Soon
          </span>
        </button>
      )}
    </form>
  );
}



function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0012 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09A6.6 6.6 0 015.5 12c0-.73.13-1.43.34-2.09V7.06H2.18A11 11 0 001 12c0 1.77.43 3.45 1.18 4.94l3.66-2.85z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 002.18 7.06l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z"
      />
    </svg>
  );
}
