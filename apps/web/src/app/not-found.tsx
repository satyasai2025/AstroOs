"use client";

import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="max-w-md w-full text-center space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-sm">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-bold text-xl">
          404
        </div>
        <h1 className="text-xl font-bold text-white">Page Not Found</h1>
        <p className="text-xs text-slate-400 leading-relaxed">
          The astrological workspace or tool you requested could not be located.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link
            href="/dashboard"
            className="rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold px-4 py-2.5 transition"
          >
            Dashboard
          </Link>
          <Link
            href="/charts/sbc"
            className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold px-4 py-2.5 transition"
          >
            SBC Tool
          </Link>
        </div>
      </div>
    </div>
  );
}
