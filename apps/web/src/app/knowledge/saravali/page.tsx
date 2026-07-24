import { Metadata } from "next";
import ResearchWorkspace from "@/components/layout/ResearchWorkspace";

export const metadata: Metadata = {
  title: "Saravali — Kalyanavarma",
  description: "Saravali of Kalyanavarma sloka browser with AI citations and confidence scores",
};

export default function SaravaliPage() {
  return <ResearchWorkspace />;
}
