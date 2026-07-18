import type { VerificationSummaryResponse } from "@/lib/types";

export function VerificationPanel({
  verification,
}: {
  verification: VerificationSummaryResponse | null;
}) {
  if (!verification) {
    return (
      <div className="glass-card p-5 text-sm text-slate-400">
        No life events are recorded for this chart yet, so there is nothing to verify rule
        predictions against. Record events for this chart, then re-run the analysis.
      </div>
    );
  }

  return (
    <div className="glass-card overflow-x-auto p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        Verification
      </h3>
      <p className="mb-3 text-xs text-slate-500">
        {verification.total_pairs} (rule, event) pairs across {verification.total_events}{" "}
        recorded events, {verification.total_rules_evaluated} distinct rules.
      </p>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
            <th className="py-2 pr-4">Rule</th>
            <th className="py-2 pr-4">Event</th>
            <th className="py-2 pr-4">Date</th>
            <th className="py-2 pr-4">Alignment</th>
            <th className="py-2">Strength</th>
          </tr>
        </thead>
        <tbody>
          {verification.pairs.map((p, i) => (
            <tr key={`${p.rule_id}-${p.event_id}-${i}`} className="border-b border-white/5 text-slate-200">
              <td className="py-2 pr-4">{p.rule_name}</td>
              <td className="py-2 pr-4">{p.event_title}</td>
              <td className="py-2 pr-4 text-xs text-slate-400">{p.event_date}</td>
              <td className="py-2 pr-4 text-xs capitalize">{p.alignment}</td>
              <td className="py-2 text-xs capitalize">{p.strength}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
