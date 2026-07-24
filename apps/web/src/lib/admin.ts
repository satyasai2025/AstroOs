/**
 * AstroOS — Admin API calls (TanStack Query integration)
 *
 * Wraps the /api/v1/admin/* endpoints: system health, module registry,
 * and user management (list, role change, suspend/activate). All of
 * these require an `admin`-role account on the backend
 * (apps/api/dependencies.py: require_admin) — a non-admin caller gets
 * a 403 from every one of these.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, adminTokenStore } from "./adminAuth";
import type {
  AdminUserListResponse,
  AdminUserSummary,
  ModuleRegistry,
  SystemStatus,
} from "./types";

export const adminKeys = {
  status: ["admin", "status"] as const,
  modules: ["admin", "modules"] as const,
  users: (statusFilter?: string, role?: string) =>
    ["admin", "users", statusFilter ?? "", role ?? ""] as const,
};

export function useSystemStatus() {
  return useQuery<SystemStatus>({
    queryKey: adminKeys.status,
    queryFn: () => adminApi.get<SystemStatus>("/api/v1/admin/status"),
    enabled: !!adminTokenStore.getAccess(),
    refetchInterval: 30_000,
  });
}

export function useModuleRegistry() {
  return useQuery<ModuleRegistry>({
    queryKey: adminKeys.modules,
    queryFn: () => adminApi.get<ModuleRegistry>("/api/v1/admin/module-registry"),
    enabled: !!adminTokenStore.getAccess(),
  });
}

export function useAdminUsers(statusFilter?: string, role?: string) {
  return useQuery<AdminUserListResponse>({
    queryKey: adminKeys.users(statusFilter, role),
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status_filter", statusFilter);
      if (role) params.set("role", role);
      params.set("limit", "100");
      const qs = params.toString();
      return adminApi.get<AdminUserListResponse>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
    },
    enabled: !!adminTokenStore.getAccess(),
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();
  return useMutation<AdminUserSummary, Error, { userId: string; role: string }>({
    mutationFn: ({ userId, role }) =>
      adminApi.patch<AdminUserSummary>(`/api/v1/admin/users/${userId}/role`, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useSuspendUser() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (userId) => adminApi.post<void>(`/api/v1/admin/users/${userId}/suspend`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useActivateUser() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (userId) => adminApi.post<void>(`/api/v1/admin/users/${userId}/activate`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}
