# Samsung Tizen + LG webOS — shared web app (JS/HTML)

- **Player:** AVPlay (Tizen) / webOS media APIs, or Shaka Player where supported.
- **DRM:** **PlayReady** (primary on both) + Widevine where available.
- One web codebase + platform shims usually serves both. You can start from `web/` and adapt.
- **Billing:** typically **account-linking** to a web subscription (no native IAP needed) — show a
  code, link on the website.
