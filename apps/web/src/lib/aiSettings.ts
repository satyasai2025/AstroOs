/**
 * AstroOS — AI Settings (per-user BYOK) data hooks
 * Mirrors the useCurrentUser / useUpdateProfile pattern in ./auth.ts.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, tokenStore } from "./api";
import type {
  AISettings,
  TestAISettingsPayload,
  TestConnectionResponse,
  UpdateAISettingsPayload,
} from "./types";

const aiSettingsKeys = {
  mine: ["ai-settings", "me"] as const,
};

export function useAISettings() {
  return useQuery<AISettings>({
    queryKey: aiSettingsKeys.mine,
    queryFn: () => api.get<AISettings>("/api/v1/ai/settings"),
    enabled: !!tokenStore.getAccess(),
  });
}

export function useUpdateAISettings() {
  const queryClient = useQueryClient();
  return useMutation<AISettings, Error, UpdateAISettingsPayload>({
    mutationFn: (payload) => api.put<AISettings>("/api/v1/ai/settings", payload),
    onSuccess: (data) => {
      queryClient.setQueryData(aiSettingsKeys.mine, data);
    },
  });
}

export function useTestAIConnection() {
  return useMutation<TestConnectionResponse, Error, TestAISettingsPayload>({
    mutationFn: (payload) => api.post<TestConnectionResponse>("/api/v1/ai/settings/test", payload),
  });
}
