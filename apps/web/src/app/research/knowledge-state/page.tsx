import { Metadata } from "next";
import { ResearchKnowledgeStateStudio } from "@/components/research/ResearchKnowledgeStateStudio";

export const metadata: Metadata = {
  title: "Longitudinal Evidence Synthesis & Research Knowledge State Engine | AstroOS Research",
  description:
    "Priority 36: Versioned Research Knowledge State Machine (RKSM) & Meta-Analytic Evidence Weighting (MAEWE) over accumulated multi-study research lineage.",
};

export default function ResearchKnowledgeStatePage() {
  return <ResearchKnowledgeStateStudio />;
}
