import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col justify-between bg-[#0b0f17] text-slate-100 px-4 py-6 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* ── Ambient Background Glows ── */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-cyan-500/15 via-violet-500/5 to-transparent blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[300px] bg-cyan-600/10 blur-3xl pointer-events-none" />

      {/* ── Top Header / Brand Bar ── */}
      <header className="relative z-10 mx-auto w-full max-w-6xl flex items-center justify-between pb-5 border-b border-slate-800">
        <Link href="/" aria-label="AstroOS Home" className="inline-flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl text-base font-bold shadow-md shadow-cyan-500/20 bg-gradient-to-br from-cyan-500 to-violet-600 text-white border border-cyan-400/40">
            ॐ
          </span>
          <span className="text-xl font-extrabold tracking-wide text-white">
            ASTRO<span className="text-cyan-400">OS</span>
          </span>
        </Link>

        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-xs font-bold text-slate-300 hover:text-cyan-400 transition"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="text-xs font-bold px-4 py-2 rounded-xl border border-cyan-500/40 bg-cyan-950/40 text-cyan-300 hover:bg-cyan-900/50 shadow-md shadow-cyan-500/10 transition-all"
          >
            Create Account
          </Link>
        </div>
      </header>

      {/* ── Main Hero Section ── */}
      <main className="relative z-10 mx-auto w-full max-w-5xl flex flex-1 flex-col items-center justify-center pt-10 pb-14 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-4 py-1.5 text-xs font-bold text-cyan-300 mb-6 shadow-md shadow-cyan-500/10 backdrop-blur-sm">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>Vedic Astrology Computational Workstation v2.0</span>
        </div>

        <h1 className="max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl text-white" style={{ lineHeight: 1.15 }}>
          Precision Vedic Analytics &<br />
          <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-violet-400 bg-clip-text text-transparent">
            Research Engine
          </span>
        </h1>

        <p className="mt-5 max-w-2xl text-sm sm:text-base leading-relaxed text-slate-300 font-medium">
          Accelerate chart analysis with real-time Swiss Ephemeris calculations, full multi-varga matrices, and dynamic predictive modeling.
        </p>

        {/* ── CTAs with High-Contrast Obsidian Glow Colors ── */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/login"
            className="rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-bold px-8 py-3 text-sm shadow-lg shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5"
          >
            Sign In to Workstation
          </Link>

          <Link
            href="/charts"
            className="rounded-xl border border-slate-700 bg-slate-900/60 hover:bg-slate-800 text-slate-200 font-bold px-7 py-3 text-sm shadow-md transition-all border-cyan-500/20 hover:border-cyan-500/40"
          >
            Interactive Dashboard
          </Link>

          <Link
            href="/register"
            className="rounded-xl border border-slate-700 bg-slate-900/40 hover:bg-slate-800 text-slate-300 font-bold px-6 py-3 text-sm transition-all"
          >
            Create Account
          </Link>
        </div>

        {/* ── 3-Column Feature Grid ── */}
        <div className="mt-16 grid w-full grid-cols-1 gap-6 text-left sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm hover:border-cyan-500/40 transition-all">
            <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 font-bold shadow-inner" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="m15 9-6 6" />
                <path d="m9 9 6 6" />
              </svg>
            </div>
            <h2 className="text-base font-bold text-slate-100">
              High-Precision Engine
            </h2>
            <p className="mt-2 text-xs font-medium leading-relaxed text-slate-300">
              Sub-arcsecond planetary computations powered by Swiss Ephemeris with customizable ayanamsha presets.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm hover:border-cyan-500/40 transition-all">
            <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 font-bold shadow-inner" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </div>
            <h2 className="text-base font-bold text-slate-100">
              Multi-Varga Mapping
            </h2>
            <p className="mt-2 text-xs font-medium leading-relaxed text-slate-300">
              Simultaneous D1–D60 divisional chart overlays with real-time aspect and strength metrics.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-sm hover:border-cyan-500/40 transition-all">
            <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 font-bold shadow-inner" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 3" />
              </svg>
            </div>
            <h2 className="text-base font-bold text-slate-100">
              Predictive Frameworks
            </h2>
            <p className="mt-2 text-xs font-medium leading-relaxed text-slate-300">
              Multi-tier dasha timelines integrated with transit heatmaps and Ashtakavarga score matrices.
            </p>
          </div>
        </div>
      </main>

      {/* ── Technical Specs Footer Strip ── */}
      <footer className="relative z-10 mx-auto w-full max-w-6xl border-t border-slate-800 pt-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
        <p className="text-xs font-bold text-slate-400">
          AstroOS Vedic Research Workstation
        </p>

        <div className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-bold font-mono border border-slate-800 bg-slate-900/80 text-slate-300 shadow-sm">
          <span>Swiss Ephemeris v2.10</span>
          <span className="text-cyan-400">·</span>
          <span>Ayanamsha: Lahiri / Chitra Paksha</span>
          <span className="text-cyan-400">·</span>
          <span>True Node Precision</span>
        </div>
      </footer>
    </div>
  );
}
