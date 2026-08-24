"use client";

import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, SearchInput, TreeView, type TreeNode } from "@/components/ui";
import {
  useEventTypeTree,
  useUpdateEventType,
  type EventTypeNode,
} from "@/lib/research";

export const dynamic = "force-dynamic";

function flattenById(nodes: EventTypeNode[], out: Map<string, EventTypeNode>) {
  for (const n of nodes) {
    out.set(n.id, n);
    if (n.children.length) flattenById(n.children, out);
  }
}

/** Keep a node if its own name matches, or any descendant matches. */
function filterTree(nodes: EventTypeNode[], query: string): EventTypeNode[] {
  if (!query.trim()) return nodes;
  const q = query.trim().toLowerCase();
  const walk = (n: EventTypeNode): EventTypeNode | null => {
    const selfMatch = n.name.toLowerCase().includes(q) || n.path.toLowerCase().includes(q);
    const children = n.children.map(walk).filter((c): c is EventTypeNode => c !== null);
    if (selfMatch || children.length > 0) {
      return { ...n, children };
    }
    return null;
  };
  return nodes.map(walk).filter((n): n is EventTypeNode => n !== null);
}

function toTreeNodes(nodes: EventTypeNode[]): TreeNode[] {
  return nodes.map((n) => ({
    key: n.id,
    label: n.name,
    color: n.source === "manual" ? "var(--cyan-300)" : undefined,
    defaultOpen: false,
    children: toTreeNodes(n.children),
  }));
}

export default function EventTypeTreePage() {
  const { data, isLoading, isError } = useEventTypeTree();
  const updateEventType = useUpdateEventType();

  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
  const [descriptionInput, setDescriptionInput] = useState("");

  const eventTypes = data?.event_types ?? [];

  const byId = useMemo(() => {
    const m = new Map<string, EventTypeNode>();
    flattenById(eventTypes, m);
    return m;
  }, [eventTypes]);

  const filtered = useMemo(() => filterTree(eventTypes, search), [eventTypes, search]);
  const treeData = useMemo(() => toTreeNodes(filtered), [filtered]);

  const selected = selectedId ? byId.get(selectedId) : undefined;
  const totalNodes = byId.size;

  const handleSelect = (key: string) => {
    setSelectedId(key);
    setDescriptionInput("");
  };

  const handleSave = () => {
    if (!selectedId) return;
    updateEventType.mutate({
      id: selectedId,
      data: { description: descriptionInput.trim() || null },
    });
  };

  return (
    <AppShell sectionColor="--section-research">
      <div className="flex flex-col gap-5 p-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Event Tree</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Open, hierarchical event types — replaces the fixed event-type list for manual
              entry and import. Auto-created as researchers register new events, up to 6 levels
              deep.
            </p>
          </div>
          <Badge tone="cyan">{totalNodes} event type{totalNodes === 1 ? "" : "s"}</Badge>
        </div>

        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search event types (e.g. Marriage, Promotion, Accident)…"
        />

        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5">
          <Card>
            {isLoading && <p className="text-sm text-slate-500 p-4">Loading event tree…</p>}
            {isError && (
              <p className="text-sm text-red-500 p-4">
                Could not load the event tree. Confirm the backend is running and the database
                migration has been applied.
              </p>
            )}
            {!isLoading && !isError && treeData.length === 0 && (
              <p className="text-sm text-slate-500 p-4">
                {search ? "No event types match your search." : "No event types yet — register a life event to populate the tree."}
              </p>
            )}
            {!isLoading && !isError && treeData.length > 0 && (
              <div key={search} className="p-4 max-h-[70vh] overflow-y-auto">
                <TreeView data={treeData} activeKey={selectedId} onSelect={handleSelect} />
              </div>
            )}
          </Card>

          <Card>
            <div className="p-4 flex flex-col gap-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Node details
              </h2>
              {!selected && (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Select an event type on the left to add a description.
                </p>
              )}
              {selected && (
                <>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Selected</p>
                    <p className="text-sm text-slate-900 dark:text-slate-100">{selected.path}</p>
                  </div>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-slate-600 dark:text-slate-300">Description</span>
                    <textarea
                      value={descriptionInput}
                      onChange={(e) => setDescriptionInput(e.target.value)}
                      rows={4}
                      placeholder="Optional note about this event type"
                      className="w-full rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </label>

                  <Button onClick={handleSave} disabled={updateEventType.isPending}>
                    {updateEventType.isPending ? "Saving…" : "Save"}
                  </Button>
                  {updateEventType.isError && (
                    <p className="text-xs text-red-500">Could not save — try again.</p>
                  )}
                  {updateEventType.isSuccess && (
                    <p className="text-xs text-emerald-500">Saved.</p>
                  )}
                </>
              )}
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
