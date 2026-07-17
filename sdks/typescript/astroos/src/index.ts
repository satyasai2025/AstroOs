/**
 * AstroOS TypeScript SDK
 *
 * Official TypeScript client for the AstroOS Vedic Astrology API.
 */

export interface SdkConfig {
  baseUrl?: string;
  apiKey?: string;
  accessToken?: string;
  timeout?: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
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

  private async request<T>(
    method: string,
    path: string,
    body?: any
  ): Promise<ApiResponse<T>> {
    const url = `${this.config.baseUrl}/${path.replace(/^\//, "")}`;
    const response = await fetch(url, {
      method,
      headers: this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return response.json();
  }

  async computeChart(req: ChartRequest): Promise<ApiResponse> {
    return this.request("POST", "/horoscope/d1", {
      birth_datetime_utc: req.birthDatetimeUtc,
      latitude: req.latitude,
      longitude: req.longitude,
      ayanamsa: req.ayanamsa || "lahiri",
      house_system: req.houseSystem || "W",
    });
  }

  async listEvents(chartId: string, category?: string): Promise<ApiResponse> {
    const params = new URLSearchParams({ chart_id: chartId });
    if (category) params.set("category", category);
    return this.request("GET", `/events?${params}`);
  }

  async createEvent(event: {
    chartId: string;
    eventDate: string;
    title: string;
    category?: string;
  }): Promise<ApiResponse> {
    return this.request("POST", "/events", {
      chart_id: event.chartId,
      event_date: event.eventDate,
      title: event.title,
      category: event.category,
    });
  }

  async health(): Promise<ApiResponse> {
    return this.request("GET", "/../healthz");
  }
}
