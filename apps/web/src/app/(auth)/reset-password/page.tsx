import type { Metadata } from "next";
import { Suspense } from "react";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";
import Link from "next/link";

export const dynamic = "force-dynamic";

export const metadata: Metadata = { title: "Reset Password" };

export default function ResetPasswordPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm animate-slide-up">
        {/* Header */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-block mb-4">
            <span className="text-3xl font-bold text-white">
              Astro<span className="text-amber-400">OS</span>
            </span>
          </Link>
          <h1 className="text-xl font-semibold text-slate-100">Set a new password</h1>
          <p className="mt-1 text-sm text-slate-400">
            Choose a new password for your account
          </p>
        </div>

        {/* Form card */}
        <div className="glass-card p-6">
          <Suspense fallback={null}>
            <ResetPasswordForm />
          </Suspense>
        </div>

        <p className="mt-4 text-center text-sm text-slate-500">
          Remembered your password?{" "}
          <Link href="/login" className="text-amber-400 hover:text-amber-300 transition">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
