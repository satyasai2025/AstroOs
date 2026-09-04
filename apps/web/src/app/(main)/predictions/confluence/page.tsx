import { Metadata } from "next";
import { PredictionConfluenceWorkspace } from "@/components/predictions/PredictionConfluenceWorkspace";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Multi-System Prediction Synthesis | AstroOS",
  description: "Unified cross-system prediction confluence engine synthesizing Dasha, KP CSL, SBC Vedha Rays, Classical Yogas, and P7 Empirical Backtests.",
};

export default function PredictionConfluencePage() {
  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <PredictionConfluenceWorkspace />
    </div>
  );
}
