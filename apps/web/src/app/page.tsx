import Link from "next/link";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { TodayPanchangCard } from "@/components/landing/TodayPanchangCard";
import { Footer } from "@/components/layout/Footer";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col justify-between bg-[#060814] text-slate-100 relative overflow-hidden">
      {/* ── Ambient Soft Background (No harsh toy neon) ── */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[400px] bg-gradient-to-b from-cyan-950/20 via-sky-950/10 to-transparent blur-3xl pointer-events-none" />
      <div className="absolute top-[40%] right-0 w-[500px] h-[350px] bg-cyan-900/10 blur-3xl pointer-events-none" />

      {/* ── Top Header Bar ── */}
      <LandingHeader />

      <main className="relative z-10 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-20">
        {/* ── Hero Section (2-Column: Left Copy is Compact & Light, Right Panchang is the Centerpiece) ── */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column (Light, concise, clutter-free) */}
          <div className="lg:col-span-6 space-y-5 text-left">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-950/30 px-3.5 py-1 text-[11px] font-semibold text-cyan-300 tracking-wide uppercase">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span>Tradition × Technology × Clarity</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-[1.15]">
              Vedic Astrology, Panchang &amp;<br />
              <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-teal-400 bg-clip-text text-transparent">
                Computational Research
              </span>
            </h1>

            <p className="text-sm sm:text-base leading-relaxed text-slate-300 max-w-lg font-normal">
              Explore timeless wisdom with modern technology. Calculate high-precision charts, find muhurats, analyze predictive dasha timelines, and conduct empirical research — all in one powerful workstation.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Link
                href="/charts"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 text-xs sm:text-sm shadow-lg shadow-cyan-500/20 transition-all transform hover:-translate-y-0.5"
              >
                <span>Get Started Free</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>

              <a
                href="#features"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-700 hover:border-cyan-500/40 bg-slate-900/40 hover:bg-slate-800 text-slate-300 font-semibold px-5 py-2.5 sm:py-3 text-xs sm:text-sm transition"
              >
                <span>Explore Features</span>
              </a>
            </div>

            {/* Micro-Trust Strip under Hero Text */}
            <div className="pt-2 flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 border border-slate-800 text-cyan-400">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                </span>
                <span>Authentic Vedic Methods</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 border border-slate-800 text-cyan-400">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                </span>
                <span>Swiss Ephemeris Precision</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 border border-slate-800 text-cyan-400">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                </span>
                <span>Learners &amp; Researchers</span>
              </div>
            </div>
          </div>

          {/* Right Column: Hero Focus Centerpiece (Today's Panchang Widget) */}
          <div className="lg:col-span-6 flex justify-center lg:justify-end">
            <TodayPanchangCard />
          </div>
        </section>

        {/* ── Feature Grid ("Everything You Need in One Place") ── */}
        <section id="features" className="space-y-8 pt-4">
          <div className="text-center space-y-2">
            <span className="text-[10px] font-bold tracking-widest text-cyan-400 uppercase">
              Explore AstroOS Platform
            </span>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
              Everything You Need in One Place
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
              From daily Panchang to advanced research tools, AstroOS gives you a complete computational ecosystem for learning, analysis, and real-world application.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
            {/* Card 1: Panchang */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Panchang
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Daily Panchang, Shubha Muhurta, Hora, Rahu Kaal, and Choghadiya calculations for any date and city.
                </p>
              </div>
              <Link
                href="/muhurta"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 2: Kundli & Charts */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 2 12 12 22 22 12 12 2" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <line x1="12" y1="2" x2="12" y2="22" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Kundli &amp; Charts
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Create and analyze birth charts with Bhavachalita, Shadbala, and simultaneous D1–D60 divisional overlays.
                </p>
              </div>
              <Link
                href="/charts"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 3: Predictions */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Predictions
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Multi-tier Vimshottari and Chara dasha timelines integrated with Gochara transit heatmaps and Ashtakavarga.
                </p>
              </div>
              <Link
                href="/predictions"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 4: Research */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Research Suite
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Query chart databases by planetary yogas, execute reverse searches, and conduct empirical statistical analysis.
                </p>
              </div>
              <Link
                href="/research"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 5: Planets Explorer */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="6" />
                    <path d="M2.05 12a10 10 0 0 1 19.9 0" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Planets Explorer
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  In-depth planetary analysis, combustion, retrogression, avasthas, Shadbala components, and Karakatva.
                </p>
              </div>
              <Link
                href="/charts/planets"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 6: Muhurat Studio */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Muhurat Studio
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Find auspicious timings for life&apos;s events: marriage, business launch, travel, and Griha Pravesha with dosha filtering.
                </p>
              </div>
              <Link
                href="/muhurta"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 7: AI Jyotish Studio */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
                    <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  AI Jyotish Studio
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Zero-hallucination astrological queries grounded strictly in classical Parashari principles and source texts.
                </p>
              </div>
              <Link
                href="/ai"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 8: Knowledge Graph */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="18" r="3" />
                    <circle cx="6" cy="6" r="3" />
                    <circle cx="18" cy="6" r="3" />
                    <path d="M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9" />
                    <path d="M12 12v3" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Knowledge Graph
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Search classical yogas, planetary combinations, and BPHS Sanskrit slokas with structured references.
                </p>
              </div>
              <Link
                href="/knowledge-graph"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Card 9: Medini & Mundane */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group hover:bg-slate-900/80">
              <div>
                <div className="mb-3.5 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-inner">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="m4.93 4.93 4.24 4.24" />
                    <path d="m14.83 9.17 4.24-4.24" />
                    <path d="m14.83 14.83 4.24 4.24" />
                    <path d="m9.17 14.83-4.24 4.24" />
                    <circle cx="12" cy="12" r="4" />
                  </svg>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  Medini &amp; Mundane
                </h3>
                <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                  Astronomical Planetary Cabinet (Nava Nayakas), solar ingresses, and mundane cycle tracking.
                </p>
              </div>
              <Link
                href="/medini"
                className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:gap-1.5 transition-all"
              >
                <span>Open Workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </section>

        {/* ── Precision Metrics & Trust Badges Strip ── */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-center">
            <div className="space-y-1">
              <span className="text-xs font-mono text-cyan-400 font-bold block">Sub-Arcsecond</span>
              <span className="text-[11px] text-slate-400 block">Swiss Ephemeris Core</span>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-mono text-cyan-400 font-bold block">100% Classical</span>
              <span className="text-[11px] text-slate-400 block">BPHS Shastric Fidelity</span>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-mono text-cyan-400 font-bold block">7 Chara Karakas</span>
              <span className="text-[11px] text-slate-400 block">Siddhantic Invariant</span>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-mono text-cyan-400 font-bold block">Zero Mock AI</span>
              <span className="text-[11px] text-slate-400 block">Verifiable Predictions</span>
            </div>
            <div className="col-span-2 sm:col-span-1 space-y-1">
              <span className="text-xs font-mono text-cyan-400 font-bold block">BYOK Encrypted</span>
              <span className="text-[11px] text-slate-400 block">Complete Client Privacy</span>
            </div>
          </div>
        </section>

        {/* ── Call To Action Banner ── */}
        <section className="rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/60 via-slate-900/90 to-[#0c1426] p-8 sm:p-12 shadow-2xl relative overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-8 space-y-3">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Begin Your Journey with AstroOS
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
                Whether you are a learner, researcher or professional astrologer, AstroOS is your complete computational Vedic astrology companion.
              </p>
              <div className="pt-2 flex flex-wrap items-center gap-3">
                <Link
                  href="/charts"
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-bold px-6 py-3 text-xs sm:text-sm shadow-md transition hover:brightness-105"
                >
                  <span>Launch Workstation</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </Link>
                <span className="text-[11px] text-slate-400">
                  No credit card required · Instant access
                </span>
              </div>
            </div>

            <div className="md:col-span-4 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6 text-center md:text-left">
              <p className="font-serif italic text-xs sm:text-sm text-cyan-300/90 leading-relaxed">
                &ldquo;When ancient wisdom meets modern technology, clarity follows.&rdquo;
              </p>
              <span className="block mt-2 text-[10px] uppercase font-bold tracking-wider text-slate-400">
                AstroOS Computational Jyotish
              </span>
            </div>
          </div>
        </section>
      </main>

      {/* ── AstroOS Platform Footer ── */}
      <Footer />
    </div>
  );
}
