/**
 * AstroOS Mobile — Configuration
 *
 * Defaults to localhost:8000 for local-first development.
 * Override via app Settings screen for remote instances.
 */
export const Config = {
  /** AstroOS API base URL (default: local-first) */
  apiBaseUrl: __DEV__
    ? 'http://localhost:8000/api/v1'
    : 'http://localhost:8000/api/v1',

  /** API key (set via Settings screen) */
  apiKey: '',

  /** Application info */
  appVersion: '2.3.0',
  appName: 'AstroOS',

  /** Offline cache TTL in seconds */
  cacheTtlSeconds: 86400,

  /** API request timeout in milliseconds */
  requestTimeoutMs: 15000,

  /** Push notifications (optional — feature-flagged) */
  pushEnabled: false,
};
