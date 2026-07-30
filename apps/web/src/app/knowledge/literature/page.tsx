import { Metadata } from "next";
import { Card } from "@/components/ui";

export const metadata: Metadata = {
  title: "Classical Literature",
  description: "AstroOS Classical Literature — BPHS, Saravali, and other Jyotish texts",
};

export default function LiteraturePage() {
  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
        Classical Literature
      </h1>
      <p className="mb-6 text-sm" style={{ color: "var(--text-secondary)" }}>
        BPHS, Saravali, and other Jyotish texts.
      </p>
      <Card style={{ padding: "2rem", textAlign: "center" }}>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          The classical literature browser isn&apos;t built yet — this page is a placeholder until it is.
        </p>
      </Card>
    </div>
  );
}
