"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, KpiCard, Select, type SelectOption } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type {
  ResearchCaseBatchImport,
  ResearchCaseBatchValidation,
  ResearchCaseImportResponse,
  ResearchCasePayload,
} from "@/lib/types";

const TARGET_FIELDS = [
  { key: "name", label: "Full Name", required: true },
  { key: "gender", label: "Gender", required: true },
  { key: "dob", label: "Date of Birth", required: true },
  { key: "tob", label: "Time of Birth", required: false },
  { key: "place", label: "Place", required: true },
  { key: "country", label: "Country", required: false },
  { key: "latitude", label: "Latitude", required: true },
  { key: "longitude", label: "Longitude", required: true },
  { key: "timezone", label: "Timezone", required: false },
] as const;
type TargetFieldKey = (typeof TARGET_FIELDS)[number]["key"];

type Step = "upload" | "map" | "preview" | "import";

/** Minimal, dependency-free CSV parser — handles quoted fields and commas
 * inside quotes. Sufficient for the "any CSV of people" upload this wizard
 * accepts (no embedded newlines inside a field). */
function parseCsv(text: string): { headers: string[]; rows: string[][] } {
  const lines = text.replace(/\r\n/g, "\n").split("\n").filter((l) => l.trim().length > 0);
  const parseLine = (line: string): string[] => {
    const cells: string[] = [];
    let cur = "";
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQuotes) {
        if (ch === '"' && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else if (ch === '"') {
          inQuotes = false;
        } else {
          cur += ch;
        }
      } else if (ch === '"') {
        inQuotes = true;
      } else if (ch === ",") {
        cells.push(cur);
        cur = "";
      } else {
        cur += ch;
      }
    }
    cells.push(cur);
    return cells.map((c) => c.trim());
  };
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = parseLine(lines[0]);
  const rows = lines.slice(1).map(parseLine);
  return { headers, rows };
}

function guessMapping(headers: string[]): Record<TargetFieldKey, string | null> {
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z]/g, "");
  const guesses: Record<TargetFieldKey, string[]> = {
    name: ["fullname", "name"],
    gender: ["gender", "sex"],
    dob: ["dob", "dateofbirth", "birthdate"],
    tob: ["tob", "timeofbirth", "birthtime"],
    place: ["place", "birthplace", "placeofbirth", "city"],
    country: ["country"],
    latitude: ["lat", "latitude"],
    longitude: ["lng", "lon", "longitude"],
    timezone: ["timezone", "tz"],
  };
  const result = {} as Record<TargetFieldKey, string | null>;
  for (const field of TARGET_FIELDS) {
    const candidates = guesses[field.key];
    const match = headers.find((h) => candidates.includes(norm(h)));
    result[field.key] = match ?? null;
  }
  return result;
}

