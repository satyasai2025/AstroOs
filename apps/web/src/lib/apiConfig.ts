/**
 * AstroOS — Production-Safe API URL & Environment Configuration
 *
 * Validates and resolves API base URLs across SSR, client-side, dev, and production.
 */

export function getApiBaseUrl(): string {
  // Check NEXT_PUBLIC_API_URL
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL;
  if (configuredUrl && configuredUrl.trim().length > 0) {
    // Strip trailing slashes
    return configuredUrl.replace(/\/+$/, "");
  }

  // If in browser context and no env var, default to relative or localhost
  if (typeof window !== "undefined") {
    // In dev on localhost:3000 -> default to backend on 8000
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
    // In production hosted on same domain / reverse proxy -> relative root
    return "";
  }

  // Server-side default
  return process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";
}

export function getValidatedExcelExportUrl(path: string, params: Record<string, string>): string {
  const base = getApiBaseUrl();
  const searchParams = new URLSearchParams(params);
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${cleanPath}?${searchParams.toString()}`;
}
