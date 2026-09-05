"use client";

import Link from "next/link";
import { useTheme } from "@/components/layout/ThemeProvider";

export function LandingHeader() {
  const { theme, toggle: toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-[#060814]/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link href="/" aria-label="AstroOS Home" className="flex items-center gap-2.5 group">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-sky-700 text-white font-bold text-base shadow-md shadow-cyan-500/25 border border-cyan-400/40 group-hover:scale-105 transition-transform">
            ॐ
          </span>
          <div className="flex flex-col leading-none">
            <span className="text-lg font-extrabold tracking-wider text-white">
              ASTRO<span className="text-cyan-400">OS</span>
            </span>
            <span className="text-[9px] font-semibold tracking-widest text-slate-400 uppercase">
              Ancient Wisdom · Modern Insights
            </span>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link
            href="/"
            className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            Home
          </Link>
          <Link
            href="/muhurta"
            className="text-xs font-medium text-slate-300 hover:text-cyan-300 transition-colors"
          >
            Panchang
          </Link>
          <Link
            href="/charts"
            className="text-xs font-medium text-slate-300 hover:text-cyan-300 transition-colors"
          >
            Kundli
          </Link>
          <Link
            href="/predictions"
            className="text-xs font-medium text-slate-300 hover:text-cyan-300 transition-colors"
          >
            Predictions
          </Link>
          <Link
            href="/research"
            className="text-xs font-medium text-slate-300 hover:text-cyan-300 transition-colors"
          >
            Research
          </Link>
          <Link
            href="/pricing"
            className="text-xs font-medium text-slate-300 hover:text-cyan-300 transition-colors"
          >
            Pricing
          </Link>
        </nav>

        {/* Right Controls */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 hover:text-cyan-300 hover:border-slate-700 transition"
            aria-label="Toggle Theme"
          >
            {theme === "dark" ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          <Link
            href="/login"
            className="hidden sm:inline-flex rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 hover:text-white transition"
          >
            Sign In
          </Link>

          <Link
            href="/charts"
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 px-3.5 py-2 text-xs font-bold text-white shadow-md shadow-cyan-500/20 transition hover:brightness-105"
          >
            <span>Launch Workstation</span>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>
        </div>
      </div>
    </header>
  );
}
