"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Table, type TableColumn } from "@/components/ui";

interface EventRow {
  id: string;
  chartSubject: string;
  eventTitle: string;
  eventDate: string;
  ruleMatched: string;
  status: "pending" | "verified" | "flagged";
}

/**
 * Illustrative event-verification queue matching the "Event Verification"
 * mockup — cross-chart, rule-vs-life-event verification at this scale
 * (queue/review workflow across many charts) doesn't exist as a backend
 * feature yet. Per-chart verification IS real (see result.verification /
 * VerificationPanel.tsx, driven by /api/v1/verification), this page is a
 * staged UI for a broader multi-chart review workflow that isn't built.
 */
const EVENTS: EventRow[] = [
  { id: "ev-1", chartSubject: "Ravi Kumar", eventTitle: "Marriage", eventDate: "2019-11-14", ruleMatched: "7th Lord conjunct Venus", status: "pending" },
  { id: "ev-2", chartSubject: "Priya Sharma", eventTitle: "Career Promotion", eventDate: "2022-03-02", ruleMatched: "10th Lord in Kendra", status: "verified" },
  { id: "ev-3", chartSubject: "Arjun Mehta", eventTitle: "Relocation Abroad", eventDate: "2021-08-19", ruleMatched: "12th Lord strong in Lagna", status: "pending" },
  { id: "ev-4", chartSubject: "Ananya Iyer", eventTitle: "Health Event", eventDate: "2023-01-27", ruleMatched: "Sade Sati (natal Moon)", status: "flagged" },
];

const STATUS_TONE: Record<EventRow["status"], "gold" | "success" | "danger"> = {
  pending: "gold",
  verified: "success",
  flagged: "danger",
};

export default function EventVerificationPage() {
  const [rows, setRows] = useState(EVENTS);

  const setStatus = (id: string, status: EventRow["status"]) =>
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)));

  const columns: TableColumn<EventRow>[] = [
    { key: "chartSubject", label: "Subject" },
    { key: "eventTitle", label: "Event" },
    { key: "eventDate", label: "Date" },
    { key: "ruleMatched", label: "Rule Matched" },
    { key: "status", label: "Status", render: (r) => <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge> },
    {
      key: "actions",
      label: "",
      render: (r) => (
        <div className="flex gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => setStatus(r.id, "verified")}>
            Verify Event
          </Button>
          <Button size="sm" variant="danger" onClick={() => setStatus(r.id, "flagged")}>
            Flag Event
          </Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Event Verification
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Vedic Astrology Research — review rule-matched life events across charts.
        </p>
      </div>

      <Card style={{ marginBottom: 12 }}>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Sample review queue shown below is illustrative. Per-chart verification against a single
          subject's real life events already exists (see the Verification tab after running an
          analysis) — this page stages what a cross-chart review workflow could look like.
        </p>
      </Card>

      <Table columns={columns} rows={rows} />
    </AppShell>
  );
}
