"use client";

import { AccountMenu } from "@/components/layout/AccountMenu";
import { SearchBar } from "@/components/layout/SearchBar";
import { ResearchModeToggle } from "@/components/research/ResearchModeToggle";
import { tokenStore } from "@/lib/api";
import { useCurrentUser, useLogout } from "@/lib/auth";
import { useWorkflowStore } from "@/lib/store";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useTheme } from "./ThemeProvider";
import { CommandPalette } from "./CommandPalette";
import { ActiveChartSelectorModal } from "./ActiveChartSelectorModal";


import { NAV_SECTIONS, isRouteActive, type NavItem, type NavSection } from "@/config/navConfig";
import { ShareButton } from "@/components/ui";

const _FLAT_LINKS = NAV_SECTIONS.flatMap((s) => s.items).filter((i) => !i.disabled);



export function NavIcon({ name }: { name: string }) {
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
    case "user":
      return (
        <svg {...common}>
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21v-1a6 6 0 0 1 12 0v1" />
        </svg>
      );
    case "star":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4" />
        </svg>
      );
    case "cpu":
      return (
        <svg {...common}>
          <path d="M12 8V4H8" />
          <rect width="16" height="12" x="4" y="8" rx="2" />
          <path d="M2 14h2M20 14h2M15 13v2M9 13v2" />
        </svg>
      );
    case "palette":
      return (
        <svg {...common}>
          <circle cx="13.5" cy="6.5" r="2.5" />
          <circle cx="17.5" cy="10.5" r="2.5" />
          <circle cx="8.5" cy="7.5" r="2.5" />
          <circle cx="6.5" cy="12.5" r="2.5" />
          <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2Z" />
        </svg>
      );
    case "lock":
      return (
        <svg {...common}>
          <path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z" />
        </svg>
      );
    case "database":
      return (
        <svg {...common}>
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v14a9 3 0 0 0 18 0V5" />
          <path d="M3 12a9 3 0 0 0 18 0" />
        </svg>
      );
    case "info":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4M12 8h.01" />
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

