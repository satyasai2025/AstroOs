import { BatchResearchOptimizationStudio } from "@/components/research/BatchResearchOptimizationStudio";

export const metadata = {
  title: "Large-Scale Batch Cohort Optimizer | AstroOS Research",
  description:
    "High-throughput distributed and local cohort optimization studio featuring multi-worker parallel execution, incremental chunk streaming, and state checkpointing.",
};

export default function BatchOptimizerPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <BatchResearchOptimizationStudio />
    </div>
  );
}
