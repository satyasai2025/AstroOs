import type { Metadata } from "next";
import { RegisterForm } from "@/components/auth/RegisterForm";
import Link from "next/link";

export const metadata: Metadata = { title: "Create Account" };

export default function RegisterPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm animate-slide-up">
        {/* Header */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-block mb-4">
            <span className="text-3xl font-bold text-white">
              Astro<span className="text-amber-400">OS</span>
            </span>
          </Link>
          <h1 className="text-xl font-semibold text-slate-100">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Join the research platform
          </p>
        </div>

        {/* Form card */}
        <div className="glass-card p-6">
          <RegisterForm />
        </div>

        <p className="mt-4 text-center text-sm text-slate-500">
          Have an account?{" "}
          <Link href="/login" className="text-amber-400 hover:text-amber-300 transition">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
