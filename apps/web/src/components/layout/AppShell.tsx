"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCurrentUser, useLogout } from "@/lib/auth";
import { tokenStore } from "@/lib/api";
import { useTheme } from "./ThemeProvider";
import { ResearchModeToggle } from "@/components/research/ResearchModeToggle";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  /** True for mockup-inspired items that don't have a real page/view yet
   * — shown greyed out with a "Soon" tag rather than linking nowhere or
   * being silently omitted. Keeps the section layout intact and honest
   * about what's actually built. */
  disabled?: boolean;
  adminOnly?: boolean;
}

interface NavSection {
  title: string;
  /** CSS custom-property name (see globals.css --section-*) — the mockup's
   * top legend color-codes each of these areas (Dashboard=blue, Chart
   * Workspace=orange, Research=purple, AI & Insights=pink, Admin=neutral),
   * so each sidebar section gets its own accent instead of one global
   * color everywhere. */
  color: string;
  items: NavItem[];
}

/**
 * Sidebar nav map (2026-07-24 redesign, rainbow-per-section palette added
 * 2026-07-24). Every enabled item points at a real, working route — the
 * 9-tab /charts page doesn't have separate routes per view, so Analysis
 * items deep-link via ?view=, which apps/charts/page.tsx now reads on
 * mount (see useSearchParams effect there). Items with no real backing
 * page/view (Import Chart, Yogas & Combinations, Ashtakavarga, Jaimini
 * Analysis, the AI & Insights pages, Knowledge Base, Pattern Discovery,
 * Case Studies, Settings, Documentation) are marked disabled rather than
 * fabricated — this app's standing rule is not to build UI that implies a
 * feature exists when it doesn't.
 */
const NAV_SECTIONS: NavSection[] = [
  {
    title: "Charts",
    color: "--section-charts",
    items: [
      { href: "/dashboard", label: "New Chart", icon: "plus" },
      { href: "/charts/history", label: "My Charts", icon: "grid" },
      { href: "/charts/compare", label: "Compare Charts", icon: "layers" },
      { href: "#", label: "Import Chart", icon: "upload", disabled: true },
    ],
  },
  {
    title: "Analysis",
    color: "--section-analysis",
    items: [
      { href: "/charts?view=chart", label: "Birth Chart", icon: "compass" },
      { href: "/charts?view=chart", label: "Divisional Charts", icon: "grid" },
      { href: "/charts?view=relationships", label: "Planet Relationship Graph", icon: "network" },
      { href: "/charts?view=houses", label: "House Dependency", icon: "network" },
      { href: "/charts?view=dasha", label: "Dasha Analysis", icon: "clock" },
      { href: "/charts?view=timeline", label: "Transit Analysis", icon: "orbit" },
      { href: "#", label: "Yogas & Combinations", icon: "star", disabled: true },
      { href: "#", label: "Ashtakavarga", icon: "grid", disabled: true },
      { href: "/charts?view=strength", label: "Shadbala", icon: "bar" },
      { href: "/charts?view=kp", label: "KP Analysis", icon: "target" },
      { href: "#", label: "Jaimini Analysis", icon: "book", disabled: true },
    ],
  },
  {
    title: "Research",
    color: "--section-research",
    items: [
      { href: "#", label: "Knowledge Base", icon: "book", disabled: true },
      { href: "/research/projects", label: "Research Explorer", icon: "search" },
      { href: "#", label: "Pattern Discovery", icon: "sparkle", disabled: true },
      { href: "#", label: "Case Studies", icon: "document", disabled: true },
      { href: "/research/projects", label: "Snapshot Manager", icon: "camera" },
    ],
  },
  {
    title: "AI & Insights",
    color: "--section-ai",
    items: [
      { href: "#", label: "AI Explain", icon: "sparkle", disabled: true },
      { href: "#", label: "AI Predictions", icon: "sparkle", disabled: true },
      { href: "#", label: "AI Research Assistant", icon: "sparkle", disabled: true },
    ],
  },
  {
    title: "System",
    color: "--section-system",
    items: [
      { href: "#", label: "Settings", icon: "gear", disabled: true },
      { href: "/admin", label: "Audit & Logs", icon: "shield", adminOnly: true },
      { href: "#", label: "Documentation", icon: "document", disabled: true },
    ],
  },
];

const _FLAT_LINKS = NAV_SECTIONS.flatMap((s) => s.items).filter((i) => !i.disabled);

