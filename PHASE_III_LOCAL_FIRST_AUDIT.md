# Phase III "Lakshmi" — Local-First Mandate Audit

**Audited:** 2026-07-20  
**Auditor:** Governance Office (Governance)  
**Reference:** `CLAUDE_START_HERE.md` local-first rules, `ASTROOS_PHASE_III_V2_3_ROADMAP.md`, `tasks_phase3_data.json`  
**Status:** REDESIGN REQUIRED — 3 workstreams fail, 3 conditional, 2 pass

---

## Local-First Mandate (from CLAUDE_START_HERE.md and prior governance rulings)

| Rule | Source |
|---|---|
| Docker, Kubernetes, Helm permanently removed from pipeline | Phase II scope amendment (2026-07-20) |
| No cloud deployment (AWS/GCP/Azure) required | CLAUDE_START_HERE.md, ADR-GOV-001 |
| No mandatory external services; everything runs on single machine | CLAUDE_START_HERE.md |
| Redis optional (JWT denylist only) | CLAUDE_START_HERE.md, Governance v2.1 audit |
| PostgreSQL only required data store | CLAUDE_START_HERE.md |
| Single-user personal research platform default | CLAUDE_START_HERE.md |
| Enterprise/multi-user features must be optional/pluggable, not required | Governance v2.1 audit |

---

## 1. Mobile Apps (iOS + Android)

**Tasks:** 6 (iOS Core), 7 (Android Core), 8 (Polish & Store), 19 (Device Lab QA)  
**Assessment:** CONDITIONAL

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| React Native offline-first SQLite | Yes | Runs entirely on device. Fully compatible. |
| Push notifications (FCM / APNs) | **No** | FCM (Google Firebase) and APNs (Apple) are external cloud services. The app cannot deliver push notifications without reaching these services. |
| In-app purchases | N/A (distribution) | App Store / Play Store requirement for monetization. This is a distribution-channel concern, not a runtime dependency. The app works without purchases. |
| Offline bidirectional sync | Conditionally | Sync between mobile device and the user's own local PostgreSQL instance requires a reachable server endpoint. Local-first compatible IF the sync target is the user's own machine (not a cloud-hosted sync relay). |
| RTL testing, device lab validation | Yes | Pure QA. No infrastructure concerns. |

### Conflicts with Local-First Mandate

1. **Push notifications (FCM/APNs) are mandatory external services** (Task 7 description: "push notifications (FCM)", Task 19: "push notification delivery"). This directly violates the "no mandatory external services" rule.
2. **Offline sync architecture** is unspecified in the task descriptions. If the sync endpoint defaults to a cloud relay server, it violates the mandate. If it targets the user's own machine, it is compatible.
3. **Task 8 success criterion "Mobile apps published to iOS App Store + Google Play"** is a distribution concern, not a runtime concern. Publishing to app stores is acceptable as a delivery mechanism — it does not impose runtime cloud dependencies on the user.

### Recommendations

1. **Push notifications MUST be behind a feature flag.** The mobile app must function fully (chart generation, Dasha timelines, D1/D9 visualizations) with zero connectivity. Push notifications degrade gracefully when FCM/APNs credentials are absent or connectivity is unavailable.
2. **Sync server URL MUST default to `http://localhost:8000`** and be user-configurable in app settings. The architecture must assume the target is the user's own local machine. No cloud sync relay service may be introduced.
3. **Remove "push notification delivery" from QA success criteria** (Task 19) unless push is explicitly marked optional. QA should test "app works with zero connectivity" as the primary path.
4. **In-app purchases** are acceptable as optional monetization. No change needed.
5. **App store submission** is acceptable as a distribution mechanism. No change needed.

---

## 2. Plugin Marketplace

**Tasks:** 9 (Plugin API & Sandbox), 10 (Marketplace Backend), 11 (Plugin Runtime & CLI), 20 (Security Audit)  
**Assessment:** FAIL

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| Plugin API spec, sandbox isolation model | Yes | Pure design and local execution model. Fully compatible. |
| Plugin installation/uninstallation, CLI tooling | Yes | Local operations. Fully compatible. |
| Sandbox execution engine (CPU/memory/network limits) | Yes | Local process isolation. Fully compatible. |
| Security audit of sandbox | Yes | Local testing. Fully compatible. |
| **Marketplace registry (listing, search, download, ratings, versioning)** | **No** | Requires a hosted web service with a database, search index, and CDN for downloads. A user on a single machine with no internet cannot access this. |
| **Stripe payments** | **No** | External payment processing. Requires internet connectivity and a Stripe account. Irrelevant for a local-first single-user platform. |
| **Developer portal** | **No** | Requires a hosted web service. |
| **Success criterion "1000+ downloads, 10+ third-party plugins"** | **No** | Assumes a public, internet-facing marketplace. Contradicts single-user local-first. |

