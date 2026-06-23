# Roku — BrightScript + SceneGraph

- **Player:** Roku `Video` node with DRM config (PlayReady or Widevine).
- **Auth/catalog/play:** call the same REST API; parse `/api/play/{id}` → `manifest.dash` + token.
- **Billing:** Roku Pay (Roku takes a cut; required for in-channel signups) OR **account-linking** —
  show an on-screen code, user links their existing web subscription on your website.
- Build a `components/` tree (HomeScene, GridScreen, DetailScreen, VideoScreen) + a `source/` API
  module. Submit via the Roku Developer Dashboard.
