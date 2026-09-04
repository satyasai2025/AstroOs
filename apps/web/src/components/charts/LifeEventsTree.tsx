"use client";

import { useState } from "react";
import { useChartEvents, useCreateEvent, useDeleteEvent, type EventResponse } from "@/lib/events";
import { Badge, Button, Input, Select } from "@/components/ui";

const CATEGORIES = [
  { value: "career", label: "Career / Job Change" },
  { value: "promotion", label: "Promotion / Achievement" },
  { value: "marriage", label: "Marriage / Relationship" },
  { value: "relocation", label: "Relocation / Travel" },
  { value: "health", label: "Health / Surgery" },
  { value: "finance", label: "Financial Event / Gain" },
  { value: "education", label: "Education / Graduation" },
  { value: "family", label: "Family / Childbirth" },
  { value: "other", label: "Other" },
];

const CATEGORY_COLORS: Record<string, "success" | "gold" | "violet" | "danger" | "neutral"> = {
  career: "gold",
  promotion: "success",
  marriage: "violet",
  relocation: "gold",
  health: "danger",
  finance: "success",
  education: "violet",
  family: "violet",
  other: "neutral",
};

interface LifeEventsTreeProps {
  chartId: string;
  onEventAdded?: (event: EventResponse) => void;
}

export function LifeEventsTree({ chartId, onEventAdded }: LifeEventsTreeProps) {
  const { data, isLoading } = useChartEvents(chartId);
  const createEvent = useCreateEvent();
  const deleteEvent = useDeleteEvent();

  const [isAdding, setIsAdding] = useState(false);
  const [title, setTitle] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [category, setCategory] = useState("career");
  const [description, setDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const events = data?.events ?? [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    if (!title.trim() || !eventDate) {
      setErrorMessage("Please provide event title and date.");
      return;
    }

    try {
      const created = await createEvent.mutateAsync({
        chart_id: chartId,
        title: title.trim(),
        event_date: eventDate,
        category,
        description: description.trim() || null,
        is_verified: true,
      });

      // Reset form
      setTitle("");
      setEventDate("");
      setDescription("");
      setIsAdding(false);
      onEventAdded?.(created);
    } catch (err: any) {
      setErrorMessage(err?.detail || err?.message || "Failed to log life event.");
    }
  };

  const handleDelete = async (eventId: string) => {
    if (!window.confirm("Remove this life event?")) return;
    try {
      await deleteEvent.mutateAsync({ eventId, chartId });
    } catch (err) {
      console.error("Failed to delete event", err);
    }
  };

  return (
    <div className="obsidian-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Life Events &amp; Timing Verification
          </h3>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Log dated life milestones to verify correlation against Dasha periods and transits.
          </p>
        </div>
        <Button
          variant="gold"
          size="sm"
          onClick={() => setIsAdding((v) => !v)}
        >
          {isAdding ? "Cancel" : "+ Add Life Event"}
        </Button>
      </div>

      {isAdding && (
        <form onSubmit={handleCreate} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 p-4 space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-500">
            Log New Milestone
          </h4>

          {errorMessage && (
            <p className="text-xs text-red-500">{errorMessage}</p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              label="Event Title"
              placeholder="e.g. Joined Google as Senior Engineer"
              value={title}
              onChange={setTitle}
              required
            />
            <Input
              label="Event Date"
              type="date"
              value={eventDate}
              onChange={setEventDate}
              required
            />
            <Select
              label="Category"
              options={CATEGORIES}
              value={category}
              onChange={setCategory}
            />
          </div>

          <div>
            <label htmlFor="life-event-desc" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Description (Optional)
            </label>
            <input
              id="life-event-desc"
              aria-label="Description"
              type="text"
              className="field-input px-3 py-1.5 text-xs w-full"
              placeholder="Context or notes about this milestone..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsAdding(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" disabled={createEvent.isPending}>
              {createEvent.isPending ? "Saving…" : "Save Event"}
            </Button>
          </div>
        </form>
      )}

      {isLoading ? (
        <p className="text-xs py-4 text-center text-slate-700 dark:text-slate-300">Loading events…</p>
      ) : events.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 dark:border-slate-700 p-6 text-center">
          <p className="text-xs text-slate-700 dark:text-slate-300 font-medium">
            No life events logged for this native yet. Click &quot;+ Add Life Event&quot; to begin correlating milestones.
          </p>
        </div>
      ) : (
        <div className="relative border-l border-slate-300 dark:border-slate-800 ml-3 pl-4 space-y-4">
          {events
            .sort((a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime())
            .map((ev) => (
              <div key={ev.id} className="relative group">
                {/* Node dot on timeline tree */}
                <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-amber-500 ring-4 ring-slate-900" />
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{ev.title}</span>
                      <Badge tone={CATEGORY_COLORS[ev.category ?? "other"] ?? "neutral"}>
                        {ev.category ?? "milestone"}
                      </Badge>
                      <span className="text-[11px] font-mono text-slate-700 dark:text-slate-300 font-semibold">
                        {new Date(ev.event_date).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                      </span>
                    </div>
                    {ev.description && (
                      <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">{ev.description}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDelete(ev.id)}
                    className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-500 text-xs transition"
                    aria-label={`Delete event ${ev.title}`}
                    title="Delete milestone"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
