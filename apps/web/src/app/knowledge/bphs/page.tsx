import { Metadata } from "next";
import ResearchWorkspace from "@/components/layout/ResearchWorkspace";

export const metadata: Metadata = {
  title: "BPHS — Brihat Parashara Hora Shastra",
  description: "Brihat Parashara Hora Shastra sloka browser with AI citations and confidence scores",
};

export default function BPHSPage() {
  return <ResearchWorkspace />;
}
