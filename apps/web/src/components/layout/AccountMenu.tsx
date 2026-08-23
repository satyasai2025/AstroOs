"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useLogout } from "@/lib/auth";
import type { User } from "@/lib/types";
import { NavIcon } from "./AppShell";

const ACCOUNT_MENU_ITEMS = [
  { href: "/settings/profile", label: "Profile", icon: "user" },
  { href: "/settings/astrology", label: "Astrology", icon: "star" },
  { href: "/settings/ai", label: "AI", icon: "cpu" },
  { href: "/settings/appearance", label: "Appearance", icon: "palette" },
  { href: "/settings/security", label: "Security", icon: "lock" },
  { href: "/settings/data", label: "Data", icon: "database" },
  { href: "/help", label: "Help & Guide", icon: "book" },
];

export function AccountMenu({ user }: { user: User }) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const logout = useLogout();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  const initial = user.display_name?.trim()?.[0]?.toUpperCase() || "?";

  return (
    <div ref={wrapperRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-transform hover:scale-105"
        style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        aria-label="Account menu"
        aria-haspopup="menu"
        aria-expanded={isOpen}
      >
        {initial}
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-lg border shadow-lg"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
          role="menu"
        >
          <div
            className="flex items-center gap-3 border-b px-4 py-3"
            style={{ borderColor: "var(--border-primary)" }}
          >
            <span
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              {initial}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {user.display_name}
              </p>
              <p className="truncate text-[11px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                {user.role}
              </p>
            </div>
          </div>

          <div className="flex flex-col py-1.5">
            {ACCOUNT_MENU_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                role="menuitem"
                className="flex items-center gap-2.5 px-4 py-2 text-sm transition"
                style={{ color: "var(--text-secondary)" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = "var(--accent)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = "var(--text-secondary)";
                }}
              >
                <NavIcon name={item.icon} />
                {item.label}
              </Link>
            ))}
          </div>

          <div className="border-t px-2 py-1.5" style={{ borderColor: "var(--border-primary)" }}>
            <button
              type="button"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="btn-ghost w-full text-xs"
            >
              {logout.isPending ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
