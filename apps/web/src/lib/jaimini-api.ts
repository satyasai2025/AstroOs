/**
 * Jaimini API client — thin wrappers around the generic `api` client for
 * the Jaimini bundle/argala endpoints (apps/api/routers/jaimini.py).
 */

import { api } from "@/lib/api";
import type {
  JaiminiArgalaRequest,
  JaiminiArgalaResponse,
  JaiminiBundleRequest,
  JaiminiBundleResponse,
} from "@/lib/types";

export function computeJaiminiBundle(
  params: JaiminiBundleRequest,
): Promise<JaiminiBundleResponse> {
  return api.post<JaiminiBundleResponse>("/api/v1/jaimini/bundle", params);
}

export function computeJaiminiArgala(
  params: JaiminiArgalaRequest,
): Promise<JaiminiArgalaResponse> {
  return api.post<JaiminiArgalaResponse>("/api/v1/jaimini/argala", params);
}
