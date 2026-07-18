/**
 * AstroOS TypeScript SDK
 *
 * Official TypeScript client for the AstroOS Vedic Astrology API.
 */

import { z } from "zod";
import { ChartReportRequestSchema, HealthResponseSchema } from "./schemas";

export interface SdkConfig {
  baseUrl?: string;
  apiKey?: string;
  accessToken?: string;
  timeout?: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  version: string;
  requestId: string;
}

export interface ChartRequest {
  birthDatetimeUtc: string;
  latitude: number;
  longitude: number;
  ayanamsa?: string;
  houseSystem?: string;
}

export interface EventRecord {
  id: string;
  chartId: string;
  eventDate: string;
  title: string;
  category?: string;
  isVerified: boolean;
}

export type ChartReportRequest = z.infer<typeof ChartReportRequestSchema>;
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

// Re-export schemas for external use
export * from "./schemas";

/**
 * AstroOS API client.
 */
export class AstroOSClient {
  private config: Required<SdkConfig>;

  constructor(config: SdkConfig = {}) {
    this.config = {
      baseUrl: config.baseUrl || "https://api.astroos.dev/v1",
      apiKey: config.apiKey || "",
      accessToken: config.accessToken || "",
      timeout: config.timeout || 30,
    };
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (this.config.apiKey) h["x-api-key"] = this.config.apiKey;
    if (this.config.accessToken) h["Authorization"] = `Bearer ${this.config.accessToken}`;
    return h;
  }

  private async get<T>(path: string, params: Record<string, string> = {}): Promise<ApiResponse<T>> {
    const urlObj = new URL(`${this.config.baseUrl}/${path.replace(/^\//, "")}`);
    Object.entries(params).forEach(([k, v]) => urlObj.searchParams.set(k, v));
    const response = await fetch(urlObj.toString(), {
      method: "GET",
      headers: this.headers(),
    });
    return response.json();
  }

  private async post<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    const url = `${this.config.baseUrl}/${path.replace(/^\//, "")}`;
    const response = await fetch(url, {
      method: "POST",
      headers: this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return response.json();
  }

  private async download(path: string, body?: unknown): Promise<Blob> {
    const url = `${this.config.baseUrl}/${path.replace(/^\//, "")}`;
    const response = await fetch(url, {
      method: "POST",
      headers: { Accept: "application/octet-stream", ...this.headers() },
      body: body ? JSON.stringify(body) : undefined,
    });
    return response.blob();
  }

  // Auth methods
  auth = {
    register: (email: string, password: string, displayName: string) =>
      this.post("/auth/register", { email, password, display_name: displayName }),

    login: (email: string, password: string) =>
      this.post("/auth/login", { email, password }),

    me: () => this.get("/auth/me"),
  };

  // Chart methods
  chart = {
    compute: (req: ChartRequest) =>
      this.post("/horoscope/d1", {
        birth_datetime_utc: req.birthDatetimeUtc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa || "lahiri",
        house_system: req.houseSystem || "W",
      }),
  };

  // Divisional methods
  divisional = {
    computeAll: (req: ChartRequest) =>
      this.post("/divisional/all", {
        birth_datetime_utc: req.birthDatetimeUtc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa || "lahiri",
        house_system: req.houseSystem || "W",
      }),

    compute: (varga: string, req: ChartRequest) =>
      this.post(`/divisional/${varga}`, {
        birth_datetime_utc: req.birthDatetimeUtc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa || "lahiri",
        house_system: req.houseSystem || "W",
      }),
  };

  // Dasha methods
  dasha = {
    compute: (system: string, req: ChartRequest, maxDepth = 3) =>
      this.post(`/dasha/${system}`, {
        birth_datetime_utc: req.birthDatetimeUtc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa || "lahiri",
        house_system: req.houseSystem || "W",
        max_depth: maxDepth,
      }),
  };

  // Event methods
  events = {
    list: (chartId: string, category?: string) => {
      const params: Record<string, string> = { chart_id: chartId };
      if (category) params.category = category;
      return this.get("/events", params);
    },

    create: (event: { chartId: string; eventDate: string; title: string; category?: string }) =>
      this.post("/events", {
        chart_id: event.chartId,
        event_date: event.eventDate,
        title: event.title,
        category: event.category,
      }),

    delete: (eventId: string) => this.post(`/events/${eventId}/delete`),
  };

  // Report methods
  reports = {
    generateChart: (req: ChartReportRequest) =>
      this.post("/report/chart", {
        birth_datetime_utc: req.birth_datetime_utc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa,
        house_system: req.house_system,
      }),

    generatePdf: async (req: ChartReportRequest): Promise<Blob> => {
      const blob = await this.download("/report/chart/pdf", {
        birth_datetime_utc: req.birth_datetime_utc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa,
        house_system: req.house_system,
      });
      return blob;
    },

    generateCsv: (req: ChartReportRequest) =>
      this.get("/report/chart/csv", {
        birth_datetime_utc: req.birth_datetime_utc,
        latitude: String(req.latitude),
        longitude: String(req.longitude),
        ayanamsa: req.ayanamsa,
        house_system: req.house_system,
      }),

    listTemplates: () => this.get<string[]>("/report/templates"),
  };

  // AI methods
  ai = {
    explain: (topic: string, sourceData: Record<string, unknown>) =>
      this.post("/ai/explain", { topic, source_data: sourceData }),
  };

  // Workflow methods
  workflow = {
    analyze: (req: ChartRequest & { researchProjectId?: string }) =>
      this.post("/workflow/analyze", {
        birth_datetime_utc: req.birthDatetimeUtc,
        latitude: req.latitude,
        longitude: req.longitude,
        ayanamsa: req.ayanamsa || "lahiri",
        house_system: req.houseSystem || "W",
        research_project_id: req.researchProjectId,
      }),
  };

  // Health check
  health = {
    check: () => this.get<HealthResponse>("/../healthz"),
  };
}