"use client";

import { useState } from "react";
import { useForgotPassword } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export function ForgotPasswordForm() {
  const forgotPassword = useForgotPassword();
  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldError(null);

    try {
      await forgotPassword.mutateAsync({ email: email.trim().toLowerCase() });
      setSent(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldError(err.detail);
      } else {
        setFieldError("An unexpected error occurred. Please try again.");
      }
    }
  };

  if (sent) {
    return (
      <p className="text-sm text-slate-300 animate-fade-in">
        If an account exists for <span className="text-slate-100">{email}</span>,
        a password reset link has been sent. Check your inbox.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="field-label">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="field-input"
          placeholder="you@example.com"
          disabled={forgotPassword.isPending}
        />
      </div>

      {fieldError && (
        <p className="text-error animate-fade-in">{fieldError}</p>
      )}

      <button
        type="submit"
        disabled={forgotPassword.isPending}
        className="btn-primary w-full mt-2"
      >
        {forgotPassword.isPending ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-cosmos-800 border-t-transparent" />
            Sending…
          </>
        ) : (
          "Send Reset Link"
        )}
      </button>
    </form>
  );
}
