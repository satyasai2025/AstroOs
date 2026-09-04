"use client";

import { useState } from "react";
import { Button, Card, Input, Select, type SelectOption } from "@/components/ui";
import { TreeLevelBuilder } from "./TreeLevelBuilder";
import type {
  ResearchCaseBatchImport,
  ResearchLifeEvent,
  ResearchPerson,
} from "@/lib/types";

const GENDER_OPTIONS: SelectOption[] = [
  { value: "Male", label: "Male" },
  { value: "Female", label: "Female" },
  { value: "Other", label: "Other" },
];
const IMPORTANCE_OPTIONS: SelectOption[] = [
  { value: "Major", label: "Major" },
  { value: "Moderate", label: "Moderate" },
  { value: "Minor", label: "Minor" },
];

interface DraftEvent {
  key: string;
  event_date: string;
  category_path: string[] | null;
  event_type_path: string[] | null;
  severity: "Major" | "Moderate" | "Minor";
  source: string;
  description: string;
}

function newDraftEvent(): DraftEvent {
  return {
    key: Math.random().toString(36).slice(2),
    event_date: "",
    category_path: null,
    event_type_path: null,
    severity: "Moderate",
    source: "Manual Entry",
    description: "",
  };
}

export interface CaseManualEntryFormProps {
  onSubmit: (payload: ResearchCaseBatchImport) => void;
  submitting?: boolean;
}

/**
 * Manual single-case entry: a person plus a dynamic list of life events,
 * each built with the open Category Tree and Event Tree (TreeLevelBuilder,
 * up to 6 levels each) instead of the old fixed EventType dropdown. Builds
 * the same ResearchCaseBatchImport shape the JSON-upload flow already
 * sends to /research/cases/import, so it feeds into that flow's existing
 * validate/import state machine rather than duplicating it.
 */
