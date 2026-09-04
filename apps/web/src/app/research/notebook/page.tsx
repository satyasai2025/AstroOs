"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card } from "@/components/ui";

interface Note {
  id: string;
  title: string;
  hypothesis: string;
  linkedCharts: string[];
  status: "review" | "confirmed" | "rejected";
}

/**
 * Illustrative research notebook matching the "Research Notebook" mockup —
 * there's no backend for freeform research notes/hypotheses linked to
 * multiple charts, so every note here is a fabricated sample.
 */
const NOTES: Note[] = [
  {
    id: "n-1",
    title: "Sade Sati correlates with career disruption",
    hypothesis: "Charts under Sade Sati at Saturn's natal position show a higher rate of job change within 18 months.",
    linkedCharts: ["Ravi Kumar", "Arjun Mehta"],
    status: "review",
  },
  {
    id: "n-2",
    title: "Gaja Kesari + strong 7th lord → early marriage",
    hypothesis: "When Gaja Kesari Yoga is present alongside a well-placed 7th lord, marriage tends to occur before age 27.",
    linkedCharts: ["Priya Sharma", "Ananya Iyer", "Vikram Singh"],
    status: "confirmed",
  },
];

const STATUS_TONE: Record<Note["status"], "gold" | "success" | "danger"> = {
  review: "gold",
  confirmed: "success",
  rejected: "danger",
};

export default function ResearchNotebookPage() {
  const [notes, setNotes] = useState(NOTES);
  const [activeId, setActiveId] = useState<string | null>(NOTES[0]?.id ?? null);

  const active = notes.find((n) => n.id === activeId) ?? null;

  const setStatus = (id: string, status: Note["status"]) =>
    setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, status } : n)));

  const removeNote = (id: string) => {
    setNotes((prev) => prev.filter((n) => n.id !== id));
    if (activeId === id) setActiveId(null);
  };

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Research Notebook
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Vedic Astrology Research — track hypotheses and the charts that support or refute them.
          </p>
        </div>
        <Button variant="primary">New Note</Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <Card padding="0">
          {notes.map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => setActiveId(n.id)}
              className="block w-full px-4 py-3 text-left transition"
              style={{
                borderBottom: "1px solid var(--border-subtle)",
                background: n.id === activeId ? "var(--surface-glass-strong)" : "transparent",
              }}
            >
              <p style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)" }}>{n.title}</p>
              <Badge tone={STATUS_TONE[n.status]}>{n.status}</Badge>
            </button>
          ))}
          {notes.length === 0 && (
            <p className="p-4 text-sm" style={{ color: "var(--text-muted)" }}>
              No notes left.
            </p>
          )}
        </Card>

        {active ? (
          <Card>
            <div className="mb-3 flex items-start justify-between gap-3">
              <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                {active.title}
              </h3>
              <Button variant="danger" size="sm" onClick={() => removeNote(active.id)}>
                Delete Note
              </Button>
            </div>

            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
              Hypothesis
            </h4>
            <p className="mb-4 text-sm" style={{ color: "var(--text-secondary)" }}>
              {active.hypothesis}
            </p>

            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
              Linked Charts
            </h4>
            <div className="mb-4 flex flex-wrap gap-1.5">
              {active.linkedCharts.map((c) => (
                <Badge key={c} tone="cyan">
                  {c}
                </Badge>
              ))}
            </div>

            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setStatus(active.id, "confirmed")}>
                Confirm Hypothesis
              </Button>
              <Button variant="ghost" onClick={() => setStatus(active.id, "rejected")}>
                Reject Hypothesis
              </Button>
            </div>
          </Card>
        ) : (
          <Card>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              Select a note to view its hypothesis and linked charts.
            </p>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
