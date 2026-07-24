import { Metadata } from "next";
import ResearchWorkspace from "@/components/layout/ResearchWorkspace";

export const metadata: Metadata = {
  title: "Research Workspace",
  description: "AstroOS Vedic Research Workspace — Navigation shell with dynamic view switching",
};

export default function ResearchPage() {
  return <ResearchWorkspace />;
}
