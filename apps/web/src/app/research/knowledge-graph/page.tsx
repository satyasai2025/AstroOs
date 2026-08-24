import { Metadata } from "next";
import { ResearchKnowledgeGraphStudio } from "@/components/research/ResearchKnowledgeGraphStudio";

export const metadata: Metadata = {
  title: "Research Knowledge Graph | AstroOS Research",
  description: "Evidence-Weighted Research Knowledge Graph with deterministic weights and non-causal disclosures.",
};

export default function ResearchKnowledgeGraphPage() {
  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <ResearchKnowledgeGraphStudio />
    </div>
  );
}
