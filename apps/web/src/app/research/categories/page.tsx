"use client";

import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Input, SearchInput, TreeView, type TreeNode } from "@/components/ui";
import {
  useEventCategoryTree,
  useUpdateEventCategory,
  type EventCategoryNode,
} from "@/lib/research";

export const dynamic = "force-dynamic";

const HOUSE_NAMES: Record<number, string> = {
  1: "1st — Self / Body", 2: "2nd — Wealth / Family",
  3: "3rd — Courage / Siblings", 4: "4th — Home / Mother",
  5: "5th — Children / Intellect", 6: "6th — Health / Conflict",
  7: "7th — Marriage / Partners", 8: "8th — Transformation / Death",
  9: "9th — Fortune / Dharma", 10: "10th — Career / Public Life",
  11: "11th — Gains / Networks", 12: "12th — Loss / Spirituality",
};

function flattenById(nodes: EventCategoryNode[], out: Map<string, EventCategoryNode>) {
  for (const n of nodes) {
    out.set(n.id, n);
    if (n.children.length) flattenById(n.children, out);
  }
}

/** Keep a node if its own name matches, or any descendant matches. */
function filterTree(nodes: EventCategoryNode[], query: string): EventCategoryNode[] {
  if (!query.trim()) return nodes;
  const q = query.trim().toLowerCase();
  const walk = (n: EventCategoryNode): EventCategoryNode | null => {
    const selfMatch = n.name.toLowerCase().includes(q) || n.path.toLowerCase().includes(q);
    const children = n.children.map(walk).filter((c): c is EventCategoryNode => c !== null);
    if (selfMatch || children.length > 0) {
      return { ...n, children };
    }
    return null;
  };
  return nodes.map(walk).filter((n): n is EventCategoryNode => n !== null);
}

function toTreeNodes(nodes: EventCategoryNode[]): TreeNode[] {
  return nodes.map((n) => ({
    key: n.id,
    label: n.house_number
      ? `${n.name} · House ${n.house_number}${n.karaka_planet ? ` (${n.karaka_planet})` : ""}`
      : n.name,
    color: n.house_number ? "var(--gold-400)" : n.source === "manual" ? "var(--cyan-300)" : undefined,
    defaultOpen: false,
    children: toTreeNodes(n.children),
  }));
}

export default function CategoryTreePage() {
  const { data, isLoading, isError } = useEventCategoryTree();
  const updateCategory = useUpdateEventCategory();

  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
  const [houseInput, setHouseInput] = useState("");
  const [karakaInput, setKarakaInput] = useState("");

  const categories = data?.categories ?? [];

  const byId = useMemo(() => {
    const m = new Map<string, EventCategoryNode>();
    flattenById(categories, m);
    return m;
  }, [categories]);

  const filtered = useMemo(() => filterTree(categories, search), [categories, search]);
  const treeData = useMemo(() => toTreeNodes(filtered), [filtered]);

  const selected = selectedId ? byId.get(selectedId) : undefined;

  const totalNodes = byId.size;
  const taggedNodes = useMemo(
    () => Array.from(byId.values()).filter((n) => n.house_number != null).length,
    [byId],
  );

  const handleSelect = (key: string) => {
    setSelectedId(key);
    const node = byId.get(key);
    setHouseInput(node?.house_number ? String(node.house_number) : "");
    setKarakaInput(node?.karaka_planet ?? "");
  };

  const handleSave = () => {
    if (!selectedId) return;
    const houseNumber = houseInput.trim() ? parseInt(houseInput.trim(), 10) : null;
    updateCategory.mutate({
      id: selectedId,
      data: {
        house_number: Number.isFinite(houseNumber) ? houseNumber : null,
        karaka_planet: karakaInput.trim() || null,
      },
    });
  };

  return (
    <AppShell sectionColor="--section-research">
      <div className="flex flex-col gap-5 p-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Category Tree</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Open, source-taxonomy-driven event categories — auto-created from imported
              research data, optionally tagged with a Vedic house / karaka for astrology-specific
              pattern research.
            </p>
          </div>
          <div className="flex gap-2">
            <Badge tone="cyan">{totalNodes} categor{totalNodes === 1 ? "y" : "ies"}</Badge>
            <Badge tone="gold">{taggedNodes} Vedic-tagged</Badge>
          </div>
        </div>

        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search categories (e.g. Marriage, Career, Fame & Renown)…"
        />

        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5">
          <Card>
            {isLoading && <p className="text-sm text-slate-500 p-4">Loading category tree…</p>}
            {isError && (
              <p className="text-sm text-red-500 p-4">
                Could not load the category tree. Confirm the backend is running and the
                database migration/seed have been applied.
              </p>
            )}
            {!isLoading && !isError && treeData.length === 0 && (
              <p className="text-sm text-slate-500 p-4">
                {search ? "No categories match your search." : "No categories yet — import a research case to populate the tree."}
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
                Vedic Tagging
              </h2>
              {!selected && (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Select a category on the left to tag it with a classical bhava (house) and
                  karaka planet. Every category starts untagged — tagging is a manual research
                  step, nothing is pre-assumed.
                </p>
              )}
              {selected && (
                <>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Selected</p>
                    <p className="text-sm text-slate-900 dark:text-slate-100">{selected.path}</p>
                    {selected.source_doc_count != null && (
                      <p className="text-xs text-slate-400 mt-1">
                        {selected.source_doc_count} document(s) in source data
                      </p>
                    )}
                  </div>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-slate-600 dark:text-slate-300">House (1–12)</span>
                    <select
                      value={houseInput}
                      onChange={(e) => setHouseInput(e.target.value)}
                      className="h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-sm"
                    >
                      <option value="">— none —</option>
                      {Object.entries(HOUSE_NAMES).map(([num, label]) => (
                        <option key={num} value={num}>{label}</option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-slate-600 dark:text-slate-300">Karaka planet</span>
                    <Input
                      value={karakaInput}
                      onChange={setKarakaInput}
                      placeholder="e.g. venus, jupiter, saturn"
                    />
                  </label>

                  <Button onClick={handleSave} disabled={updateCategory.isPending}>
                    {updateCategory.isPending ? "Saving…" : "Save Tags"}
                  </Button>
                  {updateCategory.isError && (
                    <p className="text-xs text-red-500">Could not save — try again.</p>
                  )}
                  {updateCategory.isSuccess && (
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
