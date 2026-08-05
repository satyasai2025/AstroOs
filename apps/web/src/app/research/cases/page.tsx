"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Card } from "@/components/ui";
import { AppShell } from "@/components/layout/AppShell";
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
    <AppShell sectionColor="--section-research">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Research Cases</h1>
        <p className="mt-2 text-sm text-gray-400">
          Browse imported research cases. Click any case to view its life-event timeline and details.
        </p>
      </div>

      {error && (
        <Card glow="gold" className="mb-6">
          <p className="text-red-400 m-0">{error}</p>
        </Card>
      )}

      {loading ? (
        <Card padding="0" className="p-8">
          <p className="text-gray-400 text-center m-0">Loading cases…</p>
        </Card>
      ) : cases.length === 0 ? (
        <Card padding="0" className="p-8">
          <p className="text-gray-400 text-center m-0">No cases imported yet. Try importing some sample cases.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {cases.map((c) => (
            <Link
              key={c.research_case_id}
              href={`/research/cases/${encodeURIComponent(c.research_case_id)}`}
              className="block no-underline"
            >
              <Card padding="0" className="p-4 hover:border-cyan-400/50 cursor-pointer transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-semibold text-gray-100">
                      {c.person_name || c.research_case_id}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      <code>{c.research_case_id}</code> · Born {c.dob} · {c.total_events}{" "}
                      {c.total_events === 1 ? "event" : "events"}
                    </div>
                  </div>
                  <Badge
                    tone={c.validation_status === "passed" ? "success" : "neutral"}
                    className="ml-4"
                  >
                    {c.validation_status}
                  </Badge>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}