### Conflicts with Local-First Mandate

1. **Task 10 explicitly requires a hosted registry** ("Marketplace listing, search, ratings, versioning, Stripe payments, developer portal"). This is fundamentally a cloud service and directly violates the "no cloud deployment" and "everything runs on single machine" rules.
2. **Stripe payments** are an external service dependency with no place in a local-first platform.
3. **The developer portal** is a hosted web service. Contradicts local-first.
4. **The entire marketplace concept** as described ("10+ third-party plugins, 1000+ downloads total") presupposes a public ecosystem with a hosted hub — the antithesis of local-first.

### Recommendations

1. **Replace hosted registry with a local-first plugin directory.** Plugin manifests are distributed as a bundled JSON file (e.g., `plugins/registry.json`) that ships with the app or is downloadable as a static file. Users run `astroos plugin list`, `astroos plugin install <name>`, and the CLI resolves the manifest to a download URL (GitHub release tarball, etc.).
2. **Remove Stripe payments entirely.** Plugins on a local-first platform are either free, donation-ware, or this functionality is deferred to Phase IV.
3. **Replace "Developer Portal" with local developer documentation** — CLI reference, sandbox testing guide, plugin API docs shipped with the app. No hosted web service.
4. **Re-scope Task 10** to "Plugin Discovery & Local Registry" — no hosted infrastructure.
5. **Remove the 1000-downloads / 10-plugins success criterion.** Replace with "plugin API stable, 2+ sample plugins installable via CLI."
6. **Keep Tasks 9, 11, and 20** as-is — they deal with local sandboxing, CLI, and security, all of which are local-first compatible.

---

## 3. Real-Time Collaboration

**Tasks:** 12 (Core — WebSocket, OT/CRDT, presence/cursors), 13 (UI — comments, @mentions, chats, sharing, version history)  
**Assessment:** FAIL

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| WebSocket infrastructure | Conditionally | Requires a running server process. Compatible if that server is the user's own machine. |
| OT/CRDT conflict resolution | **No** | Designed for multiple concurrent editors. Over-engineered for single-user. |
| Presence indicators, cursor sharing | **No** | Multi-user features. Have no meaning on a single-user platform. |
| @mentions, chat threads, inline comments | **No** | Multi-user features. Require multiple participants. |
| Project sharing UI | **No** | Multi-user feature. |
| Version history explorer | Yes | Single-user feature. Compatible. |
| **Success criterion "10+ concurrent users on one project"** | **No** | Explicitly multi-user. Contradicts single-user mandate. |

### Conflicts with Local-First Mandate

1. **The entire workstream is designed for multi-user collaboration.** OT/CRDT, presence indicators, cursor sharing, @mentions, chat threads, and project sharing are all features that exist only to serve multiple simultaneous users.
2. **Task 12 and Task 13** together constitute a multi-user collaboration suite. The single-user personal research platform has no use for @mentions or chat threads.
3. **The 10+ concurrent user success criterion** directly contradicts the "single-user personal research platform" mandate.
4. **OT/CRDT** is sophisticated infrastructure (operational transformation / conflict-free replicated data types) that adds significant complexity for zero benefit to a single user.

### Recommendations

**Option A (Recommended): DEFER entirely.** Move Real-Time Collaboration to Phase IV (multi-tenancy). The single-user platform has no need for this workstream. This removes Tasks 12, 13, and the collaboration portions of Task 21's dependency chain.

**Option B (If kept): SCOPE to local-network sharing only.**
- WebSocket server runs on the user's machine. Other devices connect via LAN.
- Support 2-3 concurrent connections (not 10+).
- Remove OT/CRDT — use operational locking (one-editor-at-a-time per document) which is simpler and sufficient for small-scale local use.
- Remove @mentions, chat threads, presence indicators, cursor sharing — these are enterprise features.
- Keep version history explorer (useful for single-user too).
- All collaboration features must be **disabled by default** in single-user mode.

---

## 4. Advanced Analytics

**Tasks:** 14 (Query Builder — drag-drop, cohort segmentation, filter chains), 15 (Statistical Engine — correlation, chi-squared, t-test, Bayes, significance, visualization)  
**Assessment:** PASS

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| Drag-drop query builder | Yes | Pure UI. Runs locally. |
| Cohort segmentation UI | Yes | Pure UI over local data. |
| Variable picker, filter chains | Yes | Pure UI. |
| Statistical methods (correlation, chi-squared, t-test, Bayes) | Yes | Pure computation. Runs locally. No external services needed. |
| Significance calculation | Yes | Local computation. |
| Visualization output | Yes | Local rendering. |

