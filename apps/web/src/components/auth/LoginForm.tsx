"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useLogin } from "@/lib/auth";
import { ApiError } from "@/lib/api";

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
          disabled={login.isPending}
        />
      </div>

      <div>
        <label htmlFor="password" className="field-label">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="field-input"
          placeholder="••••••••"
          disabled={login.isPending}
        />
      </div>

      {fieldError && (
        <p className="text-error animate-fade-in">{fieldError}</p>
      )}

      <button
        type="submit"
        disabled={login.isPending}
        className="btn-primary w-full mt-2"
      >
        {login.isPending ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-cosmos-800 border-t-transparent" />
            Signing in…
          </>
        ) : (
          "Sign In"
        )}
      </button>
    </form>
  );
}
