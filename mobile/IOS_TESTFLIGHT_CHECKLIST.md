# LymeWire iOS TestFlight Checklist

## App Identity

- App name: `LymeWire`
- Bundle ID: `app.lymewire.mobile`
- Version: `0.1.0`
- Build number: auto-incremented after build `1`
- Encryption: `ITSAppUsesNonExemptEncryption = false`

## Apple Developer Setup

Create or verify these in Apple Developer and App Store Connect:

- Apple Developer Program membership is active.
- Bundle ID exists for `app.lymewire.mobile`.
- App Store Connect app record exists for `LymeWire`.
- SKU can be any stable internal value, for example `lymewire-mobile`.
- Platform: iOS.
- TestFlight access is available.

## Credentials

Do not commit or paste credential contents into chat.

Required for automated upload:

- App Store Connect API Key ID.
- App Store Connect Issuer ID.
- `AuthKey_<KEY_ID>.p8` private key file stored outside the repo.

Expected local secret env shape:

```bash
ASC_KEY_ID=...
ASC_ISSUER_ID=...
ASC_KEY_PATH=/absolute/private/path/AuthKey_....p8
```

## Build Commands

EAS cloud build:

```bash
npx eas build --platform ios --profile ios-production
```

Submit after build:

```bash
npx eas submit --platform ios --profile ios-production
```

Local Mac/Xcode archive path is also possible, but requires macOS, Xcode, signing certificates, and App Store Connect API credentials.

## TestFlight Notes

Suggested "What to Test":

```text
Test Turkish/English onboarding, guest mode, LymeWire chat responses, long-answer follow-up messages, and API connectivity.
```