### Conflicts with Local-First Mandate

**None.** All statistical computation is pure mathematics executed locally. The query builder is a UI layer over local PostgreSQL. This workstream is fully aligned with the local-first mandate.

### Recommendations

- **Proceed as-is.** No changes needed.
- The dependency chain (Task 14 -> Task 15) is sensible.

---

## 5. i18n & Localization

**Tasks:** 16 (Infrastructure — message extraction, translation memory, locale switching, RTL), 17 (Content — 5 languages: ES, HI, FR, DE, AR)  
**Assessment:** PASS

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| Message extraction | Yes | Local tooling. |
| Translation memory | Yes | Local file-based or database. |
| Locale switching | Yes | Pure UI. |
| RTL layout testing | Yes | Pure UI/rendering. |
| 5 language translations | Yes | Static content. Ships with the app. |

### Conflicts with Local-First Mandate

**None.** All i18n work is static content, UI rendering logic, and local tooling. No external services required. Translation memory can use local SQLite or JSON files.

### Recommendations

- **Proceed as-is.** No changes needed.
- Ensure translation memory uses local storage (SQLite or file-based), not a cloud translation API.
- Ensure RTL testing includes single-user offline scenarios.

---

## 6. Public API & OAuth

**Tasks:** 18 (OAuth 2.0, API key portal, rate limiting, webhooks, developer playground)  
**Note:** Task 18 is listed in `tasks_phase3_data.json` with `"dependencies": [17]` (i18n), but the roadmap shows Phase III.6 depending on earlier phases. The task dependency chain appears to need the i18n pipeline completed first.  
**Assessment:** CONDITIONAL

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| OpenAPI 3.0 spec | Yes | Documentation. Fully compatible. |
| API key management panel | Yes | Web UI. Runs locally. |
| Rate limiting middleware | Yes | Local server middleware. Compatible. |
| Webhook triggers | Conditionally | Webhooks require a reachable endpoint. For local development, this works with localhost listeners. For production use, the machine needs a public URL or tunnel (ngrok, etc.). |
| **OAuth 2.0 flow** | **Over-engineered** | OAuth 2.0 is designed for third-party app authorization. For a single-user platform, API keys alone suffice. OAuth adds significant complexity (authorization server, redirect URIs, token refresh) with no benefit at single-user scale. |
| **Developer portal (playground)** | Conditionally | An interactive API playground (like Swagger UI) can and should run locally. No hosted service needed. |
| **Success criterion "10+ developers, 1000+ requests/day"** | **Contradicts local-first** | Having 10+ external developers hitting the instance implies the machine is publicly accessible (port forwarding, public IP, or cloud deployment). This contradicts the single-machine mandate. |

### Conflicts with Local-First Mandate

1. **OAuth 2.0 is over-engineered for single-user.** It adds an authorization server, token management, client registration, and redirect handling — all unnecessary when the platform has one user. API keys with scoped permissions are sufficient.
2. **The "10+ developers" success criterion** fundamentally assumes public network exposure. A local-first platform does not expose itself to the public internet by default.
3. **Webhooks** require external reachability. This is a minor concern (instructions for tunnels suffice) but worth noting.
4. **The developer portal** should be local (Swagger/ReDoc) not a hosted service.

### Recommendations

1. **Simplify OAuth 2.0 to API keys only for single-user mode.** OAuth 2.0 can be an optional add-on for users who expose their instance publicly, but it must not be the default or required path.
2. **Default rate limiting to generous (or disabled) local-first defaults.** Rate limiting is a multi-tenant concern. For single-user, it should be opt-in.
3. **Webhook delivery instructions** should document local testing with ngrok/tunnel. The webhook engine itself is local-first compatible.
4. **Developer playground** is fine as a local Swagger UI/ReDoc instance. No hosted service.
5. **Replace the success criterion:** "API key system operational, developer docs complete, webhook system testable with local endpoints (ngrok/tunnel)." Remove the "10+ developers, 1000+ requests" metric.
6. **Task 18 dependency chain** — the dependency on i18n (Task 17) seems incorrect. The Public API should depend on existing infrastructure, not localization. Audit and correct the dependency graph.

---

## 7. GDPR Compliance

**Tasks:** 21 (Data export/deletion, consent management, anonymization)  
**Dependencies:** 13 (Collaboration), 18 (Public API)  
**Assessment:** CONDITIONAL (over-engineered for single-user)

