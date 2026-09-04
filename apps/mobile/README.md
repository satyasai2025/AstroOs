# AstroOS Mobile

React Native app for AstroOS — **local-first**, connects to your local AstroOS API.

## Prerequisites

- Node.js >= 20
- React Native CLI (`npx react-native`)
- iOS: Xcode 15+, CocoaPods
- Android: Android Studio, Android SDK 30+

## Local Setup

```bash
# Install dependencies
cd apps/mobile
npm install

# iOS — install Pods
cd ios && pod install && cd ..

# Start Metro bundler
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## Architecture

```
apps/mobile/
├── src/
│   ├── api/client.ts        # API client (default: localhost:8000)
│   ├── components/           # UI components
│   │   ├── BirthForm.tsx
│   │   ├── ChartView.tsx     # D1 SVG chart
│   │   └── DashaTimeline.tsx
│   ├── hooks/                # React hooks
│   │   ├── useChart.ts       # Chart computation + offline cache
│   │   └── useOffline.ts     # Connectivity monitoring
│   ├── navigation/           # Stack navigation
│   ├── screens/              # Screen components
│   ├── storage/offline.ts    # SQLite/AsyncStorage cache
│   └── config.ts             # Local-first defaults
├── App.tsx
└── index.js
```

## Offline Mode

When the API is unreachable, the app serves cached chart computations from
AsyncStorage. The `useChart` hook transparently falls back to cache and
shows the "Offline — cached data" indicator.

## Push Notifications

Push notifications (FCM/APNs) are **optional and feature-flagged**. The app
works fully offline without push. Enable in Settings after configuring
Firebase (Android) or APNs (iOS) credentials.

## License

MIT
