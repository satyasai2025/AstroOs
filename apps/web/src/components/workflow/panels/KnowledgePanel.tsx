import type { KnowledgeSearchResultResponse } from "@/lib/types";

export function KnowledgePanel({
  citations,
}: {
  citations: KnowledgeSearchResultResponse[];
}) {
  return (
    <div className="glass-card p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        Knowledge Citations
      </h3>
      <p className="mb-3 text-xs text-slate-500">
        Best-effort keyword correlation against detected yogas — not a semantic citation
        engine.
      </p>

      {citations.length === 0 ? (
        <p className="text-sm text-slate-400">No matching classical citations found.</p>
      ) : (
        <ul className="space-y-3">
          {citations.map((c) => (
            <li key={`${c.entity_type}-${c.entity_id}`} className="border-b border-white/5 pb-3 last:border-none">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-100">{c.title}</span>
                <span className="rounded-full border border-cosmos-600/40 bg-cosmos-800/40 px-2 py-0.5 text-xs capitalize text-slate-400">
                  {c.entity_type}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-400">{c.snippet}</p>
              {c.book_title && (
                <p className="mt-1 text-xs text-slate-500">From: {c.book_title}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
