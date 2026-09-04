import { Metadata } from "next";
import { ResearchBenchmarkExpansionStudio } from "@/components/research/ResearchBenchmarkExpansionStudio";

export const metadata: Metadata = {
  title: "Research Benchmark Expansion | AstroOS Research",
  description:
    "Priority 29: Governed multi-domain benchmarks across Career, Wealth, and Vitality with strict non-medical guardrails.",
};

export default function ResearchBenchmarkExpansionPage() {
  return <ResearchBenchmarkExpansionStudio />;
}
