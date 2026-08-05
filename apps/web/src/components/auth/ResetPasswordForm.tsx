"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useResetPassword } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const resetPassword = useResetPassword();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldError(null);

    if (newPassword !== confirmPassword) {
      setFieldError("Passwords do not match.");
      return;
    }

    try {
      await resetPassword.mutateAsync({ token, new_password: newPassword });
      router.push("/login");
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldError(err.detail);
      } else {
        setFieldError("An unexpected error occurred. Please try again.");
      }
    }
  };

  if (!token) {
    return (
      <p className="text-error animate-fade-in">
        This reset link is missing its token. Request a new one from the{" "}
        <a href="/forgot-password" className="text-amber-400 hover:text-amber-300 transition">
          forgot password
        </a>{" "}
        page.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="newPassword" className="field-label">
          New Password
        </label>
        <input
          id="newPassword"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="field-input"
          placeholder="Min. 8 chars with upper, lower & digit"
          disabled={resetPassword.isPending}
        />
      </div>

      <div>
        <label htmlFor="confirmPassword" className="field-label">
          Confirm New Password
        </label>
        <input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="field-input"
          placeholder="••••••••"
          disabled={resetPassword.isPending}
        />
      </div>

      {fieldError && (
        <p className="text-error animate-fade-in">{fieldError}</p>
      )}

      <button
        type="submit"
        disabled={resetPassword.isPending}
        className="btn-primary w-full mt-2"
      >
        {resetPassword.isPending ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-cosmos-800 border-t-transparent" />
            Resetting…
          </>
        ) : (
          "Reset Password"
        )}
      </button>
    </form>
  );
}