function NavIcon({ name }: { name: string }) {
  const common = {
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  switch (name) {
    case "plus":
      return (
        <svg {...common}>
          <path d="M12 5v14M5 12h14" />
        </svg>
      );
    case "grid":
      return (
        <svg {...common}>
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      );
    case "layers":
      return (
        <svg {...common}>
          <path d="m12 3 9 5-9 5-9-5 9-5Z" />
          <path d="m3 13 9 5 9-5" />
        </svg>
      );
    case "upload":
      return (
        <svg {...common}>
          <path d="M12 16V4M6 10l6-6 6 6" />
          <path d="M4 20h16" />
        </svg>
      );
    case "compass":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="m15 9-2 6-6 2 2-6 6-2Z" />
        </svg>
      );
    case "network":
      return (
        <svg {...common}>
          <circle cx="6" cy="6" r="2.3" />
          <circle cx="18" cy="6" r="2.3" />
          <circle cx="12" cy="18" r="2.3" />
          <path d="M8 7.2 16 7.2M7 8l4 8M17 8l-4 8" />
        </svg>
      );
    case "clock":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 3" />
        </svg>
      );
    case "orbit":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="2.5" />
          <ellipse cx="12" cy="12" rx="9" ry="4" />
        </svg>
      );
    case "star":
      return (
        <svg {...common}>
          <path d="m12 3 2.6 6.2L21 10l-5 4.3L17.4 21 12 17.5 6.6 21 8 14.3 3 10l6.4-.8L12 3Z" />
        </svg>
      );
    case "bar":
      return (
        <svg {...common}>
          <path d="M5 20V10M12 20V4M19 20v-7" />
        </svg>
      );
    case "target":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <circle cx="12" cy="12" r="4" />
          <circle cx="12" cy="12" r="0.6" fill="currentColor" />
        </svg>
      );
    case "book":
      return (
        <svg {...common}>
          <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" />
          <path d="M4 5.5v16" />
        </svg>
      );
    case "search":
      return (
        <svg {...common}>
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
      );
    case "sparkle":
      return (
        <svg {...common}>
          <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
          <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
        </svg>
      );
    case "camera":
      return (
        <svg {...common}>
          <rect x="3" y="7" width="18" height="13" rx="2" />
          <path d="M8 7 10 4h4l2 3" />
          <circle cx="12" cy="13.5" r="3.2" />
        </svg>
      );
    case "gear":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 13a7.4 7.4 0 0 0 0-2l2-1.5-2-3.4-2.3.9a7.6 7.6 0 0 0-1.7-1L15 3.5h-4l-.4 2.5a7.6 7.6 0 0 0-1.7 1l-2.3-.9-2 3.4L6.6 11a7.4 7.4 0 0 0 0 2l-2 1.5 2 3.4 2.3-.9a7.6 7.6 0 0 0 1.7 1l.4 2.5h4l.4-2.5a7.6 7.6 0 0 0 1.7-1l2.3.9 2-3.4-2-1.5Z" />
        </svg>
      );
    case "shield":
      return (
        <svg {...common}>
          <path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z" />
        </svg>
      );
    case "document":
      return (
        <svg {...common}>
          <path d="M7 3h7l5 5v13H7z" />
          <path d="M14 3v5h5M9 12h6M9 16h6" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
  }
}

/**
 * Wraps every authenticated page: redirects to /login if there's no
 * valid session, otherwise renders the sidebar nav + top bar + page
 * content.
 *
 * Client-side only guard (no middleware.ts in this app) — matches the
 * rest of the auth flow, which is entirely token-in-localStorage +
 * TanStack Query, not cookie/session based.
 *
 * `sectionColor` (optional) — a --section-* CSS variable name from
 * globals.css (e.g. "--section-analysis"). When passed, it overrides
 * --accent/--accent-hover for everything inside <main>. Because nearly
 * every chart/panel component already reads its accent color via
 * `var(--accent)` instead of a hardcoded hex, this one override cascades
 * through the whole page's component tree via normal CSS custom-property
 * inheritance — no per-component edits needed to recolor a whole section
 * (Charts=blue default, Analysis=orange, Research=purple, AI &
 * Insights=pink, System=neutral, matching the sidebar's section dots).
 */
