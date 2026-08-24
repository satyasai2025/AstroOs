import { Metadata } from "next";
import { ResearchPortfolioPlannerStudio } from "@/components/research/ResearchPortfolioPlannerStudio";

export const metadata: Metadata = {
  title: "Research Portfolio & Experiment Planner | AstroOS Research",
  description:
    "Priority 26: Deterministic EvidencePriorityScore ranking & dynamically constrained scientific compute allocation.",
};

export default function ResearchPortfolioPlannerPage() {
  return <ResearchPortfolioPlannerStudio />;
}
