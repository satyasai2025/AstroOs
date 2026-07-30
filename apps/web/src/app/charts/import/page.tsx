"use client";

import { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { useBulkImportCharts } from "@/lib/workflow";
import { ApiError } from "@/lib/api";
import type { AyanamsaCode, BulkImportRow, HouseSystemCode } from "@/lib/types";

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
  const [fileName, setFileName] = useState<string | null>(null);
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const bulkImport = useBulkImportCharts();

  const validRows = parsedRows.filter((r) => r.row).map((r) => r.row!);
  const invalidCount = parsedRows.length - validRows.length;

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setParseError(null);
    setParsedRows([]);
    bulkImport.reset();
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
    bulkImport.mutate(validRows);
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
          Choose a .csv or .json file
        </label>
        <input
          type="file"
          accept=".csv,.json"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
          className="obsidian-input text-sm"
        />
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          Required columns: subject_name, birth_datetime_utc (ISO, UTC), latitude, longitude. Optional: place_name, ayanamsa, house_system.
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

            <button
              type="button"
              onClick={handleImport}
              disabled={validRows.length === 0 || bulkImport.isPending}
              className="obsidian-btn-primary mt-4 text-sm disabled:cursor-not-allowed disabled:opacity-40"
            >
              {bulkImport.isPending ? "Importing…" : `Import ${validRows.length} Chart${validRows.length === 1 ? "" : "s"}`}
            </button>
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
                  <span style={{ color: "#4ade80" }}>Created</span>
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
