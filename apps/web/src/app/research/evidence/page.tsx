import { EvidenceIntelligenceStudio } from "@/components/research/EvidenceIntelligenceStudio";

export const metadata = {
  title: "Research Knowledge & Evidence Intelligence | AstroOS Research",
  description:
    "Systematic evidence intelligence layer evaluating empirical hit rates, odds ratios, epistemic quality grades, and multi-technique synergies across historical life events.",
};

export default function EvidencePage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <EvidenceIntelligenceStudio />
    </div>
  );
}
