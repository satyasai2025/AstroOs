/**
 * AstroOS — Billing & Premium Client API (Phase 8)
 *
 * Connects frontend screens to backend Plan, Subscription, Payment, Entitlement, and Quota APIs.
 * Supports INR first-class currency, GST/tax breakdowns, and customer portal sessions.
 */

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

export type BillingCycle = "monthly" | "yearly";
export type PricingCurrency = "INR" | "USD";

export interface PricingPlanDetail {
  plan_code: string;
  name: string;
  description: string;
  currency: PricingCurrency;
  currency_symbol: string;
  tax_rate: number;
  tax_name: string;
  monthly_base_amount: number;
  monthly_base_formatted: string;
  monthly_tax_amount: number;
  monthly_tax_formatted: string;
  monthly_total_amount: number;
  monthly_total_formatted: string;
  yearly_base_amount: number;
  yearly_base_formatted: string;
  yearly_tax_amount: number;
  yearly_tax_formatted: string;
  yearly_total_amount: number;
  yearly_total_formatted: string;
  saved_horoscopes_limit: number | null;
  research_projects_monthly_limit: number | null;
  features: string[];
}

export interface PricingCatalogResponse {
  currency: PricingCurrency;
  currency_symbol: string;
  supported_currencies: PricingCurrency[];
  tax_rate: number;
  tax_name: string;
  plans: PricingPlanDetail[];
}

export interface DashboardSummary {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
  status: string;
  plan_code: string;
  plan_name: string;
  subscription_status: string | null;
  period_start: string | null;
  period_end: string | null;
  is_in_grace_period: boolean;
  saved_horoscopes_count: number;
  saved_horoscopes_limit: number | null;
  research_runs_used: number;
  research_runs_limit: number | null;
  max_storage_mb: number | null;
  recent_payments: PaymentRecord[];
  total_payments_count: number;
}

export interface SubscriptionInfo {
  id: string;
  user_id: string;
  plan_id: string;
  status: "trialing" | "active" | "past_due_cancelled" | "expired";
  current_period_start: string;
  current_period_end: string;
  trial_end: string | null;
  cancel_at_period_end: boolean;
}

export interface PlanLimitsInfo {
  saved_horoscopes: number | null;
  research_projects_monthly: number | null;
  max_storage_mb: number | null;
}

export interface EntitlementsInfo {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_run: boolean;
  can_export: boolean;
}

export interface PaymentRecord {
  id: string;
  user_id: string;
  plan_id: string | null;
  provider: string;
  amount: number;
  base_amount: number | null;
  tax_amount: number | null;
  tax_rate: number | null;
  currency: string;
  status: "pending" | "succeeded" | "failed" | "refunded" | "cancelled";
  payment_method: string | null;
  receipt_url: string | null;
  created_at: string;
}

export interface PaymentHistoryResponse {
  items: PaymentRecord[];
  total: number;
}

export interface CheckoutSessionResponse {
  session_id: string;
  checkout_url: string;
  provider: string;
  plan_code: string;
  currency: string;
  base_amount: number;
  tax_amount: number;
  tax_rate: number;
  total_amount: number;
  amount: number;
}

export interface CustomerPortalResponse {
  portal_url: string;
  provider: string;
}

export interface NotificationPreferences {
  user_id: string;
  billing_notifications: boolean;
  security_alerts: boolean;
  quota_warnings: boolean;
  product_updates: boolean;
}

// ── API Methods ───────────────────────────────────────────────────────────────

export async function fetchPricingCatalog(currency: PricingCurrency = "INR"): Promise<PricingCatalogResponse> {
  return api.get<PricingCatalogResponse>(`/api/v1/payments/pricing?currency=${currency}`);
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return api.get<DashboardSummary>("/api/v1/dashboard/summary");
}

export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: () => fetchDashboardSummary(),
    enabled: typeof window !== "undefined" && !!tokenStore.getAccess(),
  });
}

export async function fetchMySubscription(): Promise<SubscriptionInfo | null> {
  try {
    return await api.get<SubscriptionInfo>("/api/v1/subscriptions/me");
  } catch {
    return null;
  }
}

export async function fetchMyLimits(): Promise<PlanLimitsInfo> {
  try {
    return await api.get<PlanLimitsInfo>("/api/v1/entitlements/me/limits");
  } catch {
    return {
      saved_horoscopes: 5,
      research_projects_monthly: 0,
      max_storage_mb: 50,
    };
  }
}

export async function fetchMyEntitlements(): Promise<EntitlementsInfo> {
  try {
    return await api.get<EntitlementsInfo>("/api/v1/entitlements/me");
  } catch {
    return {
      can_view: true,
      can_create: true,
      can_edit: false,
      can_run: false,
      can_export: false,
    };
  }
}

export async function initiateCheckout(params: {
  plan_code: string;
  billing_cycle: BillingCycle;
  currency?: PricingCurrency;
  success_url?: string;
  cancel_url?: string;
}): Promise<CheckoutSessionResponse> {
  return api.post<CheckoutSessionResponse>("/api/v1/payments/checkout", {
    plan_code: params.plan_code,
    billing_cycle: params.billing_cycle,
    currency: params.currency || "INR",
    success_url: params.success_url || `${window.location.origin}/settings/billing?checkout=success`,
    cancel_url: params.cancel_url || `${window.location.origin}/pricing?checkout=cancelled`,
  });
}

export async function initiateCustomerPortal(): Promise<CustomerPortalResponse> {
  return api.post<CustomerPortalResponse>("/api/v1/payments/portal", {
    return_url: `${window.location.origin}/settings/billing`,
  });
}

export async function fetchPaymentHistory(limit = 20, offset = 0): Promise<PaymentHistoryResponse> {
  try {
    return await api.get<PaymentHistoryResponse>(`/api/v1/payments/history?limit=${limit}&offset=${offset}`);
  } catch {
    return { items: [], total: 0 };
  }
}

export async function fetchNotificationPreferences(): Promise<NotificationPreferences> {
  return api.get<NotificationPreferences>("/api/v1/notifications/preferences");
}

export async function updateNotificationPreferences(
  prefs: Partial<Pick<NotificationPreferences, "quota_warnings" | "product_updates">>
): Promise<NotificationPreferences> {
  return api.put<NotificationPreferences>("/api/v1/notifications/preferences", prefs);
}

export async function confirmLatestMockPayment(): Promise<any> {
  return api.post("/api/v1/payments/confirm-mock", {});
}
