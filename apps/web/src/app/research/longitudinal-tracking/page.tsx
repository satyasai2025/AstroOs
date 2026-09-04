import { Metadata } from "next";
import { ResearchLongitudinalTrackingStudio } from "@/components/research/ResearchLongitudinalTrackingStudio";

export const metadata: Metadata = {
  title: "Longitudinal Outcome Tracking | AstroOS Research",
  description:
    "Priority 27: Continuous real-world prospective observation recording, time-series calibration, & dual-drift diagnosis.",
};

export default function ResearchLongitudinalTrackingPage() {
  return <ResearchLongitudinalTrackingStudio />;
}
