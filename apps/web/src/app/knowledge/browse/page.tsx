"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Badge, Card, Select } from "@/components/ui";
import { KARAKATVA_GRAHAS, useKarakatvaSearch } from "@/lib/karakatva";

type EntityType = "planets" | "signs" | "houses" | "nakshatras" | "yogas" | "karakatvas" | "texts" | "rules";

const ENTITY_TYPES: { value: EntityType; label: string }[] = [
  { value: "planets", label: "Planets" },
  { value: "signs", label: "Signs (Rashi)" },
  { value: "houses", label: "Houses (Bhava)" },
  { value: "nakshatras", label: "Nakshatras" },
  { value: "yogas", label: "Yogas" },
  { value: "karakatvas", label: "Karakatvas" },
  { value: "texts", label: "Classical Texts" },
  { value: "rules", label: "Rules" },
];

/**
 * Illustrative sample rows for every entity type except Karakatvas, which
 * queries the real /api/v1/karakatva endpoint (same data source as the
 * standalone /karakatva page) — this app doesn't have real reference-data
 * endpoints for the other categories yet.
 */
const PLACEHOLDER_ROWS: Record<Exclude<EntityType, "karakatvas">, { title: string; desc: string }[]> = {
  planets: [
    { title: "Sun (Surya)", desc: "Karaka for soul, father, authority. Exalted in Mesha, debilitated in Tula." },
    { title: "Moon (Chandra)", desc: "Karaka for mind, mother, emotions. Exalted in Vrishabha, debilitated in Vrishchika." },
  ],
  signs: [
    { title: "Mesha (Aries)", desc: "Fire sign, cardinal (Chara), ruled by Mars." },
    { title: "Vrishabha (Taurus)", desc: "Earth sign, fixed (Sthira), ruled by Venus." },
  ],
  houses: [
    { title: "1st House — Tanu Bhava", desc: "Self, body, personality." },
    { title: "7th House — Kalatra Bhava", desc: "Marriage, partnerships." },
  ],
  nakshatras: [
    { title: "Ashwini", desc: "Ruled by Ketu, deity Ashwini Kumaras, symbol horse's head." },
    { title: "Bharani", desc: "Ruled by Venus, deity Yama, symbol yoni." },
  ],
  yogas: [
    { title: "Gaja Kesari Yoga", desc: "Jupiter in Kendra from Moon." },
    { title: "Raj Yoga (Multiple)", desc: "Combination of Kendra & Trikona lords." },
  ],
  texts: [
    { title: "Brihat Parashara Hora Shastra", desc: "Foundational classical text attributed to Sage Parashara." },
    { title: "Saravali", desc: "Classical text by Kalyana Varma covering yogas and predictions." },
  ],
  rules: [
    { title: "10th Lord in Kendra — Career Strength", desc: "Classical rule evaluated against real charts in the Rules tab." },
    { title: "Sade Sati — Saturn transit affliction", desc: "Classical rule evaluated against real charts in the Rules tab." },
  ],
};

function BrowseContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const type = (searchParams.get("type") as EntityType) ?? "planets";
  const [graha, setGraha] = useState("sun");

  const karakatvaQuery = useKarakatvaSearch({ graha });

  const setType = (v: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("type", v);
    router.push(`/knowledge/browse?${params.toString()}`);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Knowledge Browse
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Browse Vedic astrology reference entities by category.
        </p>
      </div>

      <div className="mb-4 max-w-xs">
        <Select label="Entity Type" options={ENTITY_TYPES} value={type} onChange={setType} />
      </div>

      {type === "karakatvas" ? (
        <div className="space-y-3">
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Real data from the Karakatva database (450 seeded entries) — same source as{" "}
            <a href="/karakatva" style={{ color: "var(--cyan-400)" }}>
              /karakatva
            </a>
            .
          </p>
          <div className="max-w-xs">
            <Select
              label="Filter by Graha"
              options={KARAKATVA_GRAHAS.map((g) => ({ value: g, label: g }))}
              value={graha}
              onChange={setGraha}
            />
          </div>
          {karakatvaQuery.isLoading && (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              Loading…
            </p>
          )}
          {karakatvaQuery.data?.karakatvas.slice(0, 20).map((item) => (
            <Card key={item.id}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                  {item.subject}
                </h3>
                {item.graha && <Badge tone="cyan">{item.graha}</Badge>}
              </div>
              {item.description && (
                <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                  {item.description}
                </p>
              )}
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Illustrative sample entries — a real reference-data endpoint for this category doesn't
            exist yet.
          </p>
          {PLACEHOLDER_ROWS[type]?.map((row) => (
            <Card key={row.title}>
              <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                {row.title}
              </h3>
              <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                {row.desc}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function KnowledgeBrowsePage() {
  return (
    <Suspense fallback={null}>
      <BrowseContent />
    </Suspense>
  );
}
