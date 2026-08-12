"use client";

import { useState } from "react";
import {
  BHAVA_PARAMS,
  GRAHA_PARAMS,
  NAKSHATRA_PARAMS,
  RASHI_PARAMS,
  REF_UNAVAILABLE,
} from "@/lib/astroStructural";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import { resolveStructuralColumns, type PlanetContext, type StructuralColumn } from "./context";

const COLS: { key: StructuralColumn["key"]; title: string; label: string }[] = [
  { key: "rashi", title: "Rashi", label: "Rashi" },
  { key: "graha", title: "Graha", label: "Graha" },
  { key: "bhava", title: "Bhava", label: "Bhava" },
  { key: "nakshatra", title: "Nakshatra + Pada", label: "Nakshatra" },
];

const SUTRA_LABELS: string[] = RASHI_PARAMS.map((_, i) => {
  const parts = [RASHI_PARAMS[i], GRAHA_PARAMS[i], BHAVA_PARAMS[i], NAKSHATRA_PARAMS[i]];
  return `${parts[0]} · ${parts[1]} · ${parts[2]} · ${parts[3]}`;
});

function Cell({ value }: { value: string }) {
  const unavailable = value === REF_UNAVAILABLE;
  return (
    <td className="px-3 py-2 align-top text-sm" style={{ color: unavailable ? "var(--text-muted)" : "var(--text-primary)" }}>
      {unavailable ? (
        <span className="italic" style={{ color: "var(--text-muted)" }}>Reference unavailable</span>
      ) : (
        value
      )}
    </td>
  );
}

function StructuralRelation({ columns, sutra }: { columns: StructuralColumn[]; sutra: number }) {
  const steps = columns.map((c) => ({ entity: c.entity, value: c.values[sutra] ?? REF_UNAVAILABLE }));
  return (
    <div className="rounded-lg border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Structural Relation
      </p>
      <div className="space-y-1.5 text-sm">
        {steps.map((s, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="min-w-[9rem] font-medium capitalize" style={{ color: "var(--text-muted)" }}>{s.entity}</span>
            <span style={{ color: s.value === REF_UNAVAILABLE ? "var(--text-muted)" : "var(--text-primary)" }}>
              {s.value === REF_UNAVAILABLE ? "Reference unavailable" : s.value}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-3 border-t pt-2 text-xs" style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>
        The Rashi establishes the raw attribute; {columns[1]?.entity} expresses it through its own nature;
        the {columns[2]?.entity} placement directs where it acts; and
        {columns[3]?.entity} refines its purpose. All four cells are shown verbatim from the structural
        reference — no inferred values.
      </p>
    </div>
  );
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

export function StructureTab({ ctx }: Props) {
  const [view, setView] = useState<"map" | "matrix">("map");
  const [expanded, setExpanded] = useState<number | null>(null);
  const columns = resolveStructuralColumns(ctx);

  if (columns.length === 0) {
    return <p className="text-sm" style={{ color: "var(--text-muted)" }}>No position data for {ctx.planet} in this chart.</p>;
  }

  const toggle = (i: number) => setExpanded((cur) => (cur === i ? null : i));

  return (
    <div className="space-y-4">
      {/* View toggle */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {(["map", "matrix"] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => setView(v)}
              className="rounded-lg px-3 py-1.5 text-xs font-medium capitalize"
              style={{
                backgroundColor: view === v ? "var(--accent)" : "transparent",
                color: view === v ? "var(--accent-text)" : "var(--text-secondary)",
              }}
            >
              {v === "map" ? "Structural Map" : "Matrix"}
            </button>
          ))}
        </div>
        <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          Structural identity — distinct from quantitative strength
        </span>
      </div>

      {view === "map" ? (
        <div className="overflow-x-auto rounded-2xl border" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <table className="w-full border-collapse text-left">
            <thead>
              <tr
                className="border-b text-xs uppercase tracking-wide"
                style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
              >
                <th className="px-3 py-2">Sutra</th>
                {columns.map((c) => (
                  <th key={c.key} className="px-3 py-2 capitalize">{COLS.find((x) => x.key === c.key)?.title}: {c.entity}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {columns[0].values.map((_v, i) => {
                const open = expanded === i;
                return (
                  <RowBlock key={i} i={i} suffixLabel={SUTRA_LABELS[i]} columns={columns} open={open} onTitleClick={() => toggle(i)} />
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <MatrixView columns={columns} />
      )}
    </div>
  );
}

/** A sutra row plus its (optional) expanded Structural Relation row. */
function RowBlock({
  i,
  suffixLabel,
  columns,
  open,
  onTitleClick,
}: {
  i: number;
  suffixLabel: string;
  columns: StructuralColumn[];
  open: boolean;
  onTitleClick: () => void;
}) {
  const unavailableRow = columns.every((c) => (c.values[i] ?? REF_UNAVAILABLE) === REF_UNAVAILABLE);
  return (
    <>
      <tr
        className="cursor-pointer border-b align-top"
        style={{ borderColor: "var(--border-primary)", backgroundColor: open ? "var(--bg-input)" : "transparent" }}
        onClick={onTitleClick}
        title={open ? "Collapse" : "Expand structural relation"}
      >
        <td className="px-3 py-3">
          <button type="button" className="flex items-center gap-2 text-left text-xs font-semibold uppercase" style={{ color: "var(--accent)" }}>
            <span style={{ display: "inline-block", transform: open ? "rotate(90deg)" : "none", transition: "transform .15s ease" }}>▸</span>
            <span className="normal-case">{unavailableRow ? suffixLabel : `Sutra ${i + 1}`}</span>
          </button>
          <span className="mt-1 block text-[10px] normal-case" style={{ color: "var(--text-muted)" }}>{suffixLabel}</span>
        </td>
        {columns.map((c) => (
          <Cell key={c.key} value={c.values[i] ?? REF_UNAVAILABLE} />
        ))}
      </tr>
      {open && (
        <tr className="border-b" style={{ borderColor: "var(--border-primary)" }}>
          <td colSpan={columns.length + 1} className="p-3">
            <StructuralRelation columns={columns} sutra={i} />
          </td>
        </tr>
      )}
    </>
  );
}

/** Structural matrix — 4 columns × 13 rows for quick inspection. */
function MatrixView({ columns }: { columns: StructuralColumn[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      <table className="w-full border-collapse text-left text-xs">
        <thead>
          <tr className="border-b uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
            <th className="px-3 py-2">Sutra</th>
            {columns.map((c) => (
              <th key={c.key} className="px-3 py-2 capitalize">{c.entity}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {columns[0].values.map((_v, i) => (
            <tr key={i} className="border-b align-top" style={{ borderColor: "var(--border-primary)" }}>
              <td className="px-3 py-2 font-medium" style={{ color: "var(--text-muted)" }}>S{i + 1}</td>
              {columns.map((c) => {
                const v = c.values[i] ?? REF_UNAVAILABLE;
                const un = v === REF_UNAVAILABLE;
                return (
                  <td key={c.key} className="px-3 py-2" style={{ color: un ? "var(--text-muted)" : "var(--text-primary)" }}>
                    {un ? "—" : v}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}