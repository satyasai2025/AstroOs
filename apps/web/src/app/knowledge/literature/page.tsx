import { Metadata } from "next";
import ResearchWorkspace from "@/components/layout/ResearchWorkspace";

export const metadata: Metadata = {
  title: "Classical Literature",
  description: "AstroOS Classical Literature — BPHS, Saravali, and other Jyotish texts",
};

export default function LiteraturePage() {
  return <ResearchWorkspace />;
}
