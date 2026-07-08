import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-4">
      {/* Cosmic background rings */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full border border-cosmos-700/20 animate-spin-slow" />
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[400px] w-[400px] rounded-full border border-amber-500/10" />
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[200px] w-[200px] rounded-full border border-cosmos-500/20" />
      </div>

      <div className="relative z-10 max-w-2xl text-center animate-fade-in">
        {/* Sanskrit symbol */}
        <div className="mb-6 text-5xl font-vedic text-amber-400 drop-shadow-[0_0_24px_rgba(251,191,36,0.5)]">
          ॐ
        </div>

        <h1 className="mb-3 text-5xl font-bold tracking-tight text-white">
          Astro<span className="text-amber-400">OS</span>
        </h1>

        <p className="mb-2 text-lg font-vedic text-amber-300/80">
          वैदिक ज्योतिष अनुसंधान मंच
        </p>

        <p className="mb-10 text-slate-400 leading-relaxed">
          A production-grade Vedic Astrology research platform for scholars,
          practitioners, and researchers. Built on Swiss Ephemeris with full
          divisional chart support, dasha systems, and ashtakavarga.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/login" className="btn-primary text-base px-8 py-3">
            Sign In
          </Link>
          <Link href="/register" className="btn-ghost text-base px-8 py-3">
            Create Account
          </Link>
        </div>

        {/* Status badges */}
        <div className="mt-12 flex flex-wrap justify-center gap-3">
          {[
            "Swiss Ephemeris",
            "Navagraha",
            "27 Nakshatras",
            "16 Vargas",
            "Vimshottari Dasha",
            "Ashtakavarga",
          ].map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-cosmos-600/40 bg-cosmos-800/40 px-3 py-1 text-xs text-slate-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </main>
  );
}
