"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { useCurrentUser, useLogout } from "@/lib/auth";
import { tokenStore } from "@/lib/api";

/**
 * Wraps every authenticated page: redirects to /login if there's no
 * valid session, otherwise renders the top nav + the page content.
 *
 * Client-side only guard (no middleware.ts in this app) — matches the
 * rest of the auth flow, which is entirely token-in-localStorage +
 * TanStack Query, not cookie/session based.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();

  const hasToken = typeof window !== "undefined" && !!tokenStore.getAccess();

  useEffect(() => {
    if (!hasToken || isError) {
      router.replace("/login");
    }
  }, [hasToken, isError, router]);

  if (!hasToken || isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
      </div>
    );
  }

  if (isError || !user) {
    return null; // redirect effect above is already firing
  }

  return (
    <div className="min-h-dvh">
      <nav className="border-b border-white/10 bg-cosmos-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="text-lg font-bold text-white">
            Astro<span className="text-amber-400">OS</span>
          </Link>

          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-slate-400 sm:inline">
              {user.display_name}{" "}
              <span className="rounded-full border border-cosmos-600/40 bg-cosmos-800/40 px-2 py-0.5 text-xs uppercase tracking-wide text-amber-300/80">
                {user.role}
              </span>
            </span>
            <button
              type="button"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="btn-ghost text-xs px-3 py-1.5"
            >
              {logout.isPending ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
