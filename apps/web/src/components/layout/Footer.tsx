"use client";

import Link from "next/link";
import { useState, memo } from "react";
import { useTheme } from "./ThemeProvider";

export const Footer = memo(function Footer() {
  const currentYear = new Date().getFullYear();
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);
  const { theme, toggle: toggleTheme } = useTheme();

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail("");
    }
  };

  const scrollToTop = () => {
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <footer
      role="contentinfo"
      aria-label="Site Footer"
      className="mt-auto w-full border-t transition-colors relative overflow-hidden"
      style={{
        backgroundColor: "var(--bg-secondary)",
        borderColor: "var(--border-primary)",
        color: "var(--text-secondary)",
      }}
    >
      {/* ── Top Ambient Light ── */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-24 blur-2xl pointer-events-none opacity-40 dark:opacity-70"
        style={{
          background: "radial-gradient(ellipse at top, var(--cyan-glow-soft, rgba(41,184,212,0.15)), transparent 70%)",
        }}
      />

      <div className="mx-auto max-w-[1800px] px-4 sm:px-6 lg:px-8 pt-12 pb-8 relative z-10">
        {/* ── Main 5-Column Grid ── */}
        <div
          className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-8 pb-12 border-b"
          style={{ borderColor: "var(--border-primary)" }}
        >
          {/* Column 1: Brand, About & Socials (4 cols on lg) */}
          <div className="space-y-5 lg:col-span-4">
            <Link
              href="/"
              className="inline-flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-cyan-400 rounded-lg p-0.5"
              aria-label="AstroOS Home"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-xl text-base font-bold shadow-md bg-gradient-to-br from-cyan-500 to-indigo-600 text-white border border-cyan-400/40 group-hover:scale-105 transition-transform">
                ॐ
              </span>
              <span className="text-xl font-extrabold tracking-wide" style={{ color: "var(--text-primary)" }}>
                ASTRO<span style={{ color: "var(--cyan-400)" }}>OS</span>
              </span>
            </Link>

            <p className="text-xs leading-relaxed max-w-sm" style={{ color: "var(--text-muted)" }}>
              Next-generation Vedic Astrology computational platform providing precision birth charts, 
              predictive dasha timelines, classical Shastra intelligence, and empirical research tools worldwide.
            </p>

            {/* Social Icons */}
            <div className="space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                Follow & Connect
              </p>
              <div className="flex items-center gap-2">
                <a
                  href="https://twitter.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Twitter / X"
                  className="flex h-8 w-8 items-center justify-center rounded-full border transition-colors"
                  style={{
                    backgroundColor: "var(--bg-card)",
                    borderColor: "var(--border-primary)",
                    color: "var(--text-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = "var(--cyan-400)";
                    e.currentTarget.style.borderColor = "var(--cyan-400)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = "var(--text-secondary)";
                    e.currentTarget.style.borderColor = "var(--border-primary)";
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </a>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="GitHub"
                  className="flex h-8 w-8 items-center justify-center rounded-full border transition-colors"
                  style={{
                    backgroundColor: "var(--bg-card)",
                    borderColor: "var(--border-primary)",
                    color: "var(--text-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = "var(--cyan-400)";
                    e.currentTarget.style.borderColor = "var(--cyan-400)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = "var(--text-secondary)";
                    e.currentTarget.style.borderColor = "var(--border-primary)";
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                </a>
                <a
                  href="https://youtube.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="YouTube"
                  className="flex h-8 w-8 items-center justify-center rounded-full border transition-colors"
                  style={{
                    backgroundColor: "var(--bg-card)",
                    borderColor: "var(--border-primary)",
                    color: "var(--text-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = "var(--cyan-400)";
                    e.currentTarget.style.borderColor = "var(--cyan-400)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = "var(--text-secondary)";
                    e.currentTarget.style.borderColor = "var(--border-primary)";
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                  </svg>
                </a>
                <a
                  href="https://linkedin.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="LinkedIn"
                  className="flex h-8 w-8 items-center justify-center rounded-full border transition-colors"
                  style={{
                    backgroundColor: "var(--bg-card)",
                    borderColor: "var(--border-primary)",
                    color: "var(--text-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = "var(--cyan-400)";
                    e.currentTarget.style.borderColor = "var(--cyan-400)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = "var(--text-secondary)";
                    e.currentTarget.style.borderColor = "var(--border-primary)";
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Platform Availability Badge */}
            <div
              className="inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-muted)",
              }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Web Workstation v2.4</span>
              <span>·</span>
              <span>API Active</span>
            </div>
          </div>

          {/* Column 2: Core Workstation (2 cols) */}
          <div className="space-y-3.5 lg:col-span-2">
            <p className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
              Workstation
            </p>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/charts/birth" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Birth Chart Workspace</span>
                </Link>
              </li>
              <li>
                <Link href="/charts?view=kundli" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Interactive Kundli</span>
                </Link>
              </li>
              <li>
                <Link href="/charts?view=divisional" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Divisional Matrices</span>
                </Link>
              </li>
              <li>
                <Link href="/charts/planets" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Planet & House Explorer</span>
                </Link>
              </li>
              <li>
                <Link href="/compatibility/report" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Chart Compatibility</span>
                </Link>
              </li>
              <li>
                <Link href="/charts/history" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Chart Library</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Predictive & Tools (2 cols) */}
          <div className="space-y-3.5 lg:col-span-2">
            <p className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
              Predictive Tools
            </p>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/phalita" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Phalita MoE Engine</span>
                </Link>
              </li>
              <li>
                <Link href="/charts/dasha" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Vimshottari Dasha</span>
                </Link>
              </li>
              <li>
                <Link href="/charts/transit" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Transit (Gochara)</span>
                </Link>
              </li>
              <li>
                <Link href="/muhurta" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Muhurta & Panchanga</span>
                </Link>
              </li>
              <li>
                <Link href="/medini" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Medini Mundane Ingress</span>
                </Link>
              </li>
              <li>
                <Link href="/numerology" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Meena Numerology</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Research & Learn (2 cols) */}
          <div className="space-y-3.5 lg:col-span-2">
            <p className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
              Research & Learn
            </p>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/research/projects" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Research Suite</span>
                </Link>
              </li>
              <li>
                <Link href="/research/reverse-search" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Reverse Chart Search</span>
                </Link>
              </li>
              <li>
                <Link href="/research/patterns" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Pattern Discovery</span>
                </Link>
              </li>
              <li>
                <Link href="/knowledge" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Classical Treatises</span>
                </Link>
              </li>
              <li>
                <Link href="/knowledge/bphs" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>BPHS Sloka Database</span>
                </Link>
              </li>
              <li>
                <Link href="/help" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Methodology & Docs</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 5: Platform & Contact (2 cols) */}
          <div className="space-y-3.5 lg:col-span-2">
            <p className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
              Platform
            </p>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/dashboard" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Dashboard</span>
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Plans & Pricing</span>
                </Link>
              </li>
              <li>
                <Link href="/settings" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Settings & BYOK</span>
                </Link>
              </li>
              <li>
                <Link href="/sitemap" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5 font-semibold text-cyan-400">
                  <span style={{ color: "var(--cyan-400)" }}>·</span>
                  <span>Sitemap Directory →</span>
                </Link>
              </li>
              <li>
                <Link href="/admin" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  <span style={{ color: "var(--text-muted)" }}>·</span>
                  <span>Admin Portal</span>
                </Link>
              </li>
            </ul>

            {/* Quick Contact Info */}
            <div className="pt-2 space-y-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
              <p className="font-medium" style={{ color: "var(--text-primary)" }}>Support & Inquiry</p>
              <p className="font-mono text-[10px]">support@astroos.internal</p>
              <p className="text-[10px]">Mon–Sat: 9 AM – 7 PM IST</p>
            </div>
          </div>
        </div>

        {/* ── Newsletter / Updates Strip ── */}
        <div
          className="py-8 border-b flex flex-col md:flex-row items-center justify-between gap-6"
          style={{ borderColor: "var(--border-primary)" }}
        >
          <div className="flex items-center gap-3.5">
            <div
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border"
              style={{
                backgroundColor: "var(--amber-glow-soft, rgba(251,191,36,0.1))",
                borderColor: "rgba(251,191,36,0.3)",
                color: "var(--amber-400)",
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                Vedic Research & Ephemeris Dispatch
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Subscribe for monthly astronomical ingress briefs, classical research notes, and platform release updates.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubscribe} className="w-full md:w-auto flex flex-col sm:flex-row items-center gap-2">
            <div className="relative w-full sm:w-72">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                className="w-full rounded-xl border px-3.5 py-2.5 text-xs transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
                style={{
                  backgroundColor: "var(--bg-input, var(--bg-card))",
                  borderColor: "var(--border-primary)",
                  color: "var(--text-primary)",
                }}
              />
            </div>
            <button
              type="submit"
              className="w-full sm:w-auto rounded-xl px-5 py-2.5 text-xs font-bold transition shadow-md whitespace-nowrap hover:opacity-90"
              style={{
                backgroundColor: "var(--amber-500, #f59e0b)",
                color: "#0f172a",
              }}
            >
              {subscribed ? "Subscribed ✓" : "Subscribe"}
            </button>
          </form>
        </div>

        {/* ── Trust & Quality Assurance Pills Strip ── */}
        <div
          className="py-6 border-b flex flex-wrap items-center justify-center sm:justify-between gap-3 text-xs"
          style={{ borderColor: "var(--border-primary)" }}
        >
          <div className="flex flex-wrap items-center justify-center gap-2.5">
            <span
              className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px]"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <span>🔒</span>
              <span>Encrypted Storage</span>
            </span>
            <span
              className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px]"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <span>⚡</span>
              <span>Sub-arcsecond Calculations</span>
            </span>
            <span
              className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px]"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <span>📚</span>
              <span>Classical BPHS Grounded</span>
            </span>
            <span
              className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px]"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <span>🛡️</span>
              <span>Zero Hallucination AI</span>
            </span>
            <span
              className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px]"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <span className="text-amber-400">★</span>
              <span>Scholar Verified</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
                    <circle cx="12" cy="12" r="5" /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                  </svg>
                  <span>Light</span>
                </>
              ) : (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                  </svg>
                  <span>Dark</span>
                </>
              )}
            </button>

            {/* Scroll-To-Top Button */}
            <button
              onClick={scrollToTop}
              aria-label="Scroll to top"
              className="flex h-8 w-8 items-center justify-center rounded-lg border transition-colors hover:scale-105"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="m18 15-6-6-6 6" />
              </svg>
            </button>
          </div>
        </div>

        {/* ── Sub-Footer Bottom Bar ── */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
          <div className="flex flex-wrap items-center gap-4">
            <Link href="/help" className="hover:underline transition-colors" style={{ color: "var(--text-secondary)" }}>
              Privacy Policy
            </Link>
            <span>·</span>
            <Link href="/help" className="hover:underline transition-colors" style={{ color: "var(--text-secondary)" }}>
              Terms of Service
            </Link>
            <span>·</span>
            <Link href="/settings/security" className="hover:underline transition-colors" style={{ color: "var(--text-secondary)" }}>
              Security & BYOK
            </Link>
            <span>·</span>
            <Link href="/sitemap" className="hover:underline font-medium" style={{ color: "var(--cyan-400)" }}>
              Sitemap (HTML & XML)
            </Link>
          </div>

          <p className="text-center sm:text-right">
            © {currentYear} <span className="font-semibold" style={{ color: "var(--text-primary)" }}>AstroOS</span>. Built with precision for Vedic astrology scholars & practitioners.
          </p>
        </div>
      </div>
    </footer>
  );
});
