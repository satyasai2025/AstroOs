import { DecisionSynthesisStudio } from "@/components/research/DecisionSynthesisStudio";

export const metadata = {
  title: "Research Decision & Evidence Synthesis | AstroOS Research",
  description:
    "Defensible scientific decision synthesis, epistemic separation, contradiction radar, and P1 to P22 cryptographic lineage trace.",
};

export default function DecisionSynthesisPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <DecisionSynthesisStudio />
    </div>
  );
}
