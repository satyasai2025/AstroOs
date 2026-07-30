"use client";

import { useState } from "react";
import { Badge, Button, Card, Tabs } from "@/components/ui";

type Tab = "entries" | "imports" | "audit";

interface EntryRow {
  id: string;
  title: string;
  category: string;
  status: "published" | "draft";
}

interface ImportRow {
  id: string;
  file: string;
  entries: number;
  date: string;
}

interface AuditRow {
  id: string;
  actor: string;
  action: string;
  target: string;
  date: string;
}

/**
 * Illustrative admin views matching the "Knowledge Admin" mockup — this app
 * has no knowledge-entry CRUD/import/audit-log backend yet (Karakatva
 * search is the one real knowledge feature, at /karakatva); every row here
 * is a fabricated sample.
 */
const ENTRIES: EntryRow[] = [
  { id: "e-1", title: "Gaja Kesari Yoga", category: "Yogas", status: "published" },
  { id: "e-2", title: "Mercury — Karakatva", category: "Karakatvas", status: "published" },
  { id: "e-3", title: "Ashlesha Nakshatra", category: "Nakshatras", status: "draft" },
];

const IMPORTS: ImportRow[] = [
  { id: "i-1", file: "bphs_chapter_36.txt", entries: 42, date: "2026-07-20" },
  { id: "i-2", file: "saravali_house_lords.csv", entries: 118, date: "2026-07-14" },
];

const AUDIT: AuditRow[] = [
  { id: "a-1", actor: "admin@astroos.dev", action: "Published", target: "Gaja Kesari Yoga", date: "2026-07-20 14:02" },
  { id: "a-2", actor: "admin@astroos.dev", action: "Imported", target: "bphs_chapter_36.txt", date: "2026-07-20 13:40" },
];

export default function KnowledgeAdminPage() {
  const [tab, setTab] = useState<Tab>("entries");

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Knowledge Admin
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Manage knowledge entries, imports, and edit history.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary">Browse Files</Button>
          <Button variant="primary">Add Entry</Button>
        </div>
      </div>

      <div className="mb-4">
        <Tabs
          tabs={[
            { key: "entries", label: "Knowledge Entries" },
            { key: "imports", label: "Recent Imports" },
            { key: "audit", label: "Audit Trail" },
          ]}
          active={tab}
          onChange={(k) => setTab(k as Tab)}
        />
      </div>

      {tab === "entries" && (
        <Card padding="0">
          {ENTRIES.map((e) => (
            <div key={e.id} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <div>
                <p style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)" }}>{e.title}</p>
                <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{e.category}</p>
              </div>
              <Badge tone={e.status === "published" ? "success" : "gold"}>{e.status}</Badge>
            </div>
          ))}
        </Card>
      )}

      {tab === "imports" && (
        <Card padding="0">
          {IMPORTS.map((i) => (
            <div key={i.id} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <div>
                <p style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                  {i.file}
                </p>
                <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{i.date}</p>
              </div>
              <Badge tone="cyan">{i.entries} entries</Badge>
            </div>
          ))}
        </Card>
      )}

      {tab === "audit" && (
        <Card padding="0">
          {AUDIT.map((a) => (
            <div key={a.id} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <div>
                <p style={{ fontSize: "var(--text-sm)", color: "var(--text-primary)" }}>
                  {a.actor} <span style={{ color: "var(--text-tertiary)" }}>{a.action.toLowerCase()}</span> {a.target}
                </p>
                <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{a.date}</p>
              </div>
            </div>
          ))}
        </Card>
      )}

      <p className="mt-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
        All entries, imports, and audit rows above are illustrative samples.
      </p>
    </div>
  );
}