export function CaseManualEntryForm({ onSubmit, submitting }: CaseManualEntryFormProps) {
  const [name, setName] = useState("");
  const [gender, setGender] = useState<"Male" | "Female" | "Other">("Male");
  const [dob, setDob] = useState("");
  const [tob, setTob] = useState("");
  const [place, setPlace] = useState("");
  const [country, setCountry] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [source, setSource] = useState("Self-report");
  const [notes, setNotes] = useState("");

  const [events, setEvents] = useState<DraftEvent[]>([newDraftEvent()]);

  const updateEvent = (key: string, patch: Partial<DraftEvent>) => {
    setEvents((prev) => prev.map((e) => (e.key === key ? { ...e, ...patch } : e)));
  };

  const removeEvent = (key: string) => {
    setEvents((prev) => (prev.length > 1 ? prev.filter((e) => e.key !== key) : prev));
  };

  const canSubmit =
    name.trim() && dob.trim() && place.trim() && latitude.trim() && longitude.trim();

  const handleSubmit = () => {
    if (!canSubmit) return;
    const person: ResearchPerson = {
      name: name.trim(),
      gender,
      dob: dob.trim(),
      tob: tob.trim() || null,
      place: place.trim(),
      country: country.trim() || null,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      timezone: timezone.trim() || "UTC",
      source: source.trim() || "Self-report",
    };

    const life_events: ResearchLifeEvent[] = events
      .filter((e) => e.event_date.trim())
      .map((e) => {
        const evt: ResearchLifeEvent = {
          type: "Other",
          event_date: e.event_date.trim(),
          category: e.category_path ? e.category_path.join(" / ") : "Other",
          severity: e.severity,
          source: e.source.trim() || "Manual Entry",
          description: e.description.trim() || null,
        };
        if (e.category_path && e.category_path.length > 0) {
          evt.category_path = e.category_path;
        }
        if (e.event_type_path && e.event_type_path.length > 0) {
          evt.event_type_path = e.event_type_path;
        }
        return evt;
      });

    onSubmit({
      cases: [
        {
          person,
          ayanamsa: "lahiri",
          house_system: "P",
          life_events: life_events.length > 0 ? life_events : [],
          research_notes: notes.trim() || null,
          source_batch: "manual-entry",
        },
      ],
      generate_ids: true,
    });
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <div className="p-4 flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Person Details</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Basic information about the individual.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input label="Full Name" required value={name} onChange={setName} placeholder="Enter full name" />
              <Select label="Gender" options={GENDER_OPTIONS} value={gender} onChange={(v) => setGender(v as typeof gender)} />
              <Input label="Date of Birth" required value={dob} onChange={setDob} placeholder="YYYY-MM-DD" />
              <Input label="Time of Birth" required value={tob} onChange={setTob} placeholder="HH:MM (24h)" />
              <Input label="Birth Place" required value={place} onChange={setPlace} placeholder="City, State" />
              <Input label="Country" value={country} onChange={setCountry} placeholder="Country" />
              <Input label="Timezone" required value={timezone} onChange={setTimezone} placeholder="Asia/Kolkata" />
              <Input label="Latitude" required value={latitude} onChange={setLatitude} placeholder="e.g. 28.6139" />
              <Input label="Longitude" required value={longitude} onChange={setLongitude} placeholder="e.g. 77.2090" />
              <Input label="Source" value={source} onChange={setSource} placeholder="Interview, Certificate, Self-report…" />
            </div>
            <p className="text-[11px] text-slate-400">* Required fields</p>
          </div>
        </Card>

        <Card>
          <div className="p-4 flex flex-col gap-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Case Notes (Optional)</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Additional information for reference.</p>
            </div>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-slate-700 dark:text-slate-300 font-medium text-xs">Notes</span>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any additional notes about this case…"
                rows={6}
                className="w-full rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </label>
          </div>
        </Card>
      </div>

      <Card>
        <div className="p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Life Events</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Add life events associated with this individual.</p>
            </div>
            <Button size="sm" variant="secondary" onClick={() => setEvents((prev) => [...prev, newDraftEvent()])}>
              + Add Event
            </Button>
          </div>

          {events.map((evt, i) => (
            <div key={evt.key} className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-cyan-600 dark:text-cyan-400">Event #{i + 1}</span>
                {events.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeEvent(evt.key)}
                    className="text-xs text-slate-400 hover:text-red-500"
                  >
                    Remove
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input
                  label="Event Date"
                  value={evt.event_date}
                  onChange={(v) => updateEvent(evt.key, { event_date: v })}
                  placeholder="YYYY-MM-DD"
                />
                <Select
                  label="Importance"
                  options={IMPORTANCE_OPTIONS}
                  value={evt.severity}
                  onChange={(v) => updateEvent(evt.key, { severity: v as DraftEvent["severity"] })}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div className="text-slate-700 dark:text-slate-300 font-medium text-xs mb-1.5">Category Path</div>
                  <TreeLevelBuilder
                    tree="category"
                    value={evt.category_path}
                    onChange={(path) => updateEvent(evt.key, { category_path: path })}
                  />
                </div>
                <div>
                  <div className="text-slate-700 dark:text-slate-300 font-medium text-xs mb-1.5">Event Type Path</div>
                  <TreeLevelBuilder
                    tree="event"
                    value={evt.event_type_path}
                    onChange={(path) => updateEvent(evt.key, { event_type_path: path })}
                  />
                </div>
              </div>
              <Input
                label="Description (optional)"
                value={evt.description}
                onChange={(v) => updateEvent(evt.key, { description: v })}
                placeholder="Describe the event in detail…"
              />
            </div>
          ))}

          <div className="rounded-lg bg-cyan-50 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-900/50 p-3 text-xs text-slate-600 dark:text-slate-300">
            Pick from the dropdowns to build category and event-type paths up to 6 levels deep.
            If the option you need doesn&apos;t exist yet, click &quot;+ New&quot; on that level to type it in — it&apos;s created automatically on save.
          </div>
        </div>
      </Card>

      <Button onClick={handleSubmit} disabled={!canSubmit || submitting} fullWidth>
        {submitting ? "Submitting…" : "Validate Case"}
      </Button>
    </div>
  );
}
