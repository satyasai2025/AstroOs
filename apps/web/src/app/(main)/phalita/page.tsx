import { Metadata } from "next";
import { PhalitaCanonicalDashboard } from "@/components/phalita/PhalitaCanonicalDashboard";

export const metadata: Metadata = {
  title: "Phalita MoE Consultation | AstroOS",
  description: "Canonical 3-Chart Synthesis (D1 Vishamabhava + Sudarshana Chakra + D10 Vimshopaka + VPC Solar Return) with Typed MoE Uncertainty.",
};

export default function PhalitaPage() {
  return <PhalitaCanonicalDashboard />;
}
