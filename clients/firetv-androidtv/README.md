# Fire TV / Android TV — Kotlin (or React Native for TV)

- **Player:** ExoPlayer + **Widevine**.
- **UI:** AndroidX Leanback for the 10-foot interface.
- **Billing:** Amazon Appstore IAP (Fire TV) / Google Play Billing (Android TV) →
  `/api/subscribe/verify-iap`.
- **Auth/catalog/play:** same REST API; `manifest.dash`.
