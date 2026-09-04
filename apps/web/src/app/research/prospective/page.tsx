import { ProspectiveValidationStudio } from "@/components/research/ProspectiveValidationStudio";

export const metadata = {
  title: "Prospective Research Validation & Rule Lifecycle | AstroOS Research",
  description:
    "Forward-only blind prospective cohort validation studio featuring immutable pre-registration and statistical rule lifecycle management.",
};

export default function ProspectiveValidationPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <ProspectiveValidationStudio />
    </div>
  );
}
