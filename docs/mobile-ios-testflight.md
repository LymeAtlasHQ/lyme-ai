# LymeWire iOS / TestFlight setup

LymeWire's iOS app uses the same Expo codebase as the Android APK. The app bundle identifier is:

```text
app.lymewire.mobile
```

## Apple Developer items to prepare

Create or verify these in Apple Developer / App Store Connect:

| Area | Value |
| --- | --- |
| Bundle ID | `app.lymewire.mobile` |
| App name | `LymeWire` |
| SKU | `lymewire-mobile` or another internal unique SKU |
| Primary language | Turkish or English; the app itself supports TR/EN selection |
| Platform | iOS |
| TestFlight | Enabled for internal testing |
| Encryption/export compliance | The app does not add custom encryption; it uses HTTPS/API calls only. The Expo config sets `usesNonExemptEncryption: false`. |
| Health data | No Apple Health access in this MVP. Do not enable HealthKit entitlement yet. |

## Secure credential path

Do not paste Apple private keys, p8 contents, app-specific passwords, or account passwords into chat.

For EAS cloud builds, the safe path is:

1. Sign in to Expo/EAS on a trusted terminal.
2. Run `npx eas build -p ios --profile production`.
3. Let EAS connect to Apple Developer and create or reuse the distribution certificate and provisioning profile.
4. Run `npx eas submit -p ios --profile production` after the app exists in App Store Connect.

For Codex/TestFlight automation with App Store Connect API, store these as secrets in the build environment, outside the repo:

| Secret | Meaning |
| --- | --- |
| `ASC_KEY_ID` | App Store Connect API key ID |
| `ASC_ISSUER_ID` | App Store Connect issuer ID |
| `ASC_KEY_PATH` | Local path to the private .p8 key file |

## Current repo preparation

- `mobile/app.json` contains the iOS bundle identifier and build number.
- `mobile/eas.json` contains `ios-preview` and `production` iOS build profiles.
- `.github/workflows/ios-expo-check.yml` validates the Expo iOS config and prebuild path without Apple signing.

A signed IPA/TestFlight upload still requires Apple Developer credentials or an authenticated EAS account.
