"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useRegister } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export function RegisterForm() {
  const router = useRouter();
  const register = useRegister();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldError(null);

    try {
      await register.mutateAsync({
        email: email.trim().toLowerCase(),
        display_name: displayName.trim(),
        password,
      });
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
        <label htmlFor="displayName" className="field-label">
          Display Name
        </label>
        <input
          id="displayName"
          type="text"
          autoComplete="name"
          required
          minLength={2}
          maxLength={100}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="field-input"
          placeholder="Your name"
          disabled={register.isPending}
        />
      </div>

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
          disabled={register.isPending}
        />
      </div>

      <div>
        <label htmlFor="password" className="field-label">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="field-input"
          placeholder="Min. 8 chars with upper, lower & digit"
          disabled={register.isPending}
        />
      </div>

      {fieldError && (
        <p className="text-error animate-fade-in">{fieldError}</p>
      )}

      <button
        type="submit"
        disabled={register.isPending}
        className="btn-primary w-full mt-2"
      >
        {register.isPending ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-cosmos-800 border-t-transparent" />
            Creating account…
          </>
        ) : (
          "Create Account"
        )}
      </button>
    </form>
  );
}
