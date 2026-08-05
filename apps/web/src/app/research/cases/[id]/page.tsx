"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { CaseTimelinePanel } from "@/components/research/CaseTimelinePanel";

export default function ResearchCaseTimelinePage() {
  const params = useParams();
  const researchCaseId = params.id as string;
  return (
    <AppShell sectionColor="--section-research">
      <CaseTimelinePanel researchCaseId={researchCaseId} />
    </AppShell>
  );
}
