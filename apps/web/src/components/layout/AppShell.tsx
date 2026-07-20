"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCurrentUser, useLogout } from "@/lib/auth";
import { tokenStore } from "@/lib/api";
import { useTheme } from "./ThemeProvider";
import { ResearchModeToggle } from "@/components/research/ResearchModeToggle";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/charts", label: "Charts" },
  { href: "/charts/compare", label: "Compare" },
  { href: "/research/projects", label: "Research" },
] as const;

const RESEARCH_SUB_LINKS = [
  { href: "/research/projects", label: "Projects" },
  { href: "/research/hypotheses", label: "Hypotheses" },
] as const;

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
  const pathname = usePathname();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();
  const { theme, toggle } = useTheme();

  const hasToken = typeof window !== "undefined" && !!tokenStore.getAccess();

  useEffect(() => {
    if (!hasToken || isError) {
      router.replace("/login");
    }
  }, [hasToken, isError, router]);

  if (!hasToken || isLoading) {
    return (
      <div
        className="flex min-h-dvh items-center justify-center"
        style={{ backgroundColor: "var(--bg-primary)" }}
        role="status"
        aria-label="Loading"
      >
        <span
          className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-t-transparent"
          style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
        />
      </div>
    );
  }

  if (isError || !user) {
    return null; // redirect effect above is already firing
  }

  return (
    <div className="min-h-dvh" style={{ backgroundColor: "var(--bg-primary)" }}>
      <nav
        className="border-b backdrop-blur-md"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-card)",
        }}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-lg font-bold"
              style={{ color: "var(--text-primary)" }}
              aria-label="AstroOS home"
            >
              Astro<span style={{ color: "var(--accent)" }}>OS</span>
            </Link>

            <div className="hidden items-center gap-1 sm:flex" role="menubar">
              {NAV_LINKS.map((link) => {
                const isActive =
                  pathname === link.href ||
                  (link.href !== "/dashboard" && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    role="menuitem"
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                      isActive
                        ? "font-semibold"
                        : ""
                    }`}
                    style={{
                      backgroundColor: isActive ? "var(--accent)" : "transparent",
                      color: isActive ? "var(--accent-text)" : "var(--text-secondary)",
                    }}
                    aria-current={isActive ? "page" : undefined}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Mobile nav */}
            <select
              className="sm:hidden rounded-lg border px-2 py-1 text-xs"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
              }}
              value={pathname}
              onChange={(e) => router.push(e.target.value)}
              aria-label="Navigate to page"
            >
              {NAV_LINKS.map((link) => (
                <option key={link.href} value={link.href}>
                  {link.label}
                </option>
              ))}
            </select>

            <span className="hidden text-sm sm:inline" style={{ color: "var(--text-secondary)" }}>
              {user.display_name}{" "}
              <span
                className="rounded-full px-2 py-0.5 text-xs uppercase tracking-wide"
                style={{
                  border: "1px solid var(--border-primary)",
                  backgroundColor: "var(--bg-card)",
                  color: "var(--accent)",
                }}
              >
                {user.role}
              </span>
            </span>

            {/* Research Mode Toggle */}
            <ResearchModeToggle compact />

            {/* Dark mode toggle */}
            <button
              type="button"
              onClick={toggle}
              className="theme-toggle"
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2" />
                  <path d="M12 20v2" />
                  <path d="m4.93 4.93 1.41 1.41" />
                  <path d="m17.66 17.66 1.41 1.41" />
                  <path d="M2 12h2" />
                  <path d="M20 12h2" />
                  <path d="m6.34 17.66-1.41 1.41" />
                  <path d="m19.07 4.93-1.41 1.41" />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
                </svg>
              )}
            </button>

            <button
              type="button"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="btn-ghost text-xs px-3 py-1.5"
              aria-label="Sign out of account"
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
