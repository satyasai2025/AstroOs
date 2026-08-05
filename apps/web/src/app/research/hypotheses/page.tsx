"use client";

import { useState, useEffect, useCallback } from "react";
import { useCurrentUser } from "@/lib/auth";
import { hypothesisValidationApi } from "@/lib/research";
import type { HypothesisValidation } from "@/lib/research";
import { AppShell } from "@/components/layout/AppShell";

type StatusFilter = "" | "pending" | "confirmed" | "rejected";

const STATUS_BADGE_CLASS: Record<string, string> = {
  confirmed: "bg-emerald-500/15 text-emerald-400",
  rejected: "bg-red-500/15 text-red-300",
  needs_revision: "bg-amber-500/15 text-amber-400",
};

export default function HypothesisValidationPage() {
  const { data: user } = useCurrentUser();
  const [validations, setValidations] = useState<HypothesisValidation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [total, setTotal] = useState(0);

  // Review form state
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await hypothesisValidationApi.list({
        status: statusFilter || undefined,
        limit: 100,
      });
      setValidations(data.validations);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load validations.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleReview(id: string, status: "confirmed" | "rejected") {
    setError(null);
    try {
      await hypothesisValidationApi.update(id, {
        status,
        reviewer_notes: reviewNotes.trim() || null,
      });
      setReviewingId(null);
      setReviewNotes("");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update validation.");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this validation record?")) return;
    try {
      await hypothesisValidationApi.delete(id);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete validation.");
    }
  }

  const pendingCount = validations.filter((v) => v.status === "pending").length;
  const confirmedCount = validations.filter((v) => v.status === "confirmed").length;
  const rejectedCount = validations.filter((v) => v.status === "rejected").length;

  return (
    <AppShell sectionColor="--section-research">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Hypothesis Validation</h1>
          <p className="mt-2 text-sm text-gray-400">
            Review and confirm or reject AI-generated hypotheses. Each hypothesis is flagged for human
            confirmation to ensure research integrity.
          </p>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">
            {error}
            <button type="button" onClick={() => setError(null)} className="ml-2 underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Status filter & summary */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            { value: "" as StatusFilter, label: `All (${total})` },
            { value: "pending" as StatusFilter, label: `Pending (${pendingCount})` },
            { value: "confirmed" as StatusFilter, label: `Confirmed (${confirmedCount})` },
            { value: "rejected" as StatusFilter, label: `Rejected (${rejectedCount})` },
          ].map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setStatusFilter(f.value)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === f.value
                  ? "border-cyan-400 bg-cyan-400/10 text-cyan-300"
                  : "border-gray-700 bg-transparent text-gray-400 hover:bg-white/5"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex min-h-[40vh] items-center justify-center">
            <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
          </div>
        )}

        {!loading && validations.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-gray-700 bg-white/5 py-16">
            <p className="text-sm text-gray-500">
              {statusFilter ? `No ${statusFilter} hypotheses.` : "No hypotheses flagged for validation yet."}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Flag hypotheses from the AI panel during chart analysis to start the validation workflow.
            </p>
          </div>
        )}

        {!loading && validations.length > 0 && (
          <div className="space-y-4">
            {validations.map((v) => (
              <div key={v.id} className="rounded-xl border border-gray-700 bg-white/5 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-gray-100">{v.title}</h3>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs uppercase tracking-wide ${
                          STATUS_BADGE_CLASS[v.status] ?? "bg-gray-500/15 text-gray-400"
                        }`}
                      >
                        {v.status}
                      </span>
                      {v.ai_generated && (
                        <span className="rounded-full bg-violet-500/15 px-2 py-0.5 text-xs text-violet-300">
                          AI-generated
                        </span>
                      )}
                    </div>

                    <p className="mt-1 text-sm text-gray-400">{v.description}</p>

                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                      <span className="rounded bg-black/30 px-1.5 py-0.5">{v.hypothesis_id}</span>
                      <span className="rounded bg-black/30 px-1.5 py-0.5">Domain: {v.domain}</span>
                      {v.reviewed_at && <span>Reviewed: {new Date(v.reviewed_at).toLocaleDateString()}</span>}
                    </div>

                    {/* Reviewer notes */}
                    {v.reviewer_notes && (
                      <div className="mt-2 rounded border border-gray-700 bg-black/30 p-2 text-xs text-gray-400">
                        <span className="font-medium text-gray-500">Reviewer notes:</span> {v.reviewer_notes}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="ml-4 flex flex-shrink-0 items-center gap-2">
                    {v.status === "pending" && (
                      <>
                        {reviewingId === v.id ? (
                          <div className="flex items-center gap-2">
                            <textarea
                              value={reviewNotes}
                              onChange={(e) => setReviewNotes(e.target.value)}
                              placeholder="Optional notes..."
                              rows={2}
                              className="w-[180px] rounded-lg border border-gray-700 bg-black/40 px-2 py-1 text-xs text-gray-100 outline-none"
                            />
                            <div className="flex flex-col gap-1">
                              <button
                                type="button"
                                onClick={() => handleReview(v.id, "confirmed")}
                                className="rounded-lg bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-500"
                              >
                                Confirm
                              </button>
                              <button
                                type="button"
                                onClick={() => handleReview(v.id, "rejected")}
                                className="rounded-lg bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500"
                              >
                                Reject
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setReviewingId(null);
                                  setReviewNotes("");
                                }}
                                className="rounded-lg border border-gray-700 px-3 py-1 text-xs text-gray-500"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setReviewingId(v.id)}
                            className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-amber-500"
                          >
                            Review
                          </button>
                        )}
                      </>
                    )}

                    <button
                      type="button"
                      onClick={() => handleDelete(v.id)}
                      className="rounded-lg border border-red-500/30 px-3 py-1.5 text-xs text-red-300 transition-colors"
                      aria-label={`Delete validation for ${v.title}`}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
