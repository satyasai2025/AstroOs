import { Metadata } from "next";
import ResearchWorkspace from "@/components/layout/ResearchWorkspace";

export const metadata: Metadata = {
  title: "Reverse Pattern Search",
  description: "Search for charts matching specific yogas, planetary combinations, or aspects",
};

export default function ReverseSearchPage() {
  return <ResearchWorkspace />;
}