export default function BulkImportPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [step, setStep] = useState<Step>("upload");
  const [fileName, setFileName] = useState<string | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<string[][]>([]);
  const [mapping, setMapping] = useState<Record<TargetFieldKey, string | null>>({} as Record<TargetFieldKey, string | null>);
  const [skipFirstRow, setSkipFirstRow] = useState(true);
  const [updateExisting, setUpdateExisting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validation, setValidation] = useState<ResearchCaseBatchValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ResearchCaseImportResponse | null>(null);
  const [showAllPreview, setShowAllPreview] = useState(false);

  const handleFile = async (file: File) => {
    setError(null);
    setFileName(file.name);
    try {
      const text = await file.text();
      const { headers: h, rows: r } = parseCsv(text);
      if (h.length === 0) throw new Error("CSV appears to be empty.");
      setHeaders(h);
      setRows(skipFirstRow ? r : [h, ...r]);
      setMapping(guessMapping(h));
      setStep("map");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not parse CSV file.");
    }
  };

  const buildPayload = (): ResearchCaseBatchImport => {
    const colIndex = (field: TargetFieldKey) => {
      const col = mapping[field];
      return col ? headers.indexOf(col) : -1;
    };
    const cases: ResearchCasePayload[] = rows.map((row) => {
      const get = (field: TargetFieldKey) => {
        const idx = colIndex(field);
        return idx >= 0 ? (row[idx] ?? "").trim() : "";
      };
      const genderRaw = get("gender").toLowerCase();
      const gender = genderRaw.startsWith("f") ? "Female" : genderRaw.startsWith("m") ? "Male" : "Other";
      const dob = get("dob");
      return {
        person: {
          name: get("name") || null,
          gender: gender as "Male" | "Female" | "Other",
          dob,
          tob: get("tob") || null,
          place: get("place"),
          country: get("country") || null,
          latitude: parseFloat(get("latitude")) || 0,
          longitude: parseFloat(get("longitude")) || 0,
          timezone: get("timezone") || "UTC",
          source: "Bulk CSV import",
        },
        ayanamsa: "lahiri",
        house_system: "P",
        life_events: [
          {
            type: "Other",
            event_date: dob,
            category: "Other",
            description: "Imported via bulk CSV upload",
          },
        ],
        source_batch: `bulk-csv-import:${fileName ?? "unknown"}`,
      };
    });
    return { cases, generate_ids: true, update_existing: updateExisting };
  };

  const runValidate = async () => {
    setValidating(true);
    setError(null);
    try {
      const result = await researchCasesApi.validate(buildPayload());
      setValidation(result);
      setStep("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed.");
    } finally {
      setValidating(false);
    }
  };

  const runImport = async () => {
    setImporting(true);
    setError(null);
    try {
      const result = await researchCasesApi.importCases(buildPayload());
      setImportResult(result);
      setStep("import");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed.");
    } finally {
      setImporting(false);
    }
  };

  const downloadErrorReport = () => {
    if (!validation) return;
    const lines = ["row,status,issues"];
    validation.validations.forEach((v, i) => {
      const issues = v.issues.map((iss) => `${iss.field}: ${iss.message}`).join("; ");
      lines.push(`${i + 1},${v.valid ? "valid" : "error"},"${issues.replace(/"/g, '""')}"`);
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "bulk-import-errors.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const stats = useMemo(() => {
    if (!validation) return null;
    const totalRows = validation.validations.length;
    const validRows = validation.total_valid;
    const errorRows = validation.validations.filter((v) => !v.valid).length;
    const warningRows = validation.validations.filter(
      (v) => v.valid && v.issues.some((i) => i.severity === "warning"),
    ).length;
    const totalEvents = totalRows; // one placeholder event per row for a plain CSV
    return { totalRows, validRows, errorRows, warningRows, totalEvents };
  }, [validation]);

  const previewRows = validation
    ? (showAllPreview ? validation.validations : validation.validations.slice(0, 10))
    : [];

  const stepOrder: { key: Step; label: string; detail: string }[] = [
    { key: "upload", label: "Upload File", detail: "Select and upload CSV" },
    { key: "map", label: "Map Columns", detail: "Map CSV columns" },
    { key: "preview", label: "Preview & Validate", detail: "Review and validate data" },
    { key: "import", label: "Import", detail: "Import data to system" },
  ];
  const stepIndex = stepOrder.findIndex((s) => s.key === step);

  return (
    <AppShell sectionColor="--section-research">
      <div className="flex flex-col gap-5 p-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Bulk Import Research Cases</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Import multiple research cases from a CSV file.</p>
          </div>
          <Link href="/research/cases" className="text-sm text-cyan-600 dark:text-cyan-400 font-medium">
            ← Back to Cases
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {stepOrder.map((s, i) => (
            <div key={s.key} className="flex items-center gap-3 flex-1">
              <div className="flex items-center gap-2">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${
                    i < stepIndex
                      ? "bg-cyan-500 text-white"
                      : i === stepIndex
                        ? "bg-cyan-500 text-white"
                        : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                  }`}
                >
                  {i + 1}
                </div>
                <div className="hidden sm:block">
                  <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">{s.label}</p>
                  <p className="text-[11px] text-slate-400">{s.detail}</p>
                </div>
              </div>
              {i < stepOrder.length - 1 && <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />}
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40 text-sm text-rose-700 dark:text-rose-300">
            {error}
          </div>
        )}

        {step === "upload" && (
          <Card>
            <div className="p-5 flex flex-col gap-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Upload CSV File</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Upload your CSV file containing research cases.</p>
              </div>
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
                className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-10 text-center cursor-pointer hover:border-cyan-400 hover:bg-cyan-400/5 transition"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void handleFile(file);
                  }}
                />
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Drag & drop your CSV file here</p>
                <p className="text-xs text-slate-400 mt-1">or</p>
                <Button size="sm" variant="secondary" className="mt-2">Choose File</Button>
              </div>

              <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <input type="checkbox" checked={skipFirstRow} onChange={(e) => setSkipFirstRow(e.target.checked)} />
                Skip first row (header)
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <input type="checkbox" checked={updateExisting} onChange={(e) => setUpdateExisting(e.target.checked)} />
                Update existing cases if name, DOB and TOB match
              </label>
            </div>
          </Card>
        )}

        {step === "map" && (
          <Card>
            <div className="p-5 flex flex-col gap-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Map Columns</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {fileName} — {rows.length} row(s) detected. Map each target field to a CSV column.
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {TARGET_FIELDS.map((field) => {
                  const options: SelectOption[] = [
                    { value: "", label: "— not mapped —" },
                    ...headers.map((h) => ({ value: h, label: h })),
                  ];
                  return (
                    <Select
                      key={field.key}
                      label={`${field.label}${field.required ? " *" : ""}`}
                      options={options}
                      value={mapping[field.key] ?? ""}
                      onChange={(v) => setMapping((prev) => ({ ...prev, [field.key]: v || null }))}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between">
                <Button variant="secondary" onClick={() => setStep("upload")}>Back</Button>
                <Button onClick={runValidate} disabled={validating}>
                  {validating ? "Validating…" : "Next: Preview & Validate"}
                </Button>
              </div>
            </div>
          </Card>
        )}

        {step === "preview" && validation && stats && (
          <Card>
            <div className="p-5 flex flex-col gap-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Preview & Validate Data</h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <KpiCard label="Total Rows" value={stats.totalRows} accent="cyan" />
                <KpiCard label="Valid Rows" value={stats.validRows} accent="success" />
                <KpiCard label="Errors" value={stats.errorRows} accent={stats.errorRows > 0 ? "gold" : "cyan"} />
                <KpiCard label="Warnings" value={stats.warningRows} accent="gold" />
                <KpiCard label="Events" value={stats.totalEvents} accent="violet" />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase text-[10px]">
                      <th className="py-2 px-2">Row</th>
                      <th className="py-2 px-2">Case ID</th>
                      <th className="py-2 px-2">DOB</th>
                      <th className="py-2 px-2">Status</th>
                      <th className="py-2 px-2">Issues</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {previewRows.map((v, i) => (
                      <tr key={i}>
                        <td className="py-2 px-2">{i + 1}</td>
                        <td className="py-2 px-2 font-mono">{v.research_case_id ?? "—"}</td>
                        <td className="py-2 px-2">{v.person_dob ?? "—"}</td>
                        <td className="py-2 px-2">
                          {v.valid ? (
                            v.issues.length > 0 ? <Badge tone="gold">Warning</Badge> : <Badge tone="success">Valid</Badge>
                          ) : (
                            <Badge tone="danger">Error</Badge>
                          )}
                        </td>
                        <td className="py-2 px-2 text-slate-500">
                          {v.issues.slice(0, 1).map((iss) => iss.message).join("; ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!showAllPreview && validation.validations.length > 10 && (
                  <button
                    type="button"
                    onClick={() => setShowAllPreview(true)}
                    className="text-xs text-cyan-600 dark:text-cyan-400 mt-2"
                  >
                    View All ({validation.validations.length} rows)
                  </button>
                )}
              </div>

              {stats.errorRows > 0 && (
                <div className="flex items-center justify-between p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40 text-xs text-rose-700 dark:text-rose-300">
                  <span>{stats.errorRows} row(s) have errors and will not be imported.</span>
                  <button type="button" onClick={downloadErrorReport} className="font-semibold underline shrink-0 ml-3">
                    Download Error Report
                  </button>
                </div>
              )}

              <div className="flex justify-between">
                <Button variant="secondary" onClick={() => setStep("map")}>Back</Button>
                <Button onClick={runImport} disabled={importing || stats.validRows === 0}>
                  {importing ? "Importing…" : `Import ${stats.validRows} Case${stats.validRows !== 1 ? "s" : ""}`}
                </Button>
              </div>
            </div>
          </Card>
        )}

        {step === "import" && importResult && (
          <Card>
            <div className="p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Import Complete</h2>
                <div className="flex gap-2">
                  <Badge tone="success">{importResult.succeeded} imported</Badge>
                  {importResult.failed > 0 && <Badge tone="danger">{importResult.failed} failed</Badge>}
                </div>
              </div>
              <div className="flex gap-3">
                <Button href="/research/cases">View Research Cases</Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setStep("upload");
                    setFileName(null);
                    setHeaders([]);
                    setRows([]);
                    setValidation(null);
                    setImportResult(null);
                  }}
                >
                  Import More
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
