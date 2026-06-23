# Mobile — React Native (iOS + Android)

Every client does the same three things: **authenticate → browse → play** (call `/api/play/{id}`,
load the manifest, let the OS player handle the DRM license). Only the language + player API differ.

- **Player:** `react-native-video` (DRM support) or native ExoPlayer (Android) / AVPlayer (iOS).
- **DRM:** ExoPlayer → Widevine (Android); AVPlayer → FairPlay (iOS).
- **Billing:** `react-native-iap` → Apple IAP + Google Play Billing. After purchase, POST the signed
  transaction / `purchaseToken` to `POST /api/subscribe/verify-iap` with `platform: "apple"|"google"`.
- **Auth:** reuse the same JWT endpoints as web (`/api/auth/*`, `/api/me`).

Suggested structure: `src/api/` (port `web/lib/api.js`), `src/screens/{Browse,Show,Player,Subscribe,Login}`.
Use the same `/api/play/{id}` response shape: `{ playback_token, manifest: { dash, hls }, expires_in }`.
