"use client";

import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Select } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { QueryCondition, ResearchCaseSummary } from "@/lib/types";

const PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"];

// Real, curated field templates over the canonical Fact vocabulary
// FactBuilder produces (apps/api/services/fact_builder.py) — "{planet}" is
// substituted from the Planet selector below. This is deliberately a
// curated subset (not every one of the ~500 dotted fact keys per chart)
// so the UI stays usable; power users can still type a raw field key via
// "Custom field" for anything not covered here.
const FIELD_TEMPLATES = [
  { value: "planet.{p}.retrograde", label: "Planet Retrograde", needsPlanet: true, valueHint: "true / false" },
  { value: "planet.{p}.combust", label: "Planet Combust", needsPlanet: true, valueHint: "true / false" },
  { value: "planet.{p}.house", label: "Planet in House", needsPlanet: true, valueHint: "1-12" },
  { value: "planet.{p}.rashi", label: "Planet in Rashi", needsPlanet: true, valueHint: "e.g. leo" },
  { value: "planet.{p}.exalted", label: "Planet Exalted", needsPlanet: true, valueHint: "true / false" },
  { value: "planet.{p}.debilitated", label: "Planet Debilitated", needsPlanet: true, valueHint: "true / false" },
  { value: "maraka.lord.{p}", label: "Planet is Maraka Lord", needsPlanet: true, valueHint: "true / false" },
  { value: "badhaka.lord", label: "Badhakesh (Badhaka Lord)", needsPlanet: false, valueHint: "e.g. saturn" },
  { value: "dasha.current_lord", label: "Current Mahadasha Lord", needsPlanet: false, valueHint: "e.g. saturn" },
  { value: "dasha.antardasha_lord", label: "Current Antardasha Lord", needsPlanet: false, valueHint: "e.g. saturn" },
  { value: "functional.{p}.lordship", label: "Functional Lordship", needsPlanet: true, valueHint: "benefic / malefic / neutral" },
  { value: "functional.{p}.yogakaraka", label: "Is Yogakaraka", needsPlanet: true, valueHint: "true / false" },
  { value: "yoga.{p}", label: "Custom field (type full key below)", needsPlanet: false, valueHint: "" },
] as const;

const OPERATOR_OPTIONS = [
  { value: "equals", label: "Equals" },
  { value: "not_equals", label: "Not Equals" },
  { value: "contains", label: "Contains" },
];

interface ConditionRow {
  id: string;
  templateIndex: number;
  planet: string;
  customField: string;
  operator: "equals" | "not_equals" | "contains";
  value: string;
}

let nextId = 1;

function newRow(): ConditionRow {
  return { id: `c${nextId++}`, templateIndex: 0, planet: "saturn", customField: "", operator: "equals", value: "true" };
}

function resolveField(row: ConditionRow): string {
  const template = FIELD_TEMPLATES[row.templateIndex];
  if (template.label.startsWith("Custom")) return row.customField.trim();
  return template.needsPlanet ? template.value.replace("{p}", row.planet) : template.value;
}

