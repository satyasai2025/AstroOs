import type { SelectOption } from "@/components/ui";

export const EVENT_OPTIONS: SelectOption[] = [
  { value: "", label: "All event types" },
  { value: "Marriage", label: "Marriage" },
  { value: "Divorce", label: "Divorce" },
  { value: "Promotion", label: "Promotion" },
  { value: "Job Change", label: "Job Change" },
  { value: "Accident", label: "Accident" },
  { value: "Surgery", label: "Surgery" },
  { value: "Child Birth", label: "Child Birth" },
  { value: "Education", label: "Education" },
  { value: "Business", label: "Business" },
  { value: "Finance", label: "Finance" },
  { value: "Foreign Travel", label: "Foreign Travel" },
  { value: "Property", label: "Property" },
  { value: "Health", label: "Health" },
  { value: "Spiritual", label: "Spiritual" },
  { value: "Litigation", label: "Litigation" },
  { value: "Awards", label: "Awards" },
  { value: "Political", label: "Political" },
  { value: "Vehicle", label: "Vehicle" },
  { value: "Death of Parent", label: "Death of Parent" },
  { value: "Death of Spouse", label: "Death of Spouse" },
  { value: "Hospitalization", label: "Hospitalization" },
  { value: "Other", label: "Other" },
];

export const CHART_OPTIONS: SelectOption[] = [
  { value: "", label: "All Charts" },
  { value: "D1", label: "D1 — Rashi" },
  { value: "D9", label: "D9 — Navamsa" },
  { value: "D10", label: "D10 — Dashamsa" },
  { value: "D60", label: "D60 — Shashtiamsa" },
];

export const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

export type LiftBucket = "Very High" | "High" | "Medium" | "Low";

export function liftBucket(lift: number): LiftBucket {
  if (lift >= 2.0) return "Very High";
  if (lift >= 1.5) return "High";
  if (lift >= 1.0) return "Medium";
  return "Low";
}

export const LIFT_BUCKET_COLORS: Record<LiftBucket, string> = {
  "Very High": "var(--success-400)",
  High: "var(--gold-300)",
  Medium: "var(--cyan-400)",
  Low: "var(--danger-400)",
};
