"use client";

import React, { useEffect } from "react";
import Link from "next/link";

export function LandingHeader() {
  // Landing and Panchang are strictly dark mode only — no light, no system theme
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    }
  }, []);

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
            href="/panchang#kundli"
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
