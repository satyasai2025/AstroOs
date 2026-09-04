"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Badge, Button, Card, Table, type TableColumn } from "@/components/ui";
import { AppShell } from "@/components/layout/AppShell";
import { CaseManualEntryForm } from "@/components/research/CaseManualEntryForm";
import { researchCasesApi } from "@/lib/researchCases";
import { titleCaseToken } from "@/lib/api";
import type {
  ResearchCaseBatchImport,
  ResearchCaseBatchValidation,
  ResearchCaseImportResponse,
  ResearchCaseSummary,
  ValidationIssue,
} from "@/lib/types";

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
  const [step, setStep] = useState<"upload" | "validate" | "result">("upload");
  const [uploadMode, setUploadMode] = useState<"file" | "manual">("file");

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
        setStep("validate");
        void runValidation(parsed);
      } catch (err) {
        setPayload(null);
        setError(err instanceof Error ? err.message : "Could not parse JSON file.");
      }
    },
    [runValidation],
  );

  const handleManualSubmit = useCallback(
    (p: ResearchCaseBatchImport) => {
      setFileName(null);
      setImportResult(null);
      setError(null);
      setPayload(p);
      setStep("validate");
      void runValidation(p);
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
      setStep("result");
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
    { key: "gender", label: "Gender", render: (c) => titleCaseToken(c.gender ?? "—") },
  ];

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Import Research Cases</h1>
        <p className="mt-2 text-sm text-gray-400">
          Upload a JSON batch file containing research cases. Each case is validated (birth data,
          duplicates, date consistency), then astrological snapshots are computed per event.
        </p>
      </div>

      {error && (
        <Card glow="gold" className="mb-6">
          <p className="text-red-400 m-0">{error}</p>
        </Card>
      )}

      {/* ── STEP 1: Upload ──────────────────────────────────────────────────── */}
      {step === "upload" && (
        <>
          <div className="mb-4 flex gap-2">
            <Button
              size="sm"
              variant={uploadMode === "file" ? "primary" : "secondary"}
              onClick={() => setUploadMode("file")}
            >
              Upload JSON
            </Button>
            <Button
              size="sm"
              variant={uploadMode === "manual" ? "primary" : "secondary"}
              onClick={() => setUploadMode("manual")}
            >
              Manual Entry
            </Button>
          </div>

          {uploadMode === "file" ? (
            <Card padding="0" className="mb-6">
              <div className="p-8">
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
                  className="border-2 border-dashed border-gray-600 rounded-lg p-12 text-center cursor-pointer transition-all hover:border-cyan-400 hover:bg-cyan-400/5"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/json,.json"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) void handleFile(file);
                    }}
                  />
                  <div className="text-gray-300">
                    <p className="text-lg font-semibold mb-1">Drop JSON file here</p>
                    <p className="text-sm text-gray-500">or click to browse</p>
                  </div>
                </div>

                <div className="mt-6 flex justify-center gap-3">
                  <Button
                    variant="secondary"
                    onClick={() => void handleFile(new File([JSON.stringify(SAMPLE_PAYLOAD, null, 2)], "sample.json", { type: "application/json" }))}
                  >
                    Load Sample
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <div className="mb-6">
              <CaseManualEntryForm onSubmit={handleManualSubmit} />
            </div>
          )}
        </>
      )}

      {/* ── STEP 2: Validation ──────────────────────────────────────────────── */}
      {step === "validate" && validation && (
        <Card padding="0" className="mb-6">
          <div className="border-b border-gray-700 px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold m-0">Validation Results</h2>
            <div className="flex gap-2">
              <Badge tone="success">{validation.total_valid} valid</Badge>
              <Badge tone="danger">{validation.total_invalid} invalid</Badge>
            </div>
          </div>

          <div className="p-6 max-h-96 overflow-y-auto space-y-2">
            {validation.validations.map((v, i) => (
              <div
                key={i}
                className={`border rounded-md p-3 ${
                  v.valid
                    ? "border-gray-700 bg-transparent"
                    : "border-red-900/40 bg-red-900/10"
                }`}
              >
                <div className="flex items-center gap-2 flex-wrap mb-2">
                  <code className="text-xs text-gray-400">
                    {v.research_case_id ?? `Case ${i + 1}`}
                  </code>
                  {v.valid ? <Badge tone="success">valid</Badge> : <Badge tone="danger">invalid</Badge>}
                  {v.duplicate_case && <Badge tone="gold">duplicate</Badge>}
                </div>
                {v.issues.length > 0 && (
                  <ul className="text-xs text-gray-400 space-y-1 pl-3 m-0">
                    {v.issues.slice(0, 2).map((issue, j) => (
                      <li key={j}>
                        <span className={issue.severity === "error" ? "text-red-400" : "text-yellow-400"}>
                          {issue.field}: {issue.message}
                        </span>
                      </li>
                    ))}
                    {v.issues.length > 2 && (
                      <li className="text-gray-500">+ {v.issues.length - 2} more</li>
                    )}
                  </ul>
                )}
              </div>
            ))}
          </div>

          <div className="border-t border-gray-700 px-6 py-4 flex gap-3 justify-end">
            <Button
              variant="secondary"
              onClick={() => {
                setStep("upload");
                setPayload(null);
                setValidation(null);
              }}
            >
              Back
            </Button>
            <Button
              variant="primary"
              disabled={validation.total_invalid > 0 || importing}
              onClick={handleImport}
            >
              {importing ? "Importing…" : `Import ${payload?.cases.length ?? 0} Case${payload?.cases.length !== 1 ? "s" : ""}`}
            </Button>
          </div>
        </Card>
      )}

      {/* ── STEP 3: Results ────────────────────────────────────────────────── */}
      {step === "result" && importResult && (
        <Card padding="0" className="mb-6">
          <div className="border-b border-gray-700 px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold m-0">Import Complete</h2>
            <div className="flex gap-2">
              <Badge tone="success">{importResult.succeeded} imported</Badge>
              {importResult.failed > 0 && (
                <Badge tone="danger">{importResult.failed} failed</Badge>
              )}
            </div>
          </div>

          <div className="p-6">
            <Table columns={resultColumns} rows={importResult.results} />
          </div>

          <div className="border-t border-gray-700 px-6 py-4 flex gap-3 justify-center">
            <Button
              variant="secondary"
              onClick={() => {
                setStep("upload");
                setPayload(null);
                setValidation(null);
                setImportResult(null);
              }}
            >
              Import More
            </Button>
          </div>
        </Card>
      )}
    </AppShell>
  );
}
