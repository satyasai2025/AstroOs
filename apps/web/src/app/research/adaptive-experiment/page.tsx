import { Metadata } from "next";
import { ResearchAdaptiveExperimentStudio } from "@/components/research/ResearchAdaptiveExperimentStudio";

export const metadata: Metadata = {
  title: "Adaptive Research & Sequential Experiment Studio | AstroOS Research",
  description:
    "Priority 28: Sequential interim testing with configurable alpha spending, post-hoc prevention, & blinded sample size re-estimation.",
};

export default function ResearchAdaptiveExperimentPage() {
  return <ResearchAdaptiveExperimentStudio />;
}
