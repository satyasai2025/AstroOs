# Mobile Store Submission Guide — AstroOS v2.3.0

## iOS App Store

### Prerequisites
- Apple Developer Account ($99/year)
- Xcode 15+ with command line tools
- App Store Connect record created

### Steps
1. **Archive** — Open `apps/mobile/ios/AstroOS.xcworkspace` in Xcode → Product → Archive
2. **Validate** — Window → Organizer → Validate App
3. **Upload** — Distribute App → App Store Connect
4. **TestFlight** — Internal testing (up to 100 users)
5. **Submit for Review** — App Store Connect → build → submit

### Required Metadata
- App name: AstroOS
- Category: Reference / Education
- Privacy URL: (point to docs/privacy.md)
- Age rating: 4+

## Google Play Store

### Prerequisites
- Google Play Developer account ($25 one-time)
- Signed APK/AAB (Android App Bundle)
- Store listing assets (icon, screenshots, feature graphic)

### Steps
1. **Build AAB** — `cd apps/mobile && cd android && ./gradlew bundleRelease`
2. **Sign** — Using `android/app/release.keystore` (generate if missing)
3. **Upload** — Google Play Console → Release → Production → Upload AAB
4. **Rollout** — Start with 10% staged rollout, monitor crash reports
5. **Full release** — After 48h of no critical issues

### Required Store Listing
- Short description (80 char): Chart computation + yoga detection + Dasha timeline
- Full description: Local-first Vedic Astrology research platform
- Screenshots: 8+ (phone + tablet)
- Category: Education / Reference

## Local-First Notes

- **No push credentials in code** — FCM `google-services.json` and APNs key are
  injected at build time, never committed
- **Offline-first is primary** — app must function without internet
- **User's own server** — API URL defaults to localhost; user configures
- **No analytics SDK** — no Firebase Analytics, no Crashlytics dependency
