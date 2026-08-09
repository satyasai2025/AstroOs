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

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: string,
  ) {
    super(`AstroOS API ${status}: ${statusText}`);
    this.name = "ApiError";
  }
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
      baseUrl: config.baseUrl || "https://api.astroos.dev/api/v1",
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

  private async request(
    method: string,
    path: string,
    opts: { body?: unknown; params?: Record<string, string>; accept?: string } = {},
  ): Promise<Response> {
    const urlObj = path.startsWith("http")
      ? new URL(path)
      : new URL(`${this.config.baseUrl}/${path.replace(/^\//, "")}`);
    Object.entries(opts.params ?? {}).forEach(([k, v]) => urlObj.searchParams.set(k, v));

    const headers = this.headers();
    if (opts.accept) headers.Accept = opts.accept;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.config.timeout * 1000);

    try {
      return await fetch(urlObj.toString(), {
        method,
        headers,
        body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
        signal: controller.signal,
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        throw new ApiError(0, "timeout", `Request timed out after ${this.config.timeout}s`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  private async parseJson<T>(response: Response): Promise<ApiResponse<T>> {
    const text = await response.text();
    let body: unknown;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      body = null;
    }

    if (!response.ok) {
      const message =
        (body && typeof body === "object" && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : "") || response.statusText;
      throw new ApiError(response.status, response.statusText, message);
    }

    const data = body as T;
    if (data && typeof data === "object" && "success" in (data as object)) {
      return data as unknown as ApiResponse<T>;
    }
    return { success: true, data, version: "", requestId: "" };
  }

  private async get<T>(path: string, params: Record<string, string> = {}): Promise<ApiResponse<T>> {
    const response = await this.request("GET", path, { params });
    return this.parseJson<T>(response);
  }

  private async post<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    const response = await this.request("POST", path, { body });
    return this.parseJson<T>(response);
  }

  private async delete<T>(path: string): Promise<ApiResponse<T>> {
    const response = await this.request("DELETE", path);
    return this.parseJson<T>(response);
  }

  private async download(path: string, body?: unknown, accept = "application/pdf"): Promise<Blob> {
    const response = await this.request("POST", path, { body, accept });
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText, await response.text());
    }
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

    delete: (eventId: string) => this.delete(`/events/${eventId}`),
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

    generateCsv: async (req: ChartReportRequest): Promise<ApiResponse<string>> => {
      const response = await this.request("POST", "/report/chart/csv", {
        body: {
          birth_datetime_utc: req.birth_datetime_utc,
          latitude: req.latitude,
          longitude: req.longitude,
          ayanamsa: req.ayanamsa,
          house_system: req.house_system,
        },
      });
      if (!response.ok) {
        throw new ApiError(response.status, response.statusText, await response.text());
      }
      return { success: true, data: await response.text(), version: "", requestId: "" };
    },

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
    check: () => {
      const root = new URL(this.config.baseUrl).origin;
      return this.get<HealthResponse>(`${root}/api/healthz`);
    },
  };
}