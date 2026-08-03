"use client";

import { useParams } from "next/navigation";
import { CaseTimelinePanel } from "@/components/research/CaseTimelinePanel";

export default function ResearchCaseTimelinePage() {
  const params = useParams();
  const researchCaseId = params.id as string;
  return <CaseTimelinePanel researchCaseId={researchCaseId} />;
}
