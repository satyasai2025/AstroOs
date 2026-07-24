/**
 * AstroOS — Admin Login Form
 *
 * Separate authentication interface for admin panel.
 * Styled with indigo/violet theme to distinguish from user-facing login.
 */

"use client";

import { useEffect, useState } from "react";
import { useAdminLogin } from "@/lib/adminAuth";
import { ApiError } from "@/lib/api";

interface AdminLoginFormProps {
  onSuccess?: () => void;
  mfaRequired?: boolean;
}

export function AdminLoginForm({ onSuccess, mfaRequired }: AdminLoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [showMfa, setShowMfa] = useState(mfaRequired);

  const loginMutation = useAdminLogin();

  useEffect(() => {
    if (loginMutation.isSuccess && onSuccess) {
      onSuccess();
    }
  }, [loginMutation.isSuccess, onSuccess]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const payload: { email: string; password: string; mfa_code?: string } = {
      email,
      password,
    };
    if (showMfa) {
      payload.mfa_code = mfaCode;
    }

    loginMutation.mutate(payload);
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <form
        onSubmit={handleSubmit}
        className="bg-[var(--bg-card)] border border-[var(--border-primary)] rounded-lg p-6 shadow-lg"
      >
        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
            Admin Portal
          </h2>
          <p className="text-sm text-[var(--text-muted)]">
            Authorized personnel only
          </p>
        </div>

        {/* Security Badge */}
        <div className="mb-4 p-3 bg-[rgba(124,58,237,0.1)] border border-[rgba(124,58,237,0.3)] rounded-md">
          <p className="text-xs text-[rgba(139,92,246,0.9)] text-center">
            <strong>Security Notice:</strong> This portal requires elevated
            privileges. All actions are logged.
          </p>
        </div>

        {/* Email */}
        <div className="mb-4">
          <label
            htmlFor="email"
            className="block text-sm font-medium text-[var(--text-secondary)] mb-1"
          >
            Admin Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loginMutation.isPending}
            className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent disabled:opacity-50"
            placeholder="admin@astroos.dev"
          />
        </div>

        {/* Password */}
        <div className="mb-4">
          <label
            htmlFor="password"
            className="block text-sm font-medium text-[var(--text-secondary)] mb-1"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loginMutation.isPending}
            className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent disabled:opacity-50"
            placeholder="••••••••"
          />
        </div>

        {/* MFA Code (conditionally shown) */}
        {showMfa && (
          <div className="mb-4">
            <label
              htmlFor="mfaCode"
              className="block text-sm font-medium text-[var(--text-secondary)] mb-1"
            >
              MFA Code
            </label>
            <input
              id="mfaCode"
              type="text"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              required
              disabled={loginMutation.isPending}
              className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-md text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent disabled:opacity-50"
              placeholder="123456"
              maxLength={6}
            />
          </div>
        )}

        {/* Error Display */}
        {loginMutation.error && (
          <div className="mb-4 p-3 bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.3)] rounded-md">
            <p className="text-sm text-[var(--status-danger)]">
              {(loginMutation.error as ApiError).message || "Login failed"}
            </p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="w-full py-2 px-4 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--accent-text)] font-semibold rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loginMutation.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Authenticating...
            </span>
          ) : (
            "Access Admin Panel"
          )}
        </button>

        {/* Footer */}
        <div className="mt-4 text-center">
          <p className="text-xs text-[var(--text-muted)]">
            By accessing this system, you agree to all audit and monitoring policies.
          </p>
        </div>
      </form>
    </div>
  );
}