export function AppShell({
  children,
  sectionColor,
}: {
  children: React.ReactNode;
  sectionColor?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();
  const { theme, toggle } = useTheme();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

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

  const isActive = (href: string) => {
    if (href === "#") return false;
    const [base] = href.split("?");
    return pathname === base || (base !== "/dashboard" && base !== "/charts" && pathname.startsWith(base));
  };

  return (
    <div className="flex min-h-dvh" style={{ backgroundColor: "var(--bg-primary)" }}>
      {/* ── Sidebar (desktop) ── */}
      <aside
        className="sticky top-0 hidden h-dvh w-64 flex-shrink-0 flex-col overflow-y-auto border-r px-3 py-5 lg:flex"
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        aria-label="Main navigation"
      >
        <Link href="/dashboard" className="mb-6 flex items-center gap-2 px-2" aria-label="AstroOS home">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold"
            style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            ॐ
          </span>
          <span className="leading-tight">
            <span className="block text-sm font-bold tracking-wide" style={{ color: "var(--text-primary)" }}>
              ASTRO<span style={{ color: "var(--accent)" }}>OS</span>
            </span>
            <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>
              Vedic Research Platform
            </span>
          </span>
        </Link>

        <nav className="flex flex-1 flex-col gap-5">
          {NAV_SECTIONS.map((section) => {
            const items = section.items.filter((item) => !item.adminOnly || user.role === "admin");
            if (items.length === 0) return null;
            const sectionColor = `var(${section.color})`;
            return (
              <div key={section.title}>
                <p
                  className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest"
                  style={{ color: sectionColor }}
                >
                  {section.title}
                </p>
                <div className="flex flex-col gap-0.5">
                  {items.map((item) =>
                    item.disabled ? (
                      <span
                        key={item.label}
                        className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-xs"
                        style={{ color: "var(--text-muted)", opacity: 0.55, cursor: "default" }}
                        title="Not built yet"
                      >
                        <span className="flex items-center gap-2">
                          <NavIcon name={item.icon} />
                          {item.label}
                        </span>
                        <span
                          className="rounded-full px-1.5 py-0.5 text-[9px] uppercase tracking-wide"
                          style={{ border: "1px solid var(--border-primary)" }}
                        >
                          Soon
                        </span>
                      </span>
                    ) : (
                      <Link
                        key={item.label + item.href}
                        href={item.href}
                        className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium transition"
                        style={{
                          backgroundColor: isActive(item.href) ? "var(--border-primary)" : "transparent",
                          color: isActive(item.href) ? sectionColor : "var(--text-secondary)",
                        }}
                        onMouseEnter={(e) => {
                          if (!isActive(item.href)) e.currentTarget.style.color = sectionColor;
                        }}
                        onMouseLeave={(e) => {
                          if (!isActive(item.href)) e.currentTarget.style.color = "var(--text-secondary)";
                        }}
                        aria-current={isActive(item.href) ? "page" : undefined}
                      >
                        <NavIcon name={item.icon} />
                        {item.label}
                      </Link>
                    ),
                  )}
                </div>
              </div>
            );
          })}
        </nav>

        <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
          <button
            type="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="btn-ghost w-full text-xs"
          >
            {logout.isPending ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </aside>

      {/* ── Main column ── */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b px-4 py-3 backdrop-blur-md"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <div className="flex items-center gap-3 lg:hidden">
            <button
              type="button"
              onClick={() => setMobileNavOpen((v) => !v)}
              className="theme-toggle"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileNavOpen}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <Link href="/dashboard" className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
              Astro<span style={{ color: "var(--accent)" }}>OS</span>
            </Link>
          </div>

          <div className="hidden lg:block" />

          <div className="flex items-center gap-3">
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

            <ResearchModeToggle compact />

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
          </div>
        </header>

        {/* Mobile nav drawer */}
        {mobileNavOpen && (
          <nav
            className="border-b px-4 py-3 lg:hidden"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
            aria-label="Mobile navigation"
          >
            <select
              className="field-input"
              value={pathname}
              onChange={(e) => {
                router.push(e.target.value);
                setMobileNavOpen(false);
              }}
              aria-label="Navigate to page"
            >
              {_FLAT_LINKS.filter((l) => !l.adminOnly || user.role === "admin").map((link) => (
                <option key={link.label + link.href} value={link.href}>
                  {link.label}
                </option>
              ))}
            </select>
          </nav>
        )}

        <main
          className="mx-auto w-full max-w-7xl flex-1 px-4 py-8"
          style={
            sectionColor
              ? ({
                  "--accent": `var(${sectionColor})`,
                  "--accent-hover": `var(${sectionColor}-hover)`,
                } as React.CSSProperties)
              : undefined
          }
        >
          {children}
        </main>
      </div>
    </div>
  );
}
