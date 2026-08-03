"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Card } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { ResearchCaseSummary } from "@/lib/types";

export default function ResearchCasesListPage() {
  const [cases, setCases] = useState<ResearchCaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    researchCasesApi
      .list()
      .then((data) => setCases(data.cases))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load cases."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: "var(--space-4)", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ fontSize: "var(--text-xl)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)" }}>
        Research Cases
      </h1>
      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", marginTop: -8, marginBottom: "var(--space-3)" }}>
        Click a case to view its life-event timeline.
      </p>

      {loading && <div style={{ color: "var(--text-tertiary)" }}>Loading…</div>}
      {error && <div style={{ color: "var(--danger-400)" }}>{error}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {cases.map((c) => (
          <Link key={c.research_case_id} href={`/research/cases/${encodeURIComponent(c.research_case_id)}`} style={{ textDecoration: "none" }}>
            <Card style={{ cursor: "pointer" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ color: "var(--text-primary)", fontWeight: "var(--weight-semibold)" }}>
                    {c.person_name || c.research_case_id}
                  </div>
                  <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>
                    {c.research_case_id} · Born {c.dob} · {c.total_events} {c.total_events === 1 ? "event" : "events"}
                  </div>
                </div>
                <Badge tone={c.validation_status === "passed" ? "success" : "neutral"}>{c.validation_status}</Badge>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
