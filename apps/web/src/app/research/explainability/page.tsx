import { PredictionExplainabilityStudio } from "@/components/research/PredictionExplainabilityStudio";

export const metadata = {
  title: "Research & Prediction Explainability | AstroOS Research",
  description:
    "Explainable astrological AI studio featuring exact mathematical factor decomposition, canonical shloka citations, and engine recalculation counterfactual sensitivity analysis.",
};

export default function ExplainabilityPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <PredictionExplainabilityStudio />
    </div>
  );
}
