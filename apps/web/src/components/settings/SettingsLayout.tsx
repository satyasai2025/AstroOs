"use client";

import { AppShell } from "@/components/layout/AppShell";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

interface SettingsNavItem {
  href: string;
  label: string;
  icon: ReactNode;
}

const SETTINGS_NAV: SettingsNavItem[] = [
  {
    href: "/settings/profile",
    label: "Profile",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21v-1a6 6 0 0 1 12 0v1" />
      </svg>
    ),
  },
  {
    href: "/settings/astrology",
    label: "Astrology",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4" />
      </svg>
    ),
  },
  {
    href: "/settings/ai",
    label: "AI",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2M20 14h2M15 13v2M9 13v2" />
      </svg>
    ),
  },
  {
    href: "/settings/appearance",
    label: "Appearance",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="13.5" cy="6.5" r="2.5" />
        <circle cx="17.5" cy="10.5" r="2.5" />
        <circle cx="8.5" cy="7.5" r="2.5" />
        <circle cx="6.5" cy="12.5" r="2.5" />
        <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2Z" />
      </svg>
    ),
  },
  {
    href: "/settings/security",
    label: "Security",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z" />
      </svg>
    ),
  },
  {
    href: "/settings/billing",
    label: "Billing & Plans",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect width="20" height="14" x="2" y="5" rx="2" />
        <line x1="2" x2="22" y1="10" y2="10" />
      </svg>
    ),
  },
  {
    href: "/settings/notifications",
    label: "Notifications",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
    ),
  },
  {
    href: "/settings/data",
    label: "Data",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M3 5v14a9 3 0 0 0 18 0V5" />
        <path d="M3 12a9 3 0 0 0 18 0" />
      </svg>
    ),
  },
];

interface SettingsLayoutProps {
  children: ReactNode;
  title: string;
  description?: string;
}

export function SettingsLayout({ children, title, description }: SettingsLayoutProps) {
  const pathname = usePathname();

  return (
    <AppShell>
      <div className="flex flex-col md:flex-row min-h-[calc(100vh-73px)]">
        {/* Mobile Settings Tab Bar */}
        <div
          className="flex md:hidden overflow-x-auto border-b p-2 gap-1.5 scrollbar-none"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          {SETTINGS_NAV.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium whitespace-nowrap transition-all"
                style={{
                  backgroundColor: isActive ? "var(--obsidian-accent-primary-soft)" : "transparent",
                  color: isActive ? "var(--accent)" : "var(--text-secondary)",
                  border: isActive ? "1px solid var(--accent)" : "1px solid transparent",
                }}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Desktop Settings Sidebar */}
        <aside
          className="hidden md:block w-64 flex-shrink-0 border-r"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <nav className="sticky top-0 p-4">
            <h2 className="mb-4 px-2 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Settings
            </h2>
            <div className="flex flex-col gap-1">
              {SETTINGS_NAV.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all"
                    style={{
                      backgroundColor: isActive ? "var(--obsidian-accent-primary-soft)" : "transparent",
                      color: isActive ? "var(--accent)" : "var(--text-secondary)",
                      border: isActive ? "1px solid var(--border-primary)" : "1px solid transparent",
                    }}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 overflow-auto">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 py-6 sm:py-8">
            {/* Header */}
            <div className="mb-8">
              <h1
                className="text-2xl sm:text-3xl font-bold"
                style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}
              >
                {title}
              </h1>
              {description && (
                <p className="mt-1 text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
                  {description}
                </p>
              )}
            </div>

            {/* Content */}
            {children}
          </div>
        </div>
      </div>
    </AppShell>
  );
}