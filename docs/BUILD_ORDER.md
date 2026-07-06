# Build order

The dependency-correct sequence. Each step is independently testable.

1. **Backend foundation** ✅ (in this repo) — Django, users + JWT auth, Postgres, Redis.
2. **Catalog + CMS** ✅ — data model, admin, Cloudflare direct-upload, publish flow.
3. **Cloudflare Stream integration** — upload → transcode webhook (`/api/webhooks/cloudflare`) →
   signed tokens. *Set `CF_*` to go live.*
4. **Entitlement + playback gate** ✅ — `is_entitled`, `/api/play/{id}`.
5. **Stripe (web) billing + webhook** ✅ — one billing source fully working end-to-end.
   *Set `STRIPE_*`.*
6. **Web client** ✅ — first playable surface; validates the whole pipeline with DRM.
7. **React Native mobile** + Apple IAP + Google Play Billing + webhooks (`clients/mobile`).
8. **TV apps** in priority order: Roku → Fire TV / Android TV → Apple TV → Tizen / webOS.
9. **Polish:** watch progress ✅, continue-watching ✅, search, profiles.
10. **Hardening:** rate limits ✅ (DRF throttles), token-abuse monitoring, refund/chargeback
    handling, analytics.

✅ = present in this foundation. Unchecked = scaffolded with a per-client README.
