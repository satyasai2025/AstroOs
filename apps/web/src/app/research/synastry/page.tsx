import { SynastryStudio } from "@/components/research/SynastryStudio";

export const metadata = {
  title: "Synastry & Inter-Chart Compatibility Studio | AstroOS Research",
  description:
    "Evaluate 36-Guna Ashta-Kuta with classical cancellations (BPHS/Muhurta Chintamani), inter-chart angular aspects, cross-house overlays, and joint multi-dasha confluence timing.",
};

export default function SynastryPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <SynastryStudio />
    </div>
  );
}
