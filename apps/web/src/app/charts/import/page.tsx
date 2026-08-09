"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { useAnalyzeWorkflow, useBulkImportCharts, useCheckExistingChart } from "@/lib/workflow";
import { ApiError } from "@/lib/api";
import { parseJhdFile, type JhdParsePreview } from "@/lib/jhd-import";
import type {
  AyanamsaCode,
  BulkImportRow,
  HouseSystemCode,
  WorkflowAnalysisRequest,
  WorkflowDuplicateCheckResponse,
} from "@/lib/types";

const VALID_AYANAMSAS: AyanamsaCode[] = ["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"];
const VALID_HOUSE_SYSTEMS: HouseSystemCode[] = ["W", "P", "K", "E"];

/** Loose header aliases so a real-world export ("name", "lat", "lng", ...)
 * doesn't force the user to rename columns first. */
const HEADER_ALIASES: Record<string, string> = {
  name: "subject_name",
  subject_name: "subject_name",
  birth_datetime_utc: "birth_datetime_utc",
  birth_date: "birth_datetime_utc",
  datetime: "birth_datetime_utc",
  birth_datetime: "birth_datetime_utc",
  lat: "latitude",
  latitude: "latitude",
  lon: "longitude",
  lng: "longitude",
  longitude: "longitude",
  place: "place_name",
  place_name: "place_name",
  birth_place: "place_name",
  ayanamsa: "ayanamsa",
  house_system: "house_system",
};

interface ParsedRow {
  raw: Record<string, string>;
  row: BulkImportRow | null;
  error: string | null;
}

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ",") {
      row.push(field);
      field = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field);
      field = "";
      if (row.some((cell) => cell.trim() !== "")) rows.push(row);
      row = [];
    } else {
      field += c;
    }
  }
  if (field !== "" || row.length > 0) {
    row.push(field);
    if (row.some((cell) => cell.trim() !== "")) rows.push(row);
  }
  return rows;
}

/** Ensures an ISO datetime string carries a timezone offset — the backend
 * rejects naive datetimes. A bare "YYYY-MM-DDTHH:mm:ss" from a spreadsheet
 * export is assumed to already be UTC (matches this app's "birth_datetime
 * _utc" field naming) and gets a "Z" appended rather than silently failing. */
function normalizeDatetime(value: string): string {
  const trimmed = value.trim();
  if (/[Zz]$|[+-]\d{2}:?\d{2}$/.test(trimmed)) return trimmed;
  return `${trimmed.replace(" ", "T")}Z`;
}

function rowsFromTable(headerRow: string[], dataRows: string[][]): ParsedRow[] {
  const headers = headerRow.map((h) => HEADER_ALIASES[h.trim().toLowerCase()] ?? h.trim().toLowerCase());
  return dataRows.map((cells) => {
    const raw: Record<string, string> = {};
    headers.forEach((h, i) => {
      raw[h] = (cells[i] ?? "").trim();
    });
    return { raw, ...validateRow(raw) };
  });
}

function validateRow(raw: Record<string, string>): { row: BulkImportRow | null; error: string | null } {
  if (!raw.subject_name) return { row: null, error: "Missing subject_name" };
  if (!raw.birth_datetime_utc) return { row: null, error: "Missing birth_datetime_utc" };
  if (!raw.latitude || !raw.longitude) return { row: null, error: "Missing latitude/longitude" };

  const latitude = Number(raw.latitude);
  const longitude = Number(raw.longitude);
  if (Number.isNaN(latitude) || latitude < -90 || latitude > 90) {
    return { row: null, error: `Invalid latitude: ${raw.latitude}` };
  }
  if (Number.isNaN(longitude) || longitude < -180 || longitude > 180) {
    return { row: null, error: `Invalid longitude: ${raw.longitude}` };
  }

  const isoDatetime = normalizeDatetime(raw.birth_datetime_utc);
  if (Number.isNaN(new Date(isoDatetime).getTime())) {
    return { row: null, error: `Invalid birth_datetime_utc: ${raw.birth_datetime_utc}` };
  }

  const ayanamsa = raw.ayanamsa?.toLowerCase();
  const houseSystem = raw.house_system?.toUpperCase();

  return {
    row: {
      subject_name: raw.subject_name,
      birth_datetime_utc: isoDatetime,
      latitude,
      longitude,
      place_name: raw.place_name || null,
      ayanamsa: (VALID_AYANAMSAS as string[]).includes(ayanamsa ?? "") ? (ayanamsa as AyanamsaCode) : "lahiri",
      house_system: (VALID_HOUSE_SYSTEMS as string[]).includes(houseSystem ?? "") ? (houseSystem as HouseSystemCode) : "W",
    },
    error: null,
  };
}

