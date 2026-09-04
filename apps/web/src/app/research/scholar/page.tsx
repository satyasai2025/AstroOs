import { Metadata } from "next";
import { ScholarChroniclesStudio } from "@/components/research/ScholarChroniclesStudio";

export const metadata: Metadata = {
  title: "Learning with Antigravity: The Empirical Jyotish Chronicles | AstroOS Research",
  description:
    "Autonomous Scholar Blog & Publishing Engine uniting Classical Sanskrit Shastra with 66,000+ Case Empirical Data Science, auto-published to Medium and Hashnode.",
};

export default function ScholarChroniclesPage() {
  return <ScholarChroniclesStudio />;
}
