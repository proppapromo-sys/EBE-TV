# Streaming Platform — foundational build

A subscription streaming service (Zeus / NowThatsTV style): original shows, one all-access tier
(monthly/annual), DRM-protected video to web + mobile + TV. **Django + DRF · PostgreSQL · Redis ·
Cloudflare Stream · Stripe + Apple IAP + Google Play Billing.**

This repo is the runnable foundation: a complete backend (auth, catalog, **entitlement gate**,
**signed playback tokens**, **3-source billing normalizer**, CMS), a working Next.js web client,
Docker infra, and scaffolds for the native/TV clients.

> **What's validated:** the backend runs today — `manage.py check`, migrations, and the entitlement
> test suite all pass, and the full API was exercised over HTTP (register → gate → play). Every
> external integration (Stripe/Cloudflare/Apple/Google) **degrades gracefully** when keys are
> absent, so you can build immediately and wire providers as you go.

---

## Quick start — two ways

### A) Fastest (no Docker, no external services) — backend in ~1 minute
```bash
cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # defaults run on SQLite + in-memory cache
python manage.py migrate
python manage.py seed_demo                         # demo show + plans + subscribed demo user
python manage.py createsuperuser                   # for the /admin CMS
python manage.py runserver                         # http://localhost:8000
```
Then the web client:
```bash
cd web
npm install
cp .env.local.example .env.local
npm run dev                                        # http://localhost:3000
```
Sign in with **demo@demo.test / demopass123** (seeded with an active subscription).

### B) Full stack with Postgres + Redis (Docker)
```bash
cp backend/.env.example backend/.env               # fill in real keys when ready
docker compose up --build                          # web :3000 · api :8000 · pg :5432 · redis :6379
```

---

## What works the moment you start
- **Auth:** register / login / refresh / logout (JWT) + `/api/me`. Apple/Google social exchange stub.
- **Catalog:** public browse + show/episode metadata (never exposes video).
- **Entitlement gate:** `is_entitled()` (Redis-cached) → `/api/play/{id}` returns **403** for
  non-subscribers, and a **signed Cloudflare playback token** for subscribers.
- **Billing:** Stripe checkout + webhook fully wired; Apple/Google verify + webhook handlers
  structured with the exact endpoints to call (return `not_configured` until you add keys —
  fail-closed). All three normalize into one `subscriptions.status` and bust the cache on change.
- **CMS:** Cloudflare direct-upload URL, show/episode CRUD, publish, transcode webhook → `ready`.
- **Creator payouts:** shows have an `owner`; subscription revenue is split across creators by
  **watch-time pro-rata** (minus a configurable platform fee) into a `CreatorEarning` ledger, paid
  via **Stripe Connect** transfers. `/api/creator/{onboard,account,earnings}` + the
  `compute_payouts` / `run_payouts` commands. Fail-closed until `STRIPE_SECRET_KEY` is set.
- **Creator studio (self-serve upload):** any user can `enable` creator mode, then create shows,
  request Cloudflare upload URLs, add episodes, and **submit for moderation** (draft → pending →
  admin publishes). All endpoints are owner-scoped — creators only ever see/edit their own content.
  `apps/studio` · `/api/studio/*`.
- **Web client:** browse → show → player (Shaka Player: DASH/Widevine, HLS/FairPlay on Safari),
  subscribe page, login, continue-watching, **creator studio + payout dashboard**.

## Wire the real services (when ready)
1. **Cloudflare Stream** — set `CF_ACCOUNT_ID` / `CF_API_TOKEN`, create a signing key (`CF_STREAM_
   SIGNING_KEY_ID` / `_PEM`, base64 or PEM both accepted), and set `CF_CUSTOMER_SUBDOMAIN`. Uploads
   go straight to a direct-upload URL (studio or CMS); readiness flips via the transcode webhook at
   `/api/webhooks/cloudflare` (set `CF_WEBHOOK_SECRET` to verify it) **or** the webhook-free
   fallback `python manage.py sync_video_status` (run on a cron). Playback then mints short-lived
   signed tokens → DASH/Widevine + HLS/FairPlay.
2. **Stripe** — set `STRIPE_*`, create monthly/annual Prices, point the webhook at
   `/api/webhooks/stripe`. Web signups now bill at full margin.
3. **Apple / Google** — set the IAP envs; finish the `TODO` verification calls in
   `apps/billing/apple.py` and `google.py` (endpoints are documented inline).
4. **Creator payouts (Stripe Connect)** — set `STRIPE_CONNECT_*` URLs (reuses `STRIPE_SECRET_KEY`)
   and `PLATFORM_FEE_BPS`. Creators onboard via `POST /api/creator/onboard`; run a period with
   `python manage.py compute_payouts --start … --end … --pool-cents …` then
   `python manage.py run_payouts <period_id>`.

## Layout
```
backend/   Django project — apps/{accounts,catalog,subscriptions,billing,playback,cms,payouts,studio}
web/       Next.js web client (browse, subscribe, DRM player)
infra/     Dockerfiles
clients/   native + TV client scaffolds (see each README) — build order in docs/BUILD_ORDER.md
docs/      build order + architecture notes
```

See **docs/BUILD_ORDER.md** for the recommended sequence and **docs/ARCHITECTURE.md** for how the
pieces fit. Hard-won cautions (never serve raw video, encrypt once, IAP is mandatory in-app) are in
`docs/ARCHITECTURE.md`.
