import { Metadata } from "next";
import ResearchWorkspace from "@/components/layout/ResearchWorkspace";

export const metadata: Metadata = {
  title: "Knowledge Base",
  description: "AstroOS Knowledge Base — Classical literature, slokas, and rule references",
};

export default function KnowledgeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ResearchWorkspace />;
}
