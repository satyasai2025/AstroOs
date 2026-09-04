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
          className="absolute right-0 top-full z-[100] mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0c1527] shadow-2xl"
          role="menu"
        >
          <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 px-4 py-3 bg-slate-50/50 dark:bg-slate-900/50">
            <span
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold text-white bg-cyan-600 shadow-sm"
            >
              {initial}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                {user.display_name}
              </p>
              <p className="truncate text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
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
                className="flex items-center gap-2.5 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/70 hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors"
              >
                <NavIcon name={item.icon} />
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          <div className="border-t border-slate-200 dark:border-slate-800 p-2 bg-slate-50/30 dark:bg-slate-900/30">
            <button
              type="button"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-600 dark:hover:text-rose-400 hover:border-rose-300 dark:hover:border-rose-800 transition-all cursor-pointer"
            >
              {logout.isPending ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
