import { Metadata } from "next";
import { ResearchPublicationStudio } from "@/components/research/ResearchPublicationStudio";

export const metadata: Metadata = {
  title: "Research Publication & Cryptographic Audit Report | AstroOS Research",
  description:
    "Priority 30: Publication-grade reproducible research report with complete P1→P29 pipeline evidence and cryptographic audit chain.",
};

export default function ResearchPublicationPage() {
  return <ResearchPublicationStudio />;
}
