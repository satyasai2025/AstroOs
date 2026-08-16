import type { Metadata } from "next";
import { LoginForm } from "@/components/auth/LoginForm";
import Link from "next/link";

export const metadata: Metadata = { title: "Sign In" };

export default function LoginPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-12" style={{ backgroundColor: "var(--bg-primary)" }}>
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
              ASTRO<span style={{ color: "var(--accent)" }}>OS</span>
            </span>
          </Link>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Researcher Sign In
          </h1>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Access computational engines & research datasets
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
          <LoginForm />
        </div>
      </div>
    </div>
  );
}


