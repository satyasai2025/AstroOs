"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Badge, Button, Card, Table, type TableColumn } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type {
  ResearchCaseBatchImport,
  ResearchCaseBatchValidation,
  ResearchCaseImportResponse,
  ResearchCaseSummary,
  ValidationIssue,
} from "@/lib/types";

function titleCase(value: string): string {
  return value
    .replace(/_/g, " ")
    .split(" ")
    .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1) : w))
    .join(" ");
}

/** A small, valid sample payload so the page can be tested without a file. */
const SAMPLE_PAYLOAD: ResearchCaseBatchImport = {
  generate_ids: true,
  cases: [
    {
      id: "RC-1986-002",
      person: {
        name: "Sample Subject",
        gender: "Female",
        dob: "1986-06-15",
        tob: "10:30",
        place: "Delhi",
        latitude: 28.6139,
        longitude: 77.209,
        timezone: "Asia/Kolkata",
        source: "Interview",
      },
      ayanamsa: "lahiri",
      house_system: "P",
      divisional_charts: ["D1", "D9", "D10", "D60"],
      life_events: [
        { id: "EV-1", type: "Marriage", event_date: "2012-02-14" },
        { id: "EV-2", type: "Promotion", event_date: "2018-05-01" },
        { id: "EV-3", type: "Child Birth", event_date: "2015-08-10" },
      ],
    },
  ],
};