function parseFile(name: string, text: string): ParsedRow[] {
  if (name.endsWith(".json")) {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) throw new Error("JSON file must contain an array of chart rows.");
    return data.map((entry) => {
      const raw: Record<string, string> = {};
      Object.entries(entry as Record<string, unknown>).forEach(([k, v]) => {
        const key = HEADER_ALIASES[k.trim().toLowerCase()] ?? k.trim().toLowerCase();
        raw[key] = v == null ? "" : String(v);
      });
      return { raw, ...validateRow(raw) };
    });
  }
  const table = parseCsv(text);
  if (table.length < 2) throw new Error("CSV file needs a header row plus at least one data row.");
  return rowsFromTable(table[0], table.slice(1));
}

export default function ImportChartPage() {
  const router = useRouter();
  const [fileName, setFileName] = useState<string | null>(null);
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const bulkImport = useBulkImportCharts();
  // When checked, every row is saved as a new chart even if it exactly
  // matches an already-saved one — off by default (reuse matches, same as
  // before this existed), since two different people sharing an exact
  // birth moment/location is the exception, not the norm, for a bulk file.
  const [forceNewBulk, setForceNewBulk] = useState(false);

  // .jhd (Jagannatha Hora) is a single-chart file, not a bulk row table —
  // parsed client-side, then created through the same single-chart pipeline
  // as the dashboard's "New Chart" flow instead of /workflow/bulk-import.
  const [jhdPreview, setJhdPreview] = useState<JhdParsePreview | null>(null);
  const [jhdRequest, setJhdRequest] = useState<WorkflowAnalysisRequest | null>(null);
  const analyzeJhd = useAnalyzeWorkflow();
  const checkExisting = useCheckExistingChart();
  const [jhdDuplicate, setJhdDuplicate] = useState<WorkflowDuplicateCheckResponse | null>(null);

  const validRows = parsedRows.filter((r) => r.row).map((r) => r.row!);
  const invalidCount = parsedRows.length - validRows.length;

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setParseError(null);
    setParsedRows([]);
    setJhdPreview(null);
    setJhdRequest(null);
    setJhdDuplicate(null);
    bulkImport.reset();
    analyzeJhd.reset();
    checkExisting.reset();

    if (file.name.toLowerCase().endsWith(".jhd")) {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const result = parseJhdFile(file.name, bytes);
      if (result.error || !result.request || !result.preview) {
        setParseError(result.error ?? "Could not parse this .jhd file.");
        return;
      }
      setJhdPreview(result.preview);
      setJhdRequest(result.request);
      return;
    }

    try {
      const text = await file.text();
      const rows = parseFile(file.name.toLowerCase(), text);
      if (rows.length > 100) {
        setParseError(`This file has ${rows.length} rows — only the first 100 can be imported per upload.`);
        setParsedRows(rows.slice(0, 100));
      } else {
        setParsedRows(rows);
      }
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "Could not parse this file.");
    }
  };

  const handleImport = () => {
    bulkImport.mutate(validRows.map((r) => ({ ...r, force_new: forceNewBulk })));
  };

  const handleCreateFromJhd = () => {
    if (!jhdRequest) return;
    setJhdDuplicate(null);
    checkExisting.mutate(
      {
        birth_datetime_utc: jhdRequest.birth_datetime_utc,
        latitude: jhdRequest.latitude,
        longitude: jhdRequest.longitude,
        ayanamsa: jhdRequest.ayanamsa,
        house_system: jhdRequest.house_system,
      },
      {
        onSuccess: (result) => {
          if (result.exists) {
            setJhdDuplicate(result);
          } else {
            analyzeJhd.mutate(jhdRequest, {
              onSuccess: (data) => router.push(`/charts/${data.chart_id}`),
            });
          }
        },
        onError: () =>
          analyzeJhd.mutate(jhdRequest, {
            onSuccess: (data) => router.push(`/charts/${data.chart_id}`),
          }),
      },
    );
  };

  const handleSaveJhdAsNewAnyway = () => {
    if (!jhdRequest) return;
    analyzeJhd.mutate(
      { ...jhdRequest, force_new: true },
      { onSuccess: (data) => router.push(`/charts/${data.chart_id}`) },
    );
  };

  const downloadTemplate = () => {
    const csv = [
      "subject_name,birth_datetime_utc,latitude,longitude,place_name,ayanamsa,house_system",
      "Jane Doe,1990-05-15T08:30:00Z,19.076,72.8777,\"Mumbai, Maharashtra, India\",lahiri,W",
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "astroos-import-template.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Import Charts
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Bulk-create saved charts from a CSV or JSON file of birth details.
          </p>
        </div>
        <button type="button" onClick={downloadTemplate} className="obsidian-btn-secondary text-sm">
          Download CSV Template
        </button>
      </div>

      <div className="obsidian-card p-5">
        <label className="mb-2 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
          Choose a .csv, .json, or .jhd file
        </label>
        <input
          type="file"
          accept=".csv,.json,.jhd"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
          className="obsidian-input text-sm"
        />
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          Required columns: subject_name, birth_datetime_utc (ISO, UTC), latitude, longitude. Optional: place_name, ayanamsa, house_system.
          {" "}Also accepts a single Jagannatha Hora (.jhd) birth file — creates one chart directly, no bulk row table.
        </p>

        {parseError && (
          <p className="mt-3 text-sm" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
            {parseError}
          </p>
        )}

        {fileName && parsedRows.length > 0 && (
          <div className="mt-4">
            <p className="mb-2 text-sm" style={{ color: "var(--text-primary)" }}>
              {fileName}: <span style={{ color: "#4ade80" }}>{validRows.length} valid</span>
              {invalidCount > 0 && (
                <>
                  {" · "}
                  <span style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>{invalidCount} invalid</span>
                </>
              )}
            </p>

            <div className="max-h-80 overflow-y-auto overflow-x-auto rounded-lg border" style={{ borderColor: "var(--border-primary)" }}>
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="p-2">#</th>
                    <th className="p-2">Name</th>
                    <th className="p-2">Birth (UTC)</th>
                    <th className="p-2">Lat</th>
                    <th className="p-2">Lon</th>
                    <th className="p-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {parsedRows.map((r, i) => (
                    <tr key={i} className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                      <td className="p-2">{i + 1}</td>
                      <td className="p-2">{r.raw.subject_name || "—"}</td>
                      <td className="p-2">{r.raw.birth_datetime_utc || "—"}</td>
                      <td className="p-2">{r.raw.latitude || "—"}</td>
                      <td className="p-2">{r.raw.longitude || "—"}</td>
                      <td className="p-2">
                        {r.row ? (
                          <span style={{ color: "#4ade80" }}>Valid</span>
                        ) : (
                          <span style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>{r.error}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <label className="mt-3 flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
              <input
                type="checkbox"
                checked={forceNewBulk}
                onChange={(e) => setForceNewBulk(e.target.checked)}
                className="h-4 w-4 rounded"
              />
              Always save as a new chart, even if a row&apos;s birth data matches an existing saved chart
              (two different people can share an exact birth moment and place).
            </label>

            <button
              type="button"
              onClick={handleImport}
              disabled={validRows.length === 0 || bulkImport.isPending}
              title="Bulk imports are limited to 5 uploads per hour, up to 100 rows each."
              className="obsidian-btn-primary mt-3 text-sm disabled:cursor-not-allowed disabled:opacity-40"
            >
              {bulkImport.isPending ? "Importing…" : `Import ${validRows.length} Chart${validRows.length === 1 ? "" : "s"}`}
            </button>
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              Limited to 5 bulk imports per hour, up to 100 rows each.
            </p>
          </div>
        )}

        {jhdPreview && (
          <div className="mt-4">
            <p className="mb-2 text-sm" style={{ color: "var(--text-primary)" }}>
              {fileName}: <span style={{ color: "#4ade80" }}>parsed</span>
            </p>
            <div className="rounded-lg border p-4 text-sm" style={{ borderColor: "var(--border-primary)" }}>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
                <dt style={{ color: "var(--text-muted)" }}>Subject</dt>
                <dd style={{ color: "var(--text-primary)" }}>{jhdPreview.subject_name}</dd>
                <dt style={{ color: "var(--text-muted)" }}>Birth (local, as stored in file)</dt>
                <dd style={{ color: "var(--text-primary)" }}>{jhdPreview.birth_local}</dd>
                <dt style={{ color: "var(--text-muted)" }}>Latitude</dt>
                <dd style={{ color: "var(--text-primary)" }}>{jhdPreview.latitude.toFixed(4)}</dd>
                <dt style={{ color: "var(--text-muted)" }}>Longitude</dt>
                <dd style={{ color: "var(--text-primary)" }}>{jhdPreview.longitude.toFixed(4)}</dd>
                <dt style={{ color: "var(--text-muted)" }}>Ayanamsa / House system</dt>
                <dd style={{ color: "var(--text-primary)" }}>{jhdPreview.ayanamsa} / {jhdPreview.house_system}</dd>
              </dl>
            </div>

            {jhdDuplicate?.exists ? (
              <div
                className="mt-4 rounded-lg border p-4"
                style={{ borderColor: "#f59e0b", backgroundColor: "rgba(245,158,11,0.08)" }}
              >
                <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                  A saved chart already matches this exact birth date, time, and location
                </p>
                <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                  Saved as &ldquo;{jhdDuplicate.subject_name}&rdquo;
                  {jhdDuplicate.saved_at && ` on ${new Date(jhdDuplicate.saved_at).toLocaleDateString()}`}.
                  This could be the same chart, or a different person born at the same moment.
                </p>
                <div className="mt-3 flex gap-2">
                  {jhdDuplicate.chart_id && (
                    <Link href={`/charts/${jhdDuplicate.chart_id}`} className="obsidian-btn-secondary text-xs">
                      View Existing Chart
                    </Link>
                  )}
                  <button
                    type="button"
                    onClick={handleSaveJhdAsNewAnyway}
                    disabled={analyzeJhd.isPending}
                    className="obsidian-btn-primary text-xs"
                  >
                    {analyzeJhd.isPending ? "Creating…" : "Save as New Chart Anyway"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setJhdDuplicate(null)}
                    className="text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleCreateFromJhd}
                disabled={analyzeJhd.isPending || checkExisting.isPending}
                title="Runs the full analysis pipeline once, same as New Chart — not subject to the bulk-import rate limit."
                className="obsidian-btn-primary mt-4 text-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                {analyzeJhd.isPending ? "Creating…" : checkExisting.isPending ? "Checking…" : "Create Chart"}
              </button>
            )}

            {analyzeJhd.isError && (
              <p className="mt-2 text-sm" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
                {analyzeJhd.error instanceof ApiError ? analyzeJhd.error.detail : "Could not create this chart."}
              </p>
            )}
          </div>
        )}
      </div>

      {bulkImport.isError && (
        <div className="obsidian-card mt-4 p-4 text-sm" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
          {bulkImport.error instanceof ApiError ? bulkImport.error.detail : "Import failed."}
        </div>
      )}

      {bulkImport.data && (
        <div className="obsidian-card mt-4 p-5">
          <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Import Results
          </h2>
          <p className="mb-3 text-sm" style={{ color: "var(--text-secondary)" }}>
            <span style={{ color: "#4ade80" }}>{bulkImport.data.succeeded} succeeded</span>
            {bulkImport.data.failed > 0 && (
              <>
                {" · "}
                <span style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>{bulkImport.data.failed} failed</span>
              </>
            )}
            {" "}of {bulkImport.data.total} rows.
          </p>
          <ul className="max-h-60 space-y-1 overflow-y-auto text-xs">
            {bulkImport.data.results.map((r) => (
              <li key={r.row_index} className="flex items-center justify-between border-b py-1" style={{ borderColor: "var(--border-primary)" }}>
                <span style={{ color: "var(--text-primary)" }}>{r.subject_name}</span>
                {r.success ? (
                  r.matched_existing ? (
                    <span title="Birth data matched an already-saved chart, so that chart was reused instead of creating a new one." style={{ color: "#f59e0b" }}>
                      Matched existing chart
                    </span>
                  ) : (
                    <span style={{ color: "#4ade80" }}>Created</span>
                  )
                ) : (
                  <span style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>{r.error}</span>
                )}
              </li>
            ))}
          </ul>
          {bulkImport.data.succeeded > 0 && (
            <Link href="/charts/history" className="obsidian-btn-primary mt-4 inline-flex text-sm">
              View My Charts
            </Link>
          )}
        </div>
      )}
    </AppShell>
  );
}
