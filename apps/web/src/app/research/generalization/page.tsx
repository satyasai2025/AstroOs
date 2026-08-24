import { Metadata } from "next";
import { ResearchGeneralizationStudio } from "@/components/research/ResearchGeneralizationStudio";

export const metadata: Metadata = {
  title: "External Validity & Generalization Engine | AstroOS Research",
  description:
    "Priority 35: Independent research external validity, generalization, and domain transportability platform.",
};

export default function ResearchGeneralizationPage() {
  return <ResearchGeneralizationStudio />;
}
