import type { Metadata } from "next";
import { LoginForm } from "@/components/auth/LoginForm";
import Link from "next/link";

export const metadata: Metadata = { title: "Sign In" };

export default function LoginPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm animate-slide-up">
        {/* Header */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-block mb-4">
            <span className="text-3xl font-bold" style={{ color: "var(--obsidian-text-primary)" }}>
              Astro
              <span style={{ color: "var(--obsidian-accent-secondary)" }}>OS</span>
            </span>
          </Link>
          <h1 className="text-2xl font-bold" style={{ color: "var(--obsidian-text-primary)" }}>
            Welcome back
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--obsidian-text-muted)" }}>
            Sign in to your research account
          </p>
        </div>

        {/* Form card */}
        <div className="glass-card p-6">
          <LoginForm />
        </div>

        <p className="mt-4 text-center text-sm" style={{ color: "var(--obsidian-text-muted)" }}>
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-medium transition"
            style={{ color: "var(--obsidian-accent-primary)" }}
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
