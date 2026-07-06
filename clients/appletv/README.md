# Apple TV — tvOS (Swift / SwiftUI)

- **Player:** AVPlayer + AVContentKeySession for **FairPlay** Streaming.
- **Billing:** StoreKit 2 — shares the same Apple subscription as the iOS app. POST the signed
  transaction to `/api/subscribe/verify-iap` (platform `apple`).
- **Auth/catalog/play:** same REST API; use `manifest.hls` for FairPlay.
- Structure: `Sources/{Views,Services,Player}`. Reuse the iOS networking layer.
