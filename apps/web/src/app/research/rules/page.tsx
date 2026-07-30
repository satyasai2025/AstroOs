"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Table, type TableColumn } from "@/components/ui";

interface RuleRow {
  id: string;
  name: string;
  source: string;
  category: string;
  confidence: number;
  status: "pending" | "approved" | "rejected";
}

/**
 * Illustrative rule-review queue matching the "Rule Validation" mockup —
 * this app has a real rule EVALUATION engine (RulesPanel.tsx, driven by
 * result.rule_results from the classical rules the backend already knows),
 * but no submission/approval workflow for proposing NEW rules. This page
 * stages that workflow with fabricated candidate rules, not real ones.
 */
const RULES: RuleRow[] = [
  { id: "r-1", name: "Gaja Kesari Yoga variant (Moon-Jupiter mutual aspect)", source: "BPHS Ch. 36", category: "Raj Yoga", confidence: 0.82, status: "pending" },
  { id: "r-2", name: "Kemadruma Yoga cancellation via Kendra planet", source: "Saravali", category: "Dosha Cancellation", confidence: 0.74, status: "pending" },
  { id: "r-3", name: "10th Lord in 2nd — wealth through profession", source: "Phaladeepika", category: "Career", confidence: 0.9, status: "approved" },
  { id: "r-4", name: "Rahu-Ketu axis on 7th-1st — unconventional partnerships", source: "Community submission", category: "Relationships", confidence: 0.51, status: "rejected" },
];

const STATUS_TONE: Record<RuleRow["status"], "gold" | "success" | "danger"> = {
  pending: "gold",
  approved: "success",
  rejected: "danger",
};

export default function RuleValidationPage() {
  const [rows, setRows] = useState(RULES);

  const setStatus = (id: string, status: RuleRow["status"]) =>
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)));

  const columns: TableColumn<RuleRow>[] = [
    { key: "name", label: "Rule" },
    { key: "source", label: "Source" },
    { key: "category", label: "Category" },
    { key: "confidence", label: "Confidence", align: "right", render: (r) => `${(r.confidence * 100).toFixed(0)}%` },
    { key: "status", label: "Status", render: (r) => <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge> },
    {
      key: "actions",
      label: "",
      render: (r) => (
        <div className="flex gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => setStatus(r.id, "approved")}>
            Approve Rule
          </Button>
          <Button size="sm" variant="danger" onClick={() => setStatus(r.id, "rejected")}>
            Reject Rule
          </Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Rule Validation
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Vedic Astrology Research — review candidate rules before they're added to the rule engine.
        </p>
      </div>

      <Card style={{ marginBottom: 12 }}>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Candidate rules below are illustrative samples. The rules that actually run against your
          charts (see the Rules tab after an analysis) come from a fixed, already-vetted classical
          rule set — this page stages a workflow for proposing and approving new ones.
        </p>
      </Card>

      <Table columns={columns} rows={rows} />
    </AppShell>
  );
}
