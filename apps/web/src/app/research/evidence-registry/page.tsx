import { Metadata } from "next";
import { ResearchEvidenceRegistryStudio } from "@/components/research/ResearchEvidenceRegistryStudio";

export const metadata: Metadata = {
  title: "Real-World Evidence Intake & Outcome Registry | AstroOS Research",
  description:
    "Priority 32: Governed outcome observation registry for recording real-world events with append-only audit provenance and non-causal disclosures.",
};

export default function ResearchEvidenceRegistryPage() {
  return <ResearchEvidenceRegistryStudio />;
}