function AppShellInner({
  children,
  sectionColor,
}: {
  children: React.ReactNode;
  sectionColor?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();
  const clearWorkflowResult = useWorkflowStore((s) => s.clear);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);
  const request = useWorkflowStore((s) => s.request);
  const result = useWorkflowStore((s) => s.result);
  const { theme, toggle } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [quickActionOpen, setQuickActionOpen] = useState(false);
  const [chartSelectorOpen, setChartSelectorOpen] = useState(false);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      const stored = localStorage.getItem("sidebar:collapsed");
      return stored === "true";
    } catch {
      return false;
    }
  });

  const hasToken = typeof window !== "undefined" && !!tokenStore.getAccess();

  useEffect(() => {
    if (!hasToken || isError) {
      router.replace("/login");
    }
  }, [hasToken, isError, router]);

  const isActive = (href: string) => {
    return isRouteActive(href, pathname, searchParams);
  };

  const toggleSidebar = () => {
    setSidebarCollapsed((v) => {
      const next = !v;
      try {
        localStorage.setItem("sidebar:collapsed", String(next));
      } catch {}
      return next;
    });
  };

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
    return null;
  }

  // Extract any beta / disabled items across sections for feature-flagged Beta Tools accordion
  const betaItems = NAV_SECTIONS.flatMap((s) => s.items).filter((i) => i.disabled || i.beta);

  return (
    <div className="flex min-h-dvh" style={{ backgroundColor: "var(--bg-primary)" }}>
      {/* ── Sidebar (desktop) ── */}
      <aside
        className={`sticky top-0 hidden h-dvh flex-shrink-0 flex-col overflow-y-auto border-r px-3 py-5 lg:flex transition-all duration-200 ${
          sidebarCollapsed ? "w-16" : "w-64"
        }`}
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        aria-label="Main navigation"
        aria-expanded={!sidebarCollapsed}
      >
        <div className={`mb-4 flex items-center gap-2 px-2 ${sidebarCollapsed ? "flex-col" : ""}`}>
          <Link
            href="/dashboard"
            className="flex items-center gap-2"
            aria-label="AstroOS home"
            title={sidebarCollapsed ? "AstroOS" : undefined}
          >
            <span
              className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              ॐ
            </span>
            {!sidebarCollapsed && (
              <span className="leading-tight">
                <span className="block text-sm font-bold tracking-wide" style={{ color: "var(--text-primary)" }}>
                  ASTRO<span className="text-cyan-700 dark:text-cyan-400 font-bold">OS</span>
                </span>
                <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>
                  Vedic Research Platform
                </span>
              </span>
            )}
          </Link>

          <button
            type="button"
            onClick={toggleSidebar}
            className="theme-toggle ml-auto hidden h-8 w-8 flex-shrink-0 items-center justify-center rounded transition-colors lg:flex"
            style={{ color: "var(--text-secondary)" }}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {sidebarCollapsed ? <path d="M15 18l-6-6 6-6" /> : <path d="M9 18l6-6-6-6" />}
            </svg>
          </button>
        </div>

        {/* ── Quick Action CTA Dropdown (Sidebar) ── */}
        <div className="relative mb-5 px-1">
          <button
            type="button"
            onClick={() => setQuickActionOpen((v) => !v)}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-700 hover:bg-cyan-800 py-2.5 text-xs font-bold text-white shadow-md transition"
            title="Quick Action"
          >
            <NavIcon name="plus" />
            {!sidebarCollapsed && <span>Quick Action</span>}
          </button>

          {quickActionOpen && (
            <div
              className="absolute left-1 right-1 top-full z-50 mt-1.5 flex flex-col rounded-lg border p-1 shadow-xl"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-card)",
              }}
            >
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  clearWorkflowResult();
                  openCreateModal("natal");
                }}
              >
                <NavIcon name="plus" />
                <span>New Natal Chart</span>
              </button>
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  router.push("/charts/compare");
                }}
              >
                <NavIcon name="layers" />
                <span>Compare Charts</span>
              </button>
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  openCreateModal("compatibility");
                }}
              >
                <NavIcon name="target" />
                <span>New Compatibility Match</span>
              </button>
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  openCreateModal("transit");
                }}
              >
                <NavIcon name="orbit" />
                <span>Transit Analysis</span>
              </button>
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  router.push("/charts?view=dasha");
                }}
              >
                <NavIcon name="clock" />
                <span>Dasha Explorer</span>
              </button>
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  router.push("/charts/import");
                }}
              >
                <NavIcon name="upload" />
                <span>Import Chart</span>
              </button>
              <button
                type="button"
                className="flex items-center gap-2 rounded px-2.5 py-1.5 text-left text-xs transition hover:bg-[var(--border-primary)]"
                style={{ color: "var(--text-primary)" }}
                onClick={(e) => {
                  e.preventDefault();
                  setQuickActionOpen(false);
                  router.push("/research/projects");
                }}
              >
                <NavIcon name="search" />
                <span>New Research Project</span>
              </button>
            </div>
          )}
        </div>

        <nav className="flex flex-1 flex-col gap-5">
          {NAV_SECTIONS.map((section) => {
            // In primary navigation flow, show active, non-disabled items
            const items = section.items.filter(
              (item) => (!item.adminOnly || user.role === "admin") && !item.disabled && !item.beta
            );
            if (items.length === 0) return null;
            return (
              <div key={section.title}>
                <p
                  className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-widest text-slate-700 dark:text-slate-300"
                >
                  {section.title}
                </p>
                <div className="flex flex-col gap-0.5">
                  {items.map((item) => {
                    const active = isActive(item.href);
                    return (
                      <Link
                        key={item.label + item.href}
                        href={item.href}
                        className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium transition ${
                          active
                            ? "bg-slate-200 dark:bg-slate-800 text-cyan-900 dark:text-cyan-300 font-bold"
                            : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-850"
                        }`}
                        onClick={
                          item.href === "/dashboard" && item.label === "New Chart"
                            ? () => {
                                clearWorkflowResult();
                                openCreateModal();
                              }
                            : undefined
                        }
                        aria-current={active ? "page" : undefined}
                        title={sidebarCollapsed ? item.label : undefined}
                      >
                        <NavIcon name={item.icon} />
                        {!sidebarCollapsed && item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* ── Beta Tools / Pending Routes Accordion (Feature Flagged) ── */}
          {betaItems.length > 0 && (
            <details className="mt-2 border-t pt-2 group" style={{ borderColor: "var(--border-primary)" }}>
              <summary className="flex cursor-pointer items-center justify-between px-2 py-1.5 text-[10px] font-semibold uppercase tracking-widest transition" style={{ color: "var(--text-muted)" }}>
                <span>Beta Tools</span>
                <span className="text-[9px] rounded px-1 border" style={{ borderColor: "var(--border-primary)" }}>
                  {betaItems.length}
                </span>
              </summary>
              <div className="mt-1 flex flex-col gap-0.5">
                {betaItems.map((item) => (
                  <span
                    key={item.label}
                    className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-xs"
                    style={{ color: "var(--text-muted)", opacity: 0.55, cursor: "default" }}
                    title={sidebarCollapsed ? item.label : "Pending route / In development"}
                  >
                    <span className="flex items-center gap-2">
                      <NavIcon name={item.icon} />
                      {!sidebarCollapsed && item.label}
                    </span>
                    {!sidebarCollapsed && (
                      <span
                        className="rounded-full px-1.5 py-0.5 text-[9px] uppercase tracking-wide"
                        style={{ border: "1px solid var(--border-primary)" }}
                      >
                        Soon
                      </span>
                    )}
                  </span>
                ))}
              </div>
            </details>
          )}
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
      <div className="flex min-w-0 flex-1 flex-col overflow-x-hidden">
        <header
          className="sticky top-0 z-10 flex w-full max-w-full flex-wrap items-center justify-between gap-3 border-b px-4 py-3 backdrop-blur-md"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <div className="flex items-center gap-3 lg:hidden">
            <button
              type="button"
              onClick={() => setMobileNavOpen(true)}
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

          <SearchBar />

          {/* ── Active Chart Context Pill (Header) ── */}
          <div className="hidden md:flex items-center">
            {request ? (
              <div
                className="flex items-center gap-2 rounded-lg border px-2.5 py-1 text-xs transition"
                style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
              >
                <button
                  type="button"
                  onClick={() => setChartSelectorOpen(true)}
                  className="flex items-center gap-1.5 hover:opacity-80 transition cursor-pointer text-left"
                  title="Click to switch active chart"
                >
                  <span className="h-2 w-2 rounded-full animate-pulse" style={{ backgroundColor: "var(--accent)" }} />
                  <span className="font-semibold max-w-[140px] truncate" style={{ color: "var(--text-primary)" }}>
                    {request.subject_name || "Active Chart"}
                  </span>
                  {request.place_name && (
                    <span className="text-[10px] hidden lg:inline max-w-[100px] truncate" style={{ color: "var(--text-muted)" }}>
                      · {request.place_name}
                    </span>
                  )}
                  <span className="text-[10px] text-muted-foreground ml-0.5">▾</span>
                </button>
                <button
                  type="button"
                  onClick={() => router.push("/charts/birth")}
                  className="ml-1 text-[11px] font-bold text-sky-700 dark:text-sky-400 hover:underline cursor-pointer"
                  title="View active birth chart"
                >
                  View
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setChartSelectorOpen(true)}
                className="flex items-center gap-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2.5 py-1 text-xs text-slate-700 dark:text-slate-200 hover:border-cyan-500 hover:text-cyan-600 dark:hover:text-cyan-400 transition shadow-sm cursor-pointer"
              >
                <NavIcon name="plus" />
                <span>Select Chart</span>
              </button>
            )}
          </div>


          <div className="flex items-center gap-3">
            {sidebarCollapsed && (
              <button
                type="button"
                onClick={toggleSidebar}
                className="theme-toggle hidden h-8 w-8 items-center justify-center rounded transition-colors lg:flex"
                style={{ color: "var(--text-secondary)" }}
                aria-label="Expand sidebar"
                title="Expand sidebar"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
            )}

            <ResearchModeToggle compact />

            <ShareButton />

            <button
              type="button"
              onClick={toggle}
              className="theme-toggle"
              aria-label={mounted ? `Switch to ${theme === "dark" ? "light" : "dark"} mode` : "Toggle theme"}
              title={mounted ? `Switch to ${theme === "dark" ? "light" : "dark"} mode` : "Toggle theme"}
            >
              {mounted && theme === "light" ? (
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
              )}
            </button>

            <AccountMenu user={user} />
          </div>
        </header>

        {/* ── Mobile Slide-Over Navigation Drawer ── */}
        {mobileNavOpen && (
          <div className="fixed inset-0 z-50 flex lg:hidden" role="dialog" aria-modal="true">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
              onClick={() => setMobileNavOpen(false)}
              aria-hidden="true"
            />

            {/* Slide-over panel */}
            <div
              className="relative flex w-full max-w-xs flex-1 flex-col overflow-y-auto border-r p-4 shadow-2xl"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
            >
              <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
                <Link
                  href="/dashboard"
                  onClick={() => setMobileNavOpen(false)}
                  className="flex items-center gap-2"
                >
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold"
                    style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
                  >
                    ॐ
                  </span>
                  <span className="text-sm font-bold tracking-wide" style={{ color: "var(--text-primary)" }}>
                    ASTRO<span style={{ color: "var(--accent)" }}>OS</span>
                  </span>
                </Link>
                <button
                  type="button"
                  onClick={() => setMobileNavOpen(false)}
                  className="theme-toggle h-8 w-8"
                  aria-label="Close navigation menu"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Quick Action Button in Mobile Drawer */}
              <div className="my-3">
                <button
                  type="button"
                  onClick={() => {
                    setMobileNavOpen(false);
                    clearWorkflowResult();
                    openCreateModal("natal");
                  }}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 py-2.5 text-xs font-bold text-slate-950 shadow-md shadow-cyan-500/20"
                >
                  <NavIcon name="plus" />
                  <span>+ New Natal Chart</span>
                </button>

              </div>

              {/* Navigation Sections */}
              <nav className="flex-1 space-y-4">
                {NAV_SECTIONS.map((section) => {
                  const items = section.items.filter((item) => (!item.adminOnly || user.role === "admin") && !item.disabled && !item.beta);
                  if (items.length === 0) return null;
                  const sectionColor = `var(${section.color})`;
                  return (
                    <div key={section.title}>
                      <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest" style={{ color: sectionColor }}>
                        {section.title}
                      </p>
                      <div className="flex flex-col gap-0.5">
                        {items.map((item) => (
                          <Link
                            key={item.label + item.href}
                            href={item.href}
                            onClick={() => setMobileNavOpen(false)}
                            className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium transition"
                            style={{
                              backgroundColor: isActive(item.href) ? "var(--border-primary)" : "transparent",
                              color: isActive(item.href) ? sectionColor : "var(--text-secondary)",
                            }}
                          >
                            <NavIcon name={item.icon} />
                            <span>{item.label}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </nav>

              {/* Mobile Drawer Footer */}
              <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
                <button
                  type="button"
                  onClick={() => logout.mutate()}
                  className="btn-ghost w-full text-xs"
                >
                  Sign out
                </button>
              </div>
            </div>
          </div>
        )}


        <main
          className="mx-auto w-full max-w-[1800px] flex-1 min-w-0 overflow-x-hidden px-3 sm:px-4 lg:px-6 xl:px-8 py-3 md:py-4"
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
        
        <CommandPalette />
        <ActiveChartSelectorModal isOpen={chartSelectorOpen} onClose={() => setChartSelectorOpen(false)} />
      </div>
    </div>
  );
}


export function AppShell(props: {
  children: React.ReactNode;
  sectionColor?: string;
}) {
  return (
    <Suspense fallback={null}>
      <AppShellInner {...props} />
    </Suspense>
  );
}