# Mobile Device Lab — QA Testing Guide (Phase III.5)

## Scope

Physical device testing for the AstroOS mobile app. Covers iOS and Android.

## Devices (Recommended)

### iOS
| Device | iOS Version | Priority |
|--------|-------------|----------|
| iPhone 14 Pro | iOS 17 | High |
| iPhone 13 | iOS 16 | High |
| iPhone SE (3rd gen) | iOS 16 | Medium |
| iPhone 12 | iOS 15 | Medium |
| iPad (9th gen) | iPadOS 17 | Low |

### Android
| Device | Android Version | Priority |
|--------|-----------------|----------|
| Pixel 7 | Android 14 | High |
| Samsung Galaxy S23 | Android 14 | High |
| OnePlus 11 | Android 13 | Medium |
| Samsung Galaxy A54 | Android 13 | Medium |
| Pixel 5 | Android 12 | Low |

## Test Scenarios

### 1. Offline-First (Primary Path)
1. Disable all connectivity (airplane mode)
2. Launch app — should show BirthForm
3. Enter birth data and tap "Compute"
4. Expected: error message "No cached data" (first run)
5. Enable connectivity, compute a chart
6. Disable connectivity again
7. Enter same birth data and compute
8. Expected: chart loads from cache with "Offline — cached data" badge

### 2. Online Mode
1. Verify API connection to localhost:8000
2. Compute D1 chart — verify all planets, houses display
3. Compute Dasha timeline — verify periods render
4. Verify yoga detection results display

### 3. Push Notifications (Optional)
1. Configure FCM credentials (Android) or APNs key (iOS)
2. Enable push in Settings
3. Send test notification from API
4. Verify notification delivery

### 4. RTL Layout (Arabic)
1. Switch device language to Arabic
2. Launch app — verify RTL layout
3. Compute chart — verify data displays correctly

## Known Issues
- PDF/HTML rendering: tracked in AMP-009/010 (resolved)
- D9 chart view: coming in Phase IV
