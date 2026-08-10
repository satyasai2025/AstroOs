/**
 * Dasha API client — thin wrappers around the generic `api` client for the
 * dasha-system registry and per-system compute endpoints
 * (apps/api/routers/dasha.py).
 */

import { api } from "@/lib/api";
import type {
  AyanamsaCode,
  DashaSystemCode,
  DashaSystemInfo,
  DashaTreeResponse,
  HouseSystemCode,
} from "@/lib/types";

export function getDashaSystems(): Promise<DashaSystemInfo[]> {
  return api.get<DashaSystemInfo[]>("/api/v1/dasha/systems");
}

export function computeDasha(
  system: DashaSystemCode,
  params: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa: AyanamsaCode;
    house_system: HouseSystemCode;
    max_depth?: number;
    /** Defaults true (matches DashaRequest). Pass false for a transient
     *  compute — e.g. browsing a different system in the switcher —
     *  to avoid writing a duplicate birth_charts row. */
    persist?: boolean;
  },
): Promise<DashaTreeResponse> {
  return api.post<DashaTreeResponse>(`/api/v1/dasha/${system}`, params);
}
