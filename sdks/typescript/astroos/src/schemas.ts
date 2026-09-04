// AstroOS TypeScript SDK — Schemas (Phase G)

import { z } from "zod";

export const ChartReportRequestSchema = z.object({
  birth_datetime_utc: z.string(),
  latitude: z.number(),
  longitude: z.number(),
  ayanamsa: z.string().default("lahiri"),
  house_system: z.string().default("W"),
  title: z.string().optional(),
  subject_name: z.string().optional(),
});

export const ChartReportResponseSchema = z.object({
  title: z.string(),
  subject_name: z.string(),
  sections: z.array(z.record(z.unknown())),
});

export const HealthResponseSchema = z.object({
  status: z.string(),
  version: z.string().optional(),
  environment: z.string().optional(),
  ephemeris: z
    .object({
      mode: z.string().optional(),
      official_data: z.boolean().optional(),
      path: z.string().optional(),
      se1_files: z.array(z.string()).optional(),
      test_longitude: z.number().optional(),
      error: z.string().nullable().optional(),
    })
    .optional(),
});

export const MetricsResponseSchema = z.object({
  chart_computation_duration_seconds: z.record(z.unknown()),
  api_request_duration_seconds: z.record(z.unknown()),
  db_pool_usage: z.record(z.unknown()),
});

export type ChartReportRequest = z.infer<typeof ChartReportRequestSchema>;
export type ChartReportResponse = z.infer<typeof ChartReportResponseSchema>;
export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type MetricsResponse = z.infer<typeof MetricsResponseSchema>;