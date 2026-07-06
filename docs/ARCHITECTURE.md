# Architecture notes

## The core principle
The backend **never serves raw video**. A client authenticates, browses metadata, then calls
`/api/play/{episode_id}`. The backend does an **entitlement check**, and only then mints a
**short-lived (≈120s) signed token**. The client plays directly from Cloudflare Stream's CDN; DRM
license requests are authorized by that same token. An unsubscribed user never gets a token →
never gets a license → can't decrypt.

```
client ──/api/play──▶ backend (is_entitled?) ──mint token──▶ client ──play+license──▶ Cloudflare
```

## Cloudflare Stream pipeline (`apps/cms` ingest · `apps/playback` egress)
**Ingest:** the client requests a one-time **direct-upload URL** (`requireSignedURLs:true`) and PUTs
the raw file straight to Cloudflare — bytes never touch our server. Cloudflare transcodes once to
CMAF/cbcs (one asset → Widevine + FairPlay + PlayReady). Readiness flips `Video.ready` two ways:
the **transcode webhook** (`/api/webhooks/cloudflare`, HMAC-verified via `CF_WEBHOOK_SECRET`) or the
webhook-free **`sync_video_status`** poll (cron / backfill) — belt and suspenders so an upload still
goes live if a webhook delivery is missed.
**Egress:** `/api/play` mints a short-lived **RS256 JWT** signed with the Stream signing key
(`sub`=video uid, `kid`, `exp`≈120s). It rides in the manifest path
(`…/<jwt>/manifest/video.mpd`), and the **same token authorizes the DRM license request** — so an
unentitled user gets no token, no license, no plaintext. Keys are accepted as raw PEM or
Cloudflare's base64 form.

## Entitlement (`apps/subscriptions/services.py`)
`is_entitled(user_id)` = "has an `active` subscription whose `current_period_end` is in the
future". Cached in Redis for 5 min; **every billing change calls `invalidate_entitlement`** so
access flips immediately. This one function is the gate the whole platform trusts.

## Billing normalization (`apps/billing/`)
Three providers, one truth. Stripe (web, full margin), Apple IAP, Google Play Billing all funnel
through `normalize.apply_subscription_state()` → the `subscriptions` table. Handlers are idempotent
(`update_or_create` on `(source, external_id)`).

## Creator studio (`apps/studio/`)
Self-serve upload for the "creators stream their own shows" model. A user opts into creator mode
(`is_creator`), then creates shows, requests Cloudflare upload URLs, adds episodes, and **submits
for moderation** — `draft → pending → published` (an admin publishes via the CMS). Two invariants:
every endpoint is **owner-scoped** (a creator can never read or edit another creator's content — a
foreign id 404s, not 403s, so nothing leaks), and **creators cannot self-publish** (the public
catalog only serves `published`, so a submission is invisible until approved). New uploads
auto-set `Show.owner`, which is exactly the key the payout engine attributes revenue by.

## Creator payouts (`apps/payouts/`)
For platforms where third parties stream **their own** shows. Three steps mirror three tables:
1. **Ownership** — `catalog.Show.owner` links a show to the creator who earns from it
   (`owner=None` = platform original, no payout).
2. **Attribution** — `compute_earnings(period)` splits a period's `revenue_pool_cents` by
   **watch-time pro-rata**: each creator's share = seconds watched of their shows ÷ total seconds
   watched of all owned shows (read from `catalog.WatchProgress`). Written to a `CreatorEarning`
   ledger, idempotent on `(period, creator)`. Fixed-point math so the pool splits exactly.
3. **Payout** — `run_payouts(period)` issues **Stripe Connect** transfers to each creator's
   connected account, gated on `payouts_enabled` and idempotent per earning
   (`idempotency_key=payout-<earning_id>`). The platform keeps `platform_fee_bps`.

The flat all-access sub has no per-show price, so pro-rata watch time is the fair attribution key.
A production build would feed step 2 off playback **heartbeat events** (true cumulative watch time);
`WatchProgress` is the same shape and a faithful proxy for the foundation.

## Hard-won cautions
- **Never serve raw video URLs.** Always entitlement-check → mint short-lived token. TTL ~2 min.
- **Creator payouts must reconcile against real revenue.** Only distribute money you actually
  collected for the period (net of refunds/chargebacks/app-store cut), and pay from a computed,
  reviewable ledger — never transfer straight from a webhook.
- **Webhook normalization is where this breaks.** Three async, signed sources with grace periods.
  Build idempotent handlers; always bust the Redis cache on any change.
- **Encrypt once (CMAF/cbcs).** One asset serves Widevine + FairPlay + PlayReady. Cloudflare does
  this — don't double-encode.
- **In-app purchase is mandatory** for digital subs sold inside iOS/Android apps (15–30% cut).
  Only web (Stripe) keeps full margin. Use **account-linking** for TV apps (show a code, link on
  the website) to reuse a web subscription.
- **Provider approvals take time** (Apple/StoreKit, Google Play + Pub/Sub, Roku). Start early.
