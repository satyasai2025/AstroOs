import { Metadata } from "next";
import { ResearchDecisionActionStudio } from "@/components/research/ResearchDecisionActionStudio";

export const metadata: Metadata = {
  title: "Research Decision & Action Engine | AstroOS Research",
  description:
    "Priority 25: Authoritative empirical research action layer synthesizing P19-P24 into concrete execution decisions.",
};

export default function ResearchDecisionActionPage() {
  return <ResearchDecisionActionStudio />;
}
