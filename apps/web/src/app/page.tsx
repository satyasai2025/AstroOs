import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col justify-between bg-slate-50 dark:bg-[#0b0f17] text-slate-900 dark:text-slate-100 px-4 py-6 sm:px-6 lg:px-8 relative overflow-hidden transition-colors duration-200">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute left-1/2 top-1/4 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[700px] rounded-full bg-cyan-500/10 dark:bg-cyan-500/5 blur-[120px]" />
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[350px] w-[500px] rounded-full bg-amber-500/10 dark:bg-amber-500/5 blur-[100px]" />
      </div>

      {/* ── Top Header / Brand Bar ── */}
      <header className="relative z-10 mx-auto w-full max-w-6xl flex items-center justify-between pb-5 border-b border-slate-200 dark:border-slate-800">
        <Link href="/" className="inline-flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold shadow-sm bg-cyan-600 text-white dark:bg-cyan-500 dark:text-slate-950">
            ॐ
          </span>
          <span className="text-xl font-bold tracking-wide text-slate-900 dark:text-white">
            ASTRO<span className="text-cyan-600 dark:text-cyan-400">OS</span>
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-xs font-semibold px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="text-xs font-semibold px-3.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white/50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 shadow-sm transition"
          >
            Create Account
          </Link>
        </div>
      </header>

      {/* ── Main Hero Section (Reduced Top Padding) ── */}
      <main className="relative z-10 mx-auto w-full max-w-5xl flex flex-1 flex-col items-center justify-center pt-8 pb-12 text-center animate-fade-in">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 px-3.5 py-1 text-xs font-medium mb-5 shadow-sm text-cyan-700 dark:text-cyan-400">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-600 dark:bg-cyan-400 animate-pulse" />
          <span>Vedic Astrology Computational Workstation</span>
        </div>

        <h1 className="max-w-4xl text-3xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl text-slate-900 dark:text-white" style={{ lineHeight: 1.15 }}>
          Precision Vedic Analytics &<br />
          <span className="text-cyan-600 dark:text-cyan-400">Research Engine</span>
        </h1>

        <p className="mt-4 max-w-2xl text-sm sm:text-base leading-relaxed text-slate-600 dark:text-slate-300">
          Accelerate chart analysis with real-time Swiss Ephemeris calculations, full multi-varga matrices, and dynamic predictive modeling.
        </p>

        {/* ── CTAs with High-Contrast Accessible Colors ── */}
        <div className="mt-7 flex flex-wrap items-center justify-center gap-3.5">
          <Link
            href="/login"
            className="rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-7 py-2.5 text-sm font-semibold shadow-md shadow-cyan-500/20 transition-all"
          >
            Sign In to Workstation
          </Link>

          <Link
            href="/register"
            className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white/50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 px-6 py-2.5 text-sm font-semibold shadow-sm transition-all"
          >
            Create Account
          </Link>
        </div>

        {/* ── 3-Column Feature Grid (Below the Fold) ── */}
        <div className="mt-14 grid w-full grid-cols-1 gap-5 text-left sm:grid-cols-3">
          <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-xl shadow-slate-200/50 dark:shadow-none transition hover:border-cyan-500/50 dark:hover:border-cyan-500/50">
            <div className="mb-3.5 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400 border border-cyan-100 dark:border-cyan-900/50">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="m15 9-6 6" />
                <path d="m9 9 6 6" />
              </svg>
            </div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              High-Precision Engine
            </h2>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
              Sub-arcsecond planetary computations powered by Swiss Ephemeris with customizable ayanamsha presets.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-xl shadow-slate-200/50 dark:shadow-none transition hover:border-cyan-500/50 dark:hover:border-cyan-500/50">
            <div className="mb-3.5 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400 border border-cyan-100 dark:border-cyan-900/50">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Multi-Varga Mapping
            </h2>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
              Simultaneous D1–D60 divisional chart overlays with real-time aspect and strength metrics.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-xl shadow-slate-200/50 dark:shadow-none transition hover:border-cyan-500/50 dark:hover:border-cyan-500/50">
            <div className="mb-3.5 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600 dark:text-cyan-400 border border-cyan-100 dark:border-cyan-900/50">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 3" />
              </svg>
            </div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Predictive Frameworks
            </h2>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
              Multi-tier dasha timelines integrated with transit heatmaps and Ashtakavarga score matrices.
            </p>
          </div>
        </div>
      </main>

      {/* ── Subtle Technical Specs Footer Strip ── */}
      <footer className="relative z-10 mx-auto w-full max-w-6xl border-t border-slate-200 dark:border-slate-800 pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
        <p className="text-[11px] text-slate-500 dark:text-slate-400">
          AstroOS Vedic Research Workstation
        </p>

        <div className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-[10px] font-mono border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 text-slate-600 dark:text-slate-400 shadow-sm">
          <span>Swiss Ephemeris v2.10</span>
          <span>·</span>
          <span>Ayanamsha: Lahiri / Chitra Paksha</span>
          <span>·</span>
          <span>True Node Precision</span>
        </div>
      </footer>
    </div>
  );
}


