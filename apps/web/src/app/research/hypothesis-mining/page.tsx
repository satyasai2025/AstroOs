import { HypothesisMiningStudio } from "@/components/research/HypothesisMiningStudio";

export const metadata = {
  title: "Research Discovery & Hypothesis Mining | AstroOS Research",
  description:
    "Automated astrological pattern discovery engine featuring Benjamini-Hochberg FDR control and independent holdout cohort replication testing.",
};

export default function HypothesisMiningPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <HypothesisMiningStudio />
    </div>
  );
}
