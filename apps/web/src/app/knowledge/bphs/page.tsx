import { Metadata } from "next";
import { Card } from "@/components/ui";

export const metadata: Metadata = {
  title: "BPHS — Brihat Parashara Hora Shastra",
  description: "Brihat Parashara Hora Shastra sloka browser with AI citations and confidence scores",
};

export default function BPHSPage() {
  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
        BPHS — Brihat Parashara Hora Shastra
      </h1>
      <p className="mb-6 text-sm" style={{ color: "var(--text-secondary)" }}>
        Sloka browser with AI citations and confidence scores.
      </p>
      <Card style={{ padding: "2rem", textAlign: "center" }}>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          The BPHS sloka browser isn&apos;t built yet — this page is a placeholder until it is.
        </p>
      </Card>
    </div>
  );
}