### Analysis

| Sub-item | Local-First? | Detail |
|---|---|---|
| Data export | Yes | Data is in local PostgreSQL. Export is a SQL query + file dump. Fully compatible. |
| Data deletion | Yes | Local SQL operation. Fully compatible. |
| Anonymization for research datasets | Yes | Local computation. Fully compatible. |
| **Consent management** | **Irrelevant** | Consent management is a regulatory requirement for platforms that process data on behalf of multiple data subjects. A single-user personal research platform has one data subject — the user themselves. Consent management has no applicable use case. |

### Conflicts with Local-First Mandate

1. **Consent management is unnecessary for a single-user platform.** The user owns all their own data. There is no separate "data subject" whose consent must be tracked.
2. **The dependency chain (Tasks 13, 18 -> 21)** links GDPR to collaboration and public API — implying GDPR is only needed when multi-user features are active. This is architecturally correct but the framing is wrong for a single-user default.
3. **"GDPR Compliance" as a task name** implies regulatory overhead that doesn't apply to a single-user research tool. This is over-engineering.

### Recommendations

1. **Remove consent management entirely.** Not applicable to single-user local-first platform.
2. **Re-scope Task 21 to "Research Data Privacy Tools"** — focus on practical features: 
   - "Export All My Data" button (PostgreSQL dump + file archive)
   - "Delete All Data" button (confirm + truncate)
   - Anonymization as a research publishing tool (not GDPR compliance)
3. **Remove the dependency on Task 13 (Collaboration).** Data export/deletion and anonymization must work independently of collaboration features.
4. **Keep the dependency on Task 18 (Public API)** only if API usage generates access logs that need export/deletion. Otherwise remove it.

---

## Summary

| # | Workstream | Tasks | Assessment | Verdict |
|---|---|---|---|---|
| 1 | Mobile Apps | 6, 7, 8, 19 | **CONDITIONAL** | Fix push flag, fix sync-target default, proceed |
| 2 | Plugin Marketplace | 9, 10, 11, 20 | **FAIL** | Replace hosted registry with local plugin directory; remove Stripe; remove dev portal |
| 3 | Real-Time Collaboration | 12, 13 | **FAIL** | Defer to Phase IV or scope to local-network only, remove multi-user features |
| 4 | Advanced Analytics | 14, 15 | **PASS** | Proceed as-is |
| 5 | i18n & Localization | 16, 17 | **PASS** | Proceed as-is |
| 6 | Public API & OAuth | 18 | **CONDITIONAL** | Simplify OAuth to API keys; fix success metrics; correct dependency graph |
| 7 | GDPR Compliance | 21 | **CONDITIONAL** | Remove consent mgmt; rescope to Privacy Tools; fix dependency chain |

---

## Final Recommendation: REDESIGN

Phase III "Lakshmi" as currently specified **cannot proceed as-is** because three workstreams (Plugin Marketplace, Real-Time Collaboration, GDPR Compliance framing) fundamentally conflict with the local-first mandate.

### Required Actions Before Phase III Begins

1. **Plugin Marketplace (Tasks 9-11, 20):** Redesign Task 10 to use a local plugin directory (bundled manifest JSON) instead of a hosted registry. Remove Stripe payments. Remove developer portal as hosted service. Keep sandbox, CLI, and security audit as specified.

2. **Real-Time Collaboration (Tasks 12-13):** Either defer to Phase IV entirely (recommended) or scope to local-network-only with reduced feature set (no OT/CRDT, no @mentions, no chat, max 2-3 concurrent connections, disabled by default).

3. **GDPR Compliance (Task 21):** Re-scope to "Research Data Privacy Tools." Remove consent management. Remove dependency on Task 13. Simplify data export/deletion to local SQL operations.

4. **Mobile Apps (Tasks 6-8, 19):** Make push notifications optional (feature-flagged). Default sync server to `http://localhost:8000`. Verify offline-first is the primary mode.

5. **Public API (Task 18):** Default to API keys (not OAuth 2.0). Remove the "10+ developers" success metric. Ensure the developer playground runs locally.

6. **Correct dependency graph issues:** Task 18's dependency on Task 17 (i18n) should be reviewed. Task 21's dependency on Task 13 should be removed.

### Workstreams That Pass (Proceed As-Is)

- Advanced Analytics (Tasks 14-15)
- i18n & Localization (Tasks 16-17)

---

*This audit supersedes any conflicting assumptions in the Phase III roadmap. Update `ASTROOS_PHASE_III_V2_3_ROADMAP.md` and `tasks_phase3_data.json` to reflect the required changes before Phase III execution begins.*
