import { Metadata } from "next";
import { ResearchReplicationStudio } from "@/components/research/ResearchReplicationStudio";

export const metadata: Metadata = {
  title: "Research Reproducibility, Replication & Falsification Engine | AstroOS Research",
  description:
    "Priority 34: Independent research reproducibility, replication, and falsification platform. Stress-tests claims against dataset independence, negative controls, and null models.",
};

export default function ResearchReplicationPage() {
  return <ResearchReplicationStudio />;
}
