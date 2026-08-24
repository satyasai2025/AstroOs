import { CohortValidationStudio } from "@/components/research/CohortValidationStudio";

export const metadata = {
  title: "Longitudinal Cohort Statistical Validation | AstroOS Research",
  description:
    "Mass longitudinal cohort statistical benchmarking, empirical ROC-AUC / Brier scores, and Monte Carlo label permutation null hypothesis testing.",
};

export default function CohortPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <CohortValidationStudio />
    </div>
  );
}
