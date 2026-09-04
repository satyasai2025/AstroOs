import { Metadata } from "next";
import { PredictionValidationWorkbench } from "@/components/predictions/PredictionValidationWorkbench";

export const metadata: Metadata = {
  title: "Prediction Validation Workbench | AstroOS",
  description: "Deterministic ground-truth astrological prediction validation, frozen evidence snapshots, and empirical backtesting.",
};

export default function PredictionValidationPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <PredictionValidationWorkbench />
    </div>
  );
}
