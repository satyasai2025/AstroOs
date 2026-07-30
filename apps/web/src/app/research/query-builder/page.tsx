"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Select } from "@/components/ui";

interface ConditionRow {
  id: string;
  field: string;
  operator: string;
  value: string;
}

const FIELD_OPTIONS = [
  { value: "planet_house", label: "Planet in House" },
  { value: "planet_sign", label: "Planet in Sign" },
  { value: "dasha_lord", label: "Dasha Lord" },
  { value: "yoga_present", label: "Yoga Present" },
  { value: "aspect", label: "Aspect Between Planets" },
];

const OPERATOR_OPTIONS = [
  { value: "equals", label: "Equals" },
  { value: "not_equals", label: "Not Equals" },
  { value: "contains", label: "Contains" },
];

const DATASET_OPTIONS = [
  { value: "marriage", label: "Marriage Timing Dataset" },
  { value: "career", label: "Career Success Cohort" },
  { value: "sade-sati", label: "Sade Sati Life Events" },
];

const SAVED_QUERIES = ["Jupiter in Kendra + Marriage within 2y", "10th Lord strong + Career Promotion", "Sade Sati + Health Event"];

let nextId = 1;

export default function QueryBuilderPage() {
  const [dataset, setDataset] = useState(DATASET_OPTIONS[0].value);
  const [conditions, setConditions] = useState<ConditionRow[]>([
    { id: "c0", field: "planet_house", operator: "equals", value: "" },
  ]);
  const [ran, setRan] = useState(false);

  const addCondition = () =>
    setConditions((prev) => [...prev, { id: `c${++nextId}`, field: "planet_house", operator: "equals", value: "" }]);

  const updateCondition = (id: string, patch: Partial<ConditionRow>) =>
    setConditions((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));

  const removeCondition = (id: string) => setConditions((prev) => prev.filter((c) => c.id !== id));

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Query Builder
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Vedic Astrology Research — build multi-condition queries across a dataset.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary">Save Query</Button>
          <Button variant="ghost" onClick={() => { setConditions([{ id: "c0", field: "planet_house", operator: "equals", value: "" }]); setRan(false); }}>
            Reset
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_260px]">
        <div className="space-y-4">
          <Card>
            <div className="mb-3 max-w-xs">
              <Select label="Dataset" options={DATASET_OPTIONS} value={dataset} onChange={setDataset} />
            </div>

            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
              Conditions
            </h4>
            <div className="space-y-2">
              {conditions.map((c) => (
                <div key={c.id} className="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end">
                  <Select
                    label="Field"
                    options={FIELD_OPTIONS}
                    value={c.field}
                    onChange={(v) => updateCondition(c.id, { field: v })}
                  />
                  <Select
                    label="Operator"
                    options={OPERATOR_OPTIONS}
                    value={c.operator}
                    onChange={(v) => updateCondition(c.id, { operator: v })}
                  />
                  <div>
                    <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", fontWeight: "var(--weight-medium)", marginBottom: 6 }}>
                      Value
                    </div>
                    <input
                      className="field-input"
                      value={c.value}
                      onChange={(e) => updateCondition(c.id, { value: e.target.value })}
                      placeholder="e.g. Jupiter, House 5"
                    />
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => removeCondition(c.id)} disabled={conditions.length === 1}>
                    Remove
                  </Button>
                </div>
              ))}
            </div>
            <Button variant="secondary" size="sm" onClick={addCondition} style={{ marginTop: 12 }}>
              + Add Condition
            </Button>

            <div className="mt-4 flex gap-2">
              <Button variant="primary" onClick={() => setRan(true)}>
                Run Query
              </Button>
              <Button variant="ghost">Export CSV</Button>
            </div>
          </Card>

          {ran && (
            <Card>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
                Query Results Summary
              </h4>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                <Badge tone="cyan">2,341</Badge>{" "}
                <span className="ml-2">matched charts out of {DATASET_OPTIONS.find((d) => d.value === dataset)?.label}</span>
              </p>
              <p className="mt-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
                Illustrative result count — this query engine isn't wired to a real chart corpus yet.
              </p>
            </Card>
          )}
        </div>

        <Card padding="0">
          <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "var(--text-xs)", fontWeight: "var(--weight-semibold)", color: "var(--text-tertiary)", textTransform: "uppercase" }}>
              Saved Queries
            </span>
          </div>
          <div>
            {SAVED_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                className="block w-full px-4 py-2.5 text-left text-sm transition hover:opacity-80"
                style={{ color: "var(--text-secondary)", borderBottom: "1px solid var(--border-subtle)" }}
              >
                {q}
              </button>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
