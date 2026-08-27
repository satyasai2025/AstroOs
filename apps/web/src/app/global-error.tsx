"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 flex items-center justify-center min-h-screen p-6">
        <div className="max-w-md w-full text-center space-y-4 rounded-2xl border border-rose-900/50 bg-slate-900/60 p-8 shadow-2xl">
          <h1 className="text-xl font-bold text-white">Application Error</h1>
          <p className="text-xs text-slate-400">
            {error.message || "A global application error occurred."}
          </p>
          <button
            onClick={() => reset()}
            className="rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold px-4 py-2.5 transition"
          >
            Reload Application
          </button>
        </div>
      </body>
    </html>
  );
}
