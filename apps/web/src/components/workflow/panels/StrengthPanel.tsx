import { RASHI_NAMES_EN as RASHI_NAMES } from "@/lib/astro";
import type { AllAshtakavargaResponse, ShadbalaTotalResponse } from "@/lib/types";

export function StrengthPanel({
  shadbala,
  ashtakavarga,
}: {
  shadbala: ShadbalaTotalResponse[];
  ashtakavarga: AllAshtakavargaResponse;
}) {
  const maxRupas = Math.max(...shadbala.map((s) => s.total_rupas), 1);

  return (
    <div className="space-y-6">
      <div className="glass-card p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          Shadbala (Rupas)
        </h3>
        <div className="space-y-2">
          {shadbala.map((s) => (
            <div key={s.planet} className="flex items-center gap-3">
              <span className="w-20 shrink-0 text-sm capitalize text-slate-300">{s.planet}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-amber-500"
                  style={{ width: `${Math.min(100, (s.total_rupas / maxRupas) * 100)}%` }}
                />
              </div>
              <span className="w-14 shrink-0 text-right text-xs text-slate-400">
                {s.total_rupas.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card p-5">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">
            Sarvashtakavarga
          </h3>
          <span
            className={
              ashtakavarga.sarvashtakavarga.checksum_valid
                ? "text-xs text-emerald-400"
                : "text-xs text-red-400"
            }
          >
            {ashtakavarga.sarvashtakavarga.checksum_valid ? "✓ Checksum valid (337)" : "✗ Checksum invalid"}
          </span>
        </div>
        <div className="grid grid-cols-6 gap-2 sm:grid-cols-12">
          {ashtakavarga.sarvashtakavarga.bindus_by_rashi.map((count, i) => (
            <div key={RASHI_NAMES[i]} className="rounded-lg bg-white/5 p-2 text-center">
              <p className="text-xs text-slate-500">{RASHI_NAMES[i].slice(0, 3)}</p>
              <p className="text-lg font-semibold text-slate-100">{count}</p>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Total: {ashtakavarga.sarvashtakavarga.total_bindus} bindus
        </p>
      </div>
    </div>
  );
}
