import { RectificationStudio } from "@/components/research/RectificationStudio";

export const metadata = {
  title: "Inverse Natal Profiling & Chart Rectification | AstroOS Research",
  description:
    "Bayesian inverse chart reconstruction and birth time rectification from historical life events using multi-dasha activations, double transits, and Navamsha D9 lagna harmony.",
};

export default function RectificationPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <RectificationStudio />
    </div>
  );
}
