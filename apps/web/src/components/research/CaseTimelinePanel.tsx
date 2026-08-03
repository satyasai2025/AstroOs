"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { ResearchCaseDetail } from "@/lib/types";
import { EventTimelineChart } from "./EventTimelineChart";

interface CaseTimelinePanelProps {
  researchCaseId: string;
}

export function CaseTimelinePanel({ researchCaseId }: CaseTimelinePanelProps) {
  const [detail, setDetail] = useState<ResearchCaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    researchCasesApi
      .getDetail(researchCaseId)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load case.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [researchCaseId]);

  return (
    <div style={{ padding: "var(--space-4)", maxWidth: 1100, margin: "0 auto" }}>
      <Link href="/research/cases" style={{ fontSize: "var(--text-sm)", color: "var(--cyan-400)", textDecoration: "none" }}>
        ← All research cases
      </Link>

      {loading && (
        <div style={{ color: "var(--text-tertiary)", padding: "var(--space-4)" }}>Loading case…</div>
      )}

      {error && (
        <div style={{ color: "var(--danger-400)", padding: "var(--space-4)" }}>{error}</div>
      )}

      {detail && (
        <>
          <div style={{ margin: "var(--space-3) 0" }}>
            <h1 style={{ fontSize: "var(--text-xl)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)", margin: 0 }}>
              {detail.person_name || detail.research_case_id}
            </h1>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", margin: "2px 0 0" }}>
              {detail.research_case_id} · Born {detail.dob}
              {detail.gender ? ` · ${detail.gender}` : ""} · {detail.life_events.length}{" "}
              {detail.life_events.length === 1 ? "event" : "events"}
            </p>
          </div>

          <Card>
            <EventTimelineChart events={detail.life_events} />
          </Card>
        </>
      )}
    </div>
  );
}
