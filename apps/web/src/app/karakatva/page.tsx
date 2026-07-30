"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ApiError } from "@/lib/api";
import { KARAKATVA_GRAHAS, useKarakatvaSearch, type Karakatva } from "@/lib/karakatva";
import { Badge, Card, Input, Select } from "@/components/ui";

const GRAHA_LABELS: Record<string, string> = {
  sun: "Sun (Surya)",
  moon: "Moon (Chandra)",
  mars: "Mars (Mangala)",
  mercury: "Mercury (Budha)",
  jupiter: "Jupiter (Guru)",
  venus: "Venus (Shukra)",
  saturn: "Saturn (Shani)",
  rahu: "Rahu",
  ketu: "Ketu",
};

function grahaLabel(graha: string | null): string {
  if (!graha) return "";
  return GRAHA_LABELS[graha] ?? graha;
}

function KarakatvaCard({ item }: { item: Karakatva }) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
          {item.subject}
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {item.graha && <Badge tone="cyan">{grahaLabel(item.graha)}</Badge>}
          {item.house_number != null && <Badge tone="neutral">House {item.house_number}</Badge>}
          {item.sign_id != null && <Badge tone="neutral">Sign #{item.sign_id}</Badge>}
        </div>
      </div>

      {item.description && (
        <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>
          {item.description}
        </p>
      )}

      {item.tradition && (
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          Source tradition: {item.tradition}
        </p>
      )}
    </Card>
  );
}

export default function KarakatvaExplorerPage() {
  const [subjectInput, setSubjectInput] = useState("");
  const [debouncedSubject, setDebouncedSubject] = useState("");
  const [graha, setGraha] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSubject(subjectInput), 400);
    return () => clearTimeout(timer);
  }, [subjectInput]);

  const { data, isLoading, isFetching, isError, error } = useKarakatvaSearch({
    subject: debouncedSubject,
    graha,
  });

  const errorMessage =
    error instanceof ApiError
      ? error.detail
      : error
        ? "Could not search the karakatva catalogue."
        : null;

  const hasQuery = debouncedSubject.trim().length >= 2 || !!graha;
  const results = data?.karakatvas ?? [];

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Karakatva Explorer
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Search what each planet, house, and nakshatra classically signifies —
          e.g. Mars → Career, Military, Surgery, Blood — sourced from Brihat
          Parashara Hora Shastra (BPHS). This is a curated catalogue of a few
          hundred entries, not an exhaustive database.
        </p>
      </div>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Input
            label="Search signification"
            value={subjectInput}
            onChange={setSubjectInput}
            placeholder="e.g. career, blood, marriage, surgery..."
          />
        </div>

        <div className="sm:w-48">
          <Select
            label="Planet (graha)"
            value={graha}
            onChange={setGraha}
            placeholder="All planets"
            options={[{ value: "", label: "All planets" }, ...KARAKATVA_GRAHAS.map((g) => ({ value: g, label: grahaLabel(g) }))]}
          />
        </div>
      </div>

      {!hasQuery && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Type at least 2 characters, or pick a planet, to search the karakatva catalogue.
          </p>
        </Card>
      )}

      {hasQuery && (isLoading || isFetching) && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Searching…</p>
        </Card>
      )}

      {hasQuery && isError && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--danger-400)" }} role="alert">
            {errorMessage}
          </p>
        </Card>
      )}

      {hasQuery && !isLoading && !isFetching && !isError && results.length === 0 && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            No matching significations found. This catalogue currently holds a
            few hundred classical entries (grahas, houses, nakshatras) sourced
            from BPHS — if searches keep coming back empty even for common
            terms like &quot;career&quot; or &quot;marriage&quot;, the one-time
            knowledge base seed script (<code>python -m apps.api.scripts.seed_knowledge</code>)
            may not have been run against this database yet.
          </p>
        </Card>
      )}

      {hasQuery && !isLoading && !isFetching && !isError && results.length > 0 && (
        <div>
          <p className="mb-3 text-xs" style={{ color: "var(--text-muted)" }}>
            {data?.total ?? results.length} result{(data?.total ?? results.length) === 1 ? "" : "s"}.
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {results.map((item) => (
              <KarakatvaCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}
