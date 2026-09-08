# LymeWire Mobile

Expo-based mobile app shell for LymeWire.

This is the first shared iOS, Android/APK, and web app surface. It connects to the existing Railway backend by default:

```text
https://lyme-ai-production.up.railway.app
```

## What works in this MVP

- Chat screen connected to wire-aware `POST /ask`.
- Wires screen for Care, Research, Treatment, Guideline, Trial, Doctor Brief, and Calm modes.
- Recent app messages are sent as short `history` context.
- Local-only Timeline notes.
- Doctor Brief draft generation from local Timeline notes.
- Sources screen with safety and evidence boundaries.

## What is intentionally not active yet

- No durable medical-record storage.
- No Apple Health, Huawei Health, Google Fit, or hospital system import.
- No App Store or Google Play submission until privacy/legal copy and account design are ready.
- No doctor ranking by unverifiable success rates.

## Local run

```bash
cd mobile
npm install
npm run start
```

For a different backend:

```bash
EXPO_PUBLIC_LYMEWIRE_API_URL=https://your-api.example.com npm run start
```

## Android APK

The `preview` EAS profile is configured for APK output:

```bash
cd mobile
npx eas build -p android --profile preview
```

## iOS

The production iOS bundle identifier is:

```text
app.lymewire.mobile
```

For TestFlight:

```bash
cd mobile
npx eas build -p ios --profile production
npx eas submit -p ios --profile production
```

Apple Developer credentials and App Store Connect setup are required before submit.
