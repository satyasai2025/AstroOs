/**
 * AstroOS — Auth API calls (TanStack Query integration)
 *
 * All mutation functions return typed responses.
 * useCurrentUser() is a standard TanStack Query hook.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, tokenStore } from "./api";
import type {
  AuthResponse,
  ForgotPasswordPayload,
  LoginPayload,
  MessageResponse,
  RegisterPayload,
  ResetPasswordPayload,
  User,
  UpdateProfilePayload,
  ChangePasswordPayload,
} from "./types";

// ── Query keys ────────────────────────────────────────────────────────────────

export const authKeys = {
  me: ["auth", "me"] as const,
};

// ── Current user ──────────────────────────────────────────────────────────────

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: authKeys.me,
    queryFn: () => api.get<User>("/api/v1/auth/me"),
    enabled: !!tokenStore.getAccess(),
    retry: false,
  });
}

// ── Register ──────────────────────────────────────────────────────────────────

export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation<AuthResponse, Error, RegisterPayload>({
    mutationFn: (payload) => api.post<AuthResponse>("/api/v1/auth/register", payload),
    onSuccess: (data) => {
      tokenStore.set(data.tokens.access_token, data.tokens.refresh_token);
      queryClient.setQueryData(authKeys.me, data.user);
    },
  });
}

// ── Login ─────────────────────────────────────────────────────────────────────

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation<AuthResponse, Error, LoginPayload>({
    mutationFn: (payload) => api.post<AuthResponse>("/api/v1/auth/login", payload),
    onSuccess: (data) => {
      tokenStore.set(data.tokens.access_token, data.tokens.refresh_token);
      queryClient.setQueryData(authKeys.me, data.user);
    },
  });
}

// ── Forgot / reset password ─────────────────────────────────────────────────────

export function useForgotPassword() {
  return useMutation<MessageResponse, Error, ForgotPasswordPayload>({
    mutationFn: (payload) =>
      api.post<MessageResponse>("/api/v1/auth/forgot-password", payload),
  });
}

export function useResetPassword() {
  return useMutation<MessageResponse, Error, ResetPasswordPayload>({
    mutationFn: (payload) =>
      api.post<MessageResponse>("/api/v1/auth/reset-password", payload),
  });
}

// ── Logout ────────────────────────────────────────────────────────────────────

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, void>({
    mutationFn: () => api.post<void>("/api/v1/auth/logout", {}),
    onSettled: () => {
      tokenStore.clear();
      queryClient.clear();
    },
  });
}

// ── Profile update ────────────────────────────────────────────────────────────

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation<User, Error, UpdateProfilePayload>({
    mutationFn: (payload) =>
      api.patch<User>("/api/v1/auth/me", payload),
    onSuccess: (data) => {
      queryClient.setQueryData(authKeys.me, data);
    },
  });
}

// ── Password change ───────────────────────────────────────────────────────────

export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation<MessageResponse, Error, ChangePasswordPayload>({
    mutationFn: (payload) =>
      api.post<MessageResponse>("/api/v1/auth/me/change-password", payload),
    onSuccess: () => {
      tokenStore.clear();
      queryClient.clear();
    },
  });
}