export default function QueryBuilderPage() {
  const [conditions, setConditions] = useState<ConditionRow[]>([newRow()]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ total_scanned: number; total_matched: number; matches: ResearchCaseSummary[] } | null>(null);

  const addCondition = () => setConditions((prev) => [...prev, newRow()]);
  const updateCondition = (id: string, patch: Partial<ConditionRow>) =>
    setConditions((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  const removeCondition = (id: string) => setConditions((prev) => (prev.length > 1 ? prev.filter((c) => c.id !== id) : prev));

  const runQuery = async () => {
    setRunning(true);
    setError(null);
    try {
      const payload: { conditions: QueryCondition[] } = {
        conditions: conditions
          .map((c) => ({ field: resolveField(c), operator: c.operator, value: c.value.trim() }))
          .filter((c) => c.field && c.value),
      };
      if (payload.conditions.length === 0) {
        setError("Add at least one condition with a field and value.");
        return;
      }
      const res = await researchCasesApi.queryCases(payload);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Query Builder
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Search real imported research cases by canonical chart facts (Maraka, Badhaka, Functional
            Lordship, Retrograde, Combust, Dasha, and more).
          </p>
        </div>
        <Button
          variant="ghost"
          onClick={() => {
            setConditions([newRow()]);
            setResult(null);
            setError(null);
          }}
        >
          Reset
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <Card>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
            Conditions (all must match — AND)
          </h4>
          <div className="space-y-3">
            {conditions.map((c) => {
              const template = FIELD_TEMPLATES[c.templateIndex];
              const isCustom = template.label.startsWith("Custom");
              return (
                <div key={c.id} className="grid grid-cols-1 gap-2 sm:grid-cols-[1.4fr_0.8fr_1fr_1fr_auto] sm:items-end">
                  <Select
                    label="Field"
                    options={FIELD_TEMPLATES.map((t, i) => ({ value: String(i), label: t.label }))}
                    value={String(c.templateIndex)}
                    onChange={(v) => updateCondition(c.id, { templateIndex: Number(v) })}
                  />
                  {template.needsPlanet ? (
                    <Select
                      label="Planet"
                      options={PLANETS.map((p) => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) }))}
                      value={c.planet}
                      onChange={(v) => updateCondition(c.id, { planet: v })}
                    />
                  ) : isCustom ? (
                    <div>
                      <div className="text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                        Full field key
                      </div>
                      <input
                        className="field-input"
                        value={c.customField}
                        onChange={(e) => updateCondition(c.id, { customField: e.target.value })}
                        placeholder="e.g. planet.rahu.house"
                      />
                    </div>
                  ) : (
                    <div />
                  )}
                  <Select
                    label="Operator"
                    options={OPERATOR_OPTIONS}
                    value={c.operator}
                    onChange={(v) => updateCondition(c.id, { operator: v as ConditionRow["operator"] })}
                  />
                  <div>
                    <div className="text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>
                      Value {template.valueHint && <span className="text-slate-400">({template.valueHint})</span>}
                    </div>
                    <input
                      className="field-input"
                      value={c.value}
                      onChange={(e) => updateCondition(c.id, { value: e.target.value })}
                      placeholder="e.g. true, 1, saturn"
                    />
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => removeCondition(c.id)} disabled={conditions.length === 1}>
                    Remove
                  </Button>
                </div>
              );
            })}
          </div>
          <Button variant="secondary" size="sm" onClick={addCondition} style={{ marginTop: 12 }}>
            + Add Condition
          </Button>

          <div className="mt-4 flex gap-2">
            <Button variant="primary" onClick={runQuery} disabled={running}>
              {running ? "Running…" : "Run Query"}
            </Button>
          </div>

          {error && <p className="mt-3 text-sm text-rose-500">{error}</p>}
        </Card>

        {result && (
          <Card>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
              Query Results
            </h4>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              <Badge tone="cyan">{result.total_matched.toLocaleString()}</Badge>{" "}
              <span className="ml-2">
                matched out of {result.total_scanned.toLocaleString()} scanned real research cases
              </span>
            </p>
            {result.total_matched > 0 && (
              <div className="mt-3 flex flex-col gap-1.5 max-h-80 overflow-y-auto">
                {result.matches.map((m) => (
                  <Link
                    key={m.research_case_id}
                    href={`/research/cases/${encodeURIComponent(m.research_case_id)}`}
                    className="flex items-center justify-between px-3 py-2 rounded-md border border-slate-200 dark:border-slate-800 hover:border-cyan-500 text-sm"
                  >
                    <span className="text-slate-900 dark:text-slate-100 font-medium">
                      {m.person_name || m.research_case_id}
                    </span>
                    <span className="text-slate-400 text-xs font-mono">{m.dob}</span>
                  </Link>
                ))}
                {result.total_matched > result.matches.length && (
                  <p className="text-xs text-slate-400 mt-1">
                    Showing first {result.matches.length} of {result.total_matched} matches.
                  </p>
                )}
              </div>
            )}
          </Card>
        )}
      </div>
    </AppShell>
  );
}
