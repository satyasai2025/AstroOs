import { Metadata } from "next";
import { ResearchForensicStudio } from "@/components/research/ResearchForensicStudio";

export const metadata: Metadata = {
  title: "Research Forensics & Evidence Reconstruction | AstroOS Research",
  description:
    "Priority 31: Deterministic forensic reconstruction engine. Audits evidence integrity, detects calculation drift, and classifies synthetic vs real-world evidence.",
};

export default function ResearchForensicPage() {
  return <ResearchForensicStudio />;
}