export default function ResearchImportPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [payload, setPayload] = useState<ResearchCaseBatchImport | null>(null);
  const [validation, setValidation] = useState<ResearchCaseBatchValidation | null>(null);
  const [importResult, setImportResult] = useState<ResearchCaseImportResponse | null>(null);
  const [cases, setCases] = useState<ResearchCaseSummary[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCases = useCallback(async () => {
    try {
      const data = await researchCasesApi.list();
      setCases(data.cases);
    } catch {
      // Non-fatal — the list is auxiliary to the import flow.
    }
  }, []);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  const runValidation = useCallback(async (p: ResearchCaseBatchImport) => {
    setValidation(null);
    setError(null);
    try {
      const result = await researchCasesApi.validate(p);
      setValidation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed.");
    }
  }, []);

  const handleFile = useCallback(
    async (file: File) => {
      setFileName(file.name);
      setImportResult(null);
      setError(null);
      try {
        const text = await file.text();
        const parsed = JSON.parse(text) as ResearchCaseBatchImport;
        if (!parsed || !Array.isArray(parsed.cases)) {
          throw new Error("Invalid payload: expected an object with a `cases` array.");
        }
        setPayload(parsed);
        void runValidation(parsed);
      } catch (err) {
        setPayload(null);
        setError(err instanceof Error ? err.message : "Could not parse JSON file.");
      }
    },
    [runValidation],
  );

  const handleImport = useCallback(async () => {
    if (!payload) return;
    setImporting(true);
    setImportResult(null);
    setError(null);
    try {
      const result = await researchCasesApi.importCases(payload);
      setImportResult(result);
      await loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed.");
    } finally {
      setImporting(false);
    }
  }, [payload, loadCases]);

  const issueCount = (issues: ValidationIssue[], severity: string) =>
    issues.filter((i) => i.severity === severity).length;

  const resultColumns: TableColumn<ResearchCaseImportResponse["results"][number]>[] = [
    { key: "id", label: "Case ID", mono: true, render: (r) => r.research_case_id },
    {
      key: "person",
      label: "Person",
      render: (r) => r.person_name ?? "—",
    },
    { key: "dob", label: "DOB", render: (r) => r.dob },
    { key: "events", label: "Events", render: (r) => r.total_events },
    {
      key: "snapshots",
      label: "Snapshots",
      render: (r) => (
        <span style={{ color: "var(--cyan-300)", fontWeight: "var(--weight-semibold)" }}>
          {r.total_snapshots_created}
        </span>
      ),
    },
    {
      key: "status",
      label: "Status",
      render: (r) =>
        r.errors.length ? (
          <Badge tone="danger">{r.errors[0]}</Badge>
        ) : r.duplicate ? (
          <Badge tone="gold">duplicate</Badge>
        ) : (
          <Badge tone="success">imported</Badge>
        ),
    },
  ];

  const listColumns: TableColumn<ResearchCaseSummary>[] = [
    { key: "id", label: "Case ID", mono: true, render: (c) => c.research_case_id },
    { key: "person", label: "Person", render: (c) => c.person_name ?? "—" },
    { key: "dob", label: "DOB", render: (c) => c.dob },
    { key: "events", label: "Events", render: (c) => c.total_events },
    { key: "gender", label: "Gender", render: (c) => titleCase(c.gender ?? "—") },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", padding: "var(--space-4)" }}>
      <div>
        <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)" }}>
          Research Case Import
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", maxWidth: 720 }}>
          Drop a JSON batch of research cases. Each case is validated (birth data, duplicates, date
          consistency), then astrological snapshots are computed per event and persisted to the
          database.
        </p>
      </div>

      {/* ── File drop zone ─────────────────────────────────────────────────── */}
      <Card padding="var(--space-4)">
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const file = e.dataTransfer.files?.[0];
            if (file) void handleFile(file);
          }}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          style={{
            border: "2px dashed var(--border-default)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            textAlign: "center",
            cursor: "pointer",
            transition: "border-color var(--duration-fast)",
          }}
          onMouseOver={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "var(--cyan-400)")}
          onMouseOut={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "var(--border-default)")}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
            }}
          />
          <p style={{ color: "var(--text-primary)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
            {fileName ? `Loaded: ${fileName}` : "Drag & drop a JSON file here, or click to browse"}
          </p>
          <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", margin: "var(--space-2) 0 0" }}>
            {payload ? `${payload.cases.length} case(s) parsed` : "Expects a {\"cases\": [...]} batch payload"}
          </p>
        </div>

        <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-3)" }}>
          <Button
            variant="secondary"
            size="md"
            onClick={() => void handleFile(new File([JSON.stringify(SAMPLE_PAYLOAD, null, 2)], "sample.json", { type: "application/json" }))}
          >
            Load sample
          </Button>
          <Button
            variant="primary"
            size="md"
            disabled={!payload || importing}
            onClick={handleImport}
          >
            {importing ? "Importing…" : `Import ${payload?.cases.length ?? 0} case(s)`}
          </Button>
        </div>
      </Card>

      {error && (
        <Card glow="gold">
          <p style={{ color: "var(--text-primary)", margin: 0 }}>{error}</p>
        </Card>
      )}

      {/* ── Validation preview ─────────────────────────────────────────────── */}
      {validation && (
        <Card padding="var(--space-4)">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-3)" }}>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
              Validation Preview
            </h2>
            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <Badge tone="success">{validation.total_valid} valid</Badge>
              <Badge tone="danger">{validation.total_invalid} invalid</Badge>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {validation.validations.map((v, i) => (
              <div
                key={i}
                style={{
                  border: `1px solid ${v.valid ? "var(--border-default)" : "rgba(248,113,113,0.4)"}`,
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3)",
                  background: "var(--bg-surface-800)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
                  <strong style={{ color: "var(--text-primary)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}>
                    {v.research_case_id ?? `Case ${i + 1}`}
                  </strong>
                  {v.valid ? <Badge tone="success">valid</Badge> : <Badge tone="danger">invalid</Badge>}
                  {v.duplicate_case && <Badge tone="gold">duplicate case</Badge>}
                  {v.duplicate_events.length > 0 && <Badge tone="gold">duplicate events</Badge>}
                  <span style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                    DOB {v.person_dob ?? "—"}
                  </span>
                </div>
                {v.issues.length > 0 && (
                  <ul style={{ margin: "var(--space-2) 0 0", paddingLeft: "var(--space-4)", color: "var(--text-secondary)", fontSize: "var(--text-sm)" }}>
                    {v.issues.map((issue, j) => (
                      <li key={j}>
                        <span
                          style={{
                            color: issue.severity === "error" ? "var(--red-300)" : issue.severity === "warning" ? "var(--gold-300)" : "var(--text-tertiary)",
                          }}
                        >
                          [{issue.severity}] {issue.field}: {issue.message}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── Import result ──────────────────────────────────────────────────── */}
      {importResult && (
        <Card padding="var(--space-4)">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-3)" }}>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
              Import Results
            </h2>
            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <Badge tone="success">{importResult.succeeded} succeeded</Badge>
              <Badge tone="danger">{importResult.failed} failed</Badge>
            </div>
          </div>
          <Table columns={resultColumns} rows={importResult.results} />
        </Card>
      )}

      {/* ── Previously imported cases ──────────────────────────────────────── */}
      <Card padding="var(--space-4)">
        <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginBottom: "var(--space-3)" }}>
          Imported Cases ({cases.length})
        </h2>
        {cases.length === 0 ? (
          <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", margin: 0 }}>
            No research cases imported yet.
          </p>
        ) : (
          <Table columns={listColumns} rows={cases} />
        )}
      </Card>
    </div>
  );
}
