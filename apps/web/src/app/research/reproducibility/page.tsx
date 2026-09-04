import { ResearchReproducibilityStudio } from "@/components/research/ResearchReproducibilityStudio";

export const metadata = {
  title: "Research Reproducibility & Independent Validation | AstroOS Research",
  description:
    "Cryptographic research-run manifest replay studio, zero-leakage independent re-execution, and exact result-diff audit engine.",
};

export default function ReproducibilityPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <ResearchReproducibilityStudio />
    </div>
  );
}
