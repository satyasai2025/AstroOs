import { Metadata } from "next";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "Knowledge Base",
  description: "AstroOS Knowledge Base — Classical literature, slokas, and rule references",
};

export default function KnowledgeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell sectionColor="--section-research">{children}</AppShell>;
}
