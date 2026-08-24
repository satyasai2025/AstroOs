import { Metadata } from "next";
import { ResearchValidityStudio } from "@/components/research/ResearchValidityStudio";

export const metadata: Metadata = {
  title: "Research Validity & Statistical Integrity Engine | AstroOS Research",
  description:
    "Priority 33: Independent research validity and statistical integrity engine. Evaluates sample quality, temporal integrity, baseline comparison, data leakage, and conservative verdicts.",
};

export default function ResearchValidityPage() {
  return <ResearchValidityStudio />;
}
