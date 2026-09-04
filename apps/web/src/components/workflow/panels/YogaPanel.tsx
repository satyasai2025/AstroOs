import type { YogaEvaluationResponse } from "@/lib/types";

export function YogaPanel({ yogas }: { yogas: YogaEvaluationResponse }) {
  const present = yogas.results.filter((y) => y.is_present);

  return (
    <div className="glass-card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          Yogas
        </h3>
        <span className="text-xs text-slate-500">
          {yogas.total_present} present of {yogas.total_evaluated} evaluated
        </span>
      </div>

      {present.length === 0 ? (
        <p className="text-sm text-slate-400">No yogas detected for this chart.</p>
      ) : (
        <ul className="space-y-3">
          {present.map((y) => (
            <li key={y.yoga_id} className="border-b border-white/5 pb-3 last:border-none">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-100">{y.name}</span>
                {y.strength && (
                  <span className="rounded-full border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-xs capitalize text-amber-300">
                    {y.strength}
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {y.category} · {y.source_text}
              </p>
              {y.involved_planets.length > 0 && (
                <p className="mt-1 text-xs text-slate-400">
                  Involves: {y.involved_planets.join(", ")}
                  {y.involved_houses.length > 0 &&
                    ` · Houses: ${y.involved_houses.join(", ")}`}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
