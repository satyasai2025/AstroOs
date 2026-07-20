/**
 * AstroOS Mobile — API Client
 *
 * Connects to the local AstroOS API. All requests go to localhost:8000
 * by default. Falls back to cached data when offline.
 */
import { Config } from '../config';

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = Config.apiBaseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, params } = opts;
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
    if (Config.apiKey) {
      headers['x-api-key'] = Config.apiKey;
    }

    const response = await fetch(url.toString(), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorBody = await response.text().catch(() => '');
      throw new ApiError(response.status, response.statusText, errorBody);
    }

    return response.json() as Promise<T>;
  }

  // -- Chart API --

  async computeChart(data: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa?: string;
    house_system?: string;
  }) {
    return this.request<Record<string, unknown>>('/horoscope/d1', {
      method: 'POST',
      body: data,
    });
  }

  async computeDivisional(varga: string, data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>(`/divisional/${varga}`, {
      method: 'POST',
      body: data,
    });
  }

  // -- Dasha API --

  async computeDasha(system: string, data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>(`/dasha/${system}`, {
      method: 'POST',
      body: data,
    });
  }

  // -- Yoga API --

  async evaluateYogas(data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>('/yoga/evaluate', {
      method: 'POST',
      body: data,
    });
  }

  async evaluateYogasWithStrength(data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>('/yoga/evaluate/with-strength', {
      method: 'POST',
      body: data,
    });
  }

  // -- AI API --

  async getChartSummary(data: Record<string, unknown>) {
    return this.request<Record<string, unknown>>('/ai/chart-summary', {
      method: 'POST',
      body: data,
    });
  }

  // -- Health --

  async health() {
    return this.request<{ status: string }>('/health/live');
  }
}

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: string,
  ) {
    super(`API ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

export const api = new ApiClient();
export { ApiClient, ApiError };
