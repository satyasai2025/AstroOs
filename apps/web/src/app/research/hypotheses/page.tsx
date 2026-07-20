"use client";

import { useState, useEffect, useCallback } from "react";
import { useCurrentUser } from "@/lib/auth";
import { hypothesisValidationApi } from "@/lib/research";
import type { HypothesisValidation } from "@/lib/research";

type StatusFilter = "" | "pending" | "confirmed" | "rejected";

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

  async function handleReview(
    id: string,
    status: "confirmed" | "rejected"
  ) {
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Hypothesis Validation
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Review and confirm or reject AI-generated hypotheses. Each hypothesis is
          flagged for human confirmation to ensure research integrity.
        </p>
      </div>

      {error && (
        <div
          className="rounded-lg border px-4 py-3 text-sm"
          style={{
            borderColor: "rgba(239, 68, 68, 0.3)",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            color: "#fca5a5",
          }}
          role="alert"
        >
          {error}
          <button
            type="button"
            onClick={() => setError(null)}
            className="ml-2 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Status filter & summary */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex gap-2">
          {[
            { value: "" as StatusFilter, label: `All (${total})`, color: "var(--text-secondary)" },
            {
              value: "pending" as StatusFilter,
              label: `Pending (${pendingCount})`,
              color: "#fbbf24",
            },
            {
              value: "confirmed" as StatusFilter,
              label: `Confirmed (${confirmedCount})`,
              color: "#22c55e",
            },
            {
              value: "rejected" as StatusFilter,
              label: `Rejected (${rejectedCount})`,
              color: "#fca5a5",
            },
          ].map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setStatusFilter(f.value)}
              className="rounded-full px-3 py-1 text-xs font-medium transition-colors"
              style={{
                backgroundColor:
                  statusFilter === f.value
                    ? "var(--accent)"
                    : "var(--bg-card)",
                color:
                  statusFilter === f.value
                    ? "var(--accent-text)"
                    : f.color,
                border: `1px solid ${
                  statusFilter === f.value ? "var(--accent)" : "var(--border-primary)"
                }`,
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex min-h-[40vh] items-center justify-center">
          <span
            className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-t-transparent"
            style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
          />
        </div>
      )}

      {!loading && validations.length === 0 && (
        <div
          className="flex flex-col items-center justify-center rounded-xl border py-16"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            {statusFilter
              ? `No ${statusFilter} hypotheses.`
              : "No hypotheses flagged for validation yet."}
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Flag hypotheses from the AI panel during chart analysis to start the
            validation workflow.
          </p>
        </div>
      )}

      {!loading && validations.length > 0 && (
        <div className="space-y-4">
          {validations.map((v) => (
            <div
              key={v.id}
              className="rounded-xl border p-4"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-card)",
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                      {v.title}
                    </h3>
                    <span
                      className="rounded-full px-2 py-0.5 text-xs uppercase tracking-wide"
                      style={{
                        backgroundColor:
                          v.status === "confirmed"
                            ? "rgba(34, 197, 94, 0.15)"
                            : v.status === "rejected"
                              ? "rgba(239, 68, 68, 0.15)"
                              : v.status === "needs_revision"
                                ? "rgba(251, 191, 36, 0.15)"
                                : "rgba(148, 163, 184, 0.15)",
                        color:
                          v.status === "confirmed"
                            ? "#22c55e"
                            : v.status === "rejected"
                              ? "#fca5a5"
                              : v.status === "needs_revision"
                                ? "#fbbf24"
                                : "var(--text-muted)",
                      }}
                    >
                      {v.status}
                    </span>
                    {v.ai_generated && (
                      <span
                        className="rounded-full px-2 py-0.5 text-xs"
                        style={{
                          backgroundColor: "rgba(139, 92, 246, 0.15)",
                          color: "#a78bfa",
                        }}
                      >
                        AI-generated
                      </span>
                    )}
                  </div>

                  <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                    {v.description}
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
                    <span
                      className="rounded px-1.5 py-0.5"
                      style={{ backgroundColor: "var(--bg-secondary)" }}
                    >
                      {v.hypothesis_id}
                    </span>
                    <span
                      className="rounded px-1.5 py-0.5"
                      style={{ backgroundColor: "var(--bg-secondary)" }}
                    >
                      Domain: {v.domain}
                    </span>
                    {v.reviewed_at && (
                      <span>
                        Reviewed: {new Date(v.reviewed_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  {/* Reviewer notes */}
                  {v.reviewer_notes && (
                    <div
                      className="mt-2 rounded border p-2 text-xs"
                      style={{
                        borderColor: "var(--border-primary)",
                        backgroundColor: "var(--bg-secondary)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <span className="font-medium" style={{ color: "var(--text-muted)" }}>
                        Reviewer notes:
                      </span>{" "}
                      {v.reviewer_notes}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                  {v.status === "pending" && (
                    <>
                      {reviewingId === v.id ? (
                        <div className="flex items-center gap-2">
                          <textarea
                            value={reviewNotes}
                            onChange={(e) => setReviewNotes(e.target.value)}
                            placeholder="Optional notes..."
                            rows={2}
                            className="rounded-lg border px-2 py-1 text-xs outline-none"
                            style={{
                              borderColor: "var(--border-primary)",
                              backgroundColor: "var(--bg-input)",
                              color: "var(--text-primary)",
                              width: "180px",
                            }}
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
                              className="rounded-lg px-3 py-1 text-xs"
                              style={{
                                border: "1px solid var(--border-primary)",
                                color: "var(--text-muted)",
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setReviewingId(v.id)}
                          className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-500 transition-colors"
                        >
                          Review
                        </button>
                      )}
                    </>
                  )}

                  <button
                    type="button"
                    onClick={() => handleDelete(v.id)}
                    className="rounded-lg px-3 py-1.5 text-xs transition-colors"
                    style={{
                      border: "1px solid rgba(239, 68, 68, 0.3)",
                      color: "#fca5a5",
                    }}
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
  );
}
