import type { Metadata } from "next";
import { RegisterForm } from "@/components/auth/RegisterForm";
import Link from "next/link";

export const metadata: Metadata = { title: "Create Account" };

export default function RegisterPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-4 py-12" style={{ backgroundColor: "var(--bg-primary)" }}>
      <div className="w-full max-w-sm animate-slide-up">
        {/* Header */}
        <div className="mb-6 text-center">
          <Link href="/" className="inline-flex items-center gap-2 mb-3">
            <span
              className="flex h-9 w-9 items-center justify-center rounded-lg text-sm font-bold shadow-sm"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              ॐ
            </span>
            <span className="text-2xl font-bold tracking-wide" style={{ color: "var(--text-primary)" }}>
              ASTRO<span className="text-cyan-700 dark:text-cyan-400 font-bold">OS</span>
            </span>
          </Link>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Create your account
          </h1>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Join the research platform
          </p>
        </div>

        {/* Form card */}
        <div
          className="rounded-xl border p-6 shadow-sm"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <RegisterForm />
        </div>

        <p className="mt-4 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
          Have an account?{" "}
          <Link href="/login" className="underline underline-offset-4 transition font-medium text-cyan-700 dark:text-cyan-400">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
