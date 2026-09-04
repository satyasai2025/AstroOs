import { Metadata } from "next";
import { ShastricConsultationDashboard } from "@/components/consultation/ShastricConsultationDashboard";

export const metadata: Metadata = {
  title: "Shastric Life Consultation | AstroOS",
  description: "Deterministic Layer 3 Supervisory Adaptive Decision Engine, Bhrigu Bindu, and Sarvato-Bhadra Chakra life consultation scanner.",
};

export default function ConsultationPage() {
  return <ShastricConsultationDashboard />;
}
