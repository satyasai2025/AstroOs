"use client";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="max-w-md w-full text-center space-y-4 rounded-2xl border border-rose-900/50 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-sm">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold text-xl">
          ⚠️
        </div>
        <h1 className="text-xl font-bold text-white">Something Went Wrong</h1>
        <p className="text-xs text-slate-400 leading-relaxed">
          {error.message || "An unexpected error occurred in the workspace."}
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <button
            onClick={() => reset()}
            className="rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold px-4 py-2.5 transition"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}
