# Go-live checklist — EBE·TV web

Everything below is config + deploy; the application code is launch-ready. Order matters loosely;
do **1–3** to deploy, **4–6** to make money + stream, **7** to verify.

## 1. Generate app secrets
- `DJANGO_SECRET_KEY` — long random string (`python -c "import secrets;print(secrets.token_urlsafe(50))"`)
- `JWT_SIGNING_KEY` — another long random string
- `ALLOWED_HOSTS=api.ebe.tv` · `CORS_ALLOWED_ORIGINS=https://ebe.tv`

## 2. Provision data stores
- **Postgres** + **Redis** (Railway/Render give you both). Set `DATABASE_URL` and `REDIS_URL`.

## 3. Deploy
- **Backend** → Railway/Render from `infra/Dockerfile.backend`. After deploy:
  `python manage.py migrate` (and `createsuperuser` for admin + moderation).
- **Web** → Vercel from `web/`. Set `NEXT_PUBLIC_API_BASE=https://api.ebe.tv/api`.
- Point DNS: `ebe.tv` → Vercel, `api.ebe.tv` → backend host.

## 4. Cloudflare Stream (video)
1. Create an **API token** with Stream edit → `CF_ACCOUNT_ID`, `CF_API_TOKEN`.
2. Create a **signing key** (`POST /stream/keys`) → `CF_STREAM_SIGNING_KEY_ID`, `CF_STREAM_SIGNING_KEY_PEM`.
3. Set `CF_CUSTOMER_SUBDOMAIN` (customer-XXXX.cloudflarestream.com).
4. Add a **transcode webhook** → `https://api.ebe.tv/api/webhooks/cloudflare`; set `CF_WEBHOOK_SECRET`.
   (Or rely on `python manage.py sync_video_status` on a cron.)

## 5. Stripe (billing)
1. Create the account under **EBE TECHNOLOGIES INC**, connect your bank.
2. Create **Prices** (monthly, annual) → `STRIPE_PRICE_MONTHLY`, `STRIPE_PRICE_ANNUAL`.
3. `STRIPE_SECRET_KEY`. Add a **webhook** → `https://api.ebe.tv/api/webhooks/stripe`; set `STRIPE_WEBHOOK_SECRET`.
4. (Creator payouts) enable **Connect**, set `PLATFORM_FEE_BPS` + `STRIPE_CONNECT_*` URLs.

## 6. Resend (email)
- `RESEND_API_KEY`, verify your sending domain, set `EMAIL_FROM` and `FRONTEND_BASE_URL=https://ebe.tv`.

## 7. Content + verify
- `python manage.py bulk_ingest --json library.json --publish` (or upload via the Studio).
  Run `sync_video_status` until videos are `ready`.
- Legal: the `/terms` and `/privacy` pages ship as templates — have counsel review.
- Smoke test on prod: register → receive welcome email → subscribe (real charge) →
  play a DRM video → cancel from Account. Approve a creator submission from **/moderate**.

## Env var summary
`DJANGO_SECRET_KEY JWT_SIGNING_KEY ALLOWED_HOSTS CORS_ALLOWED_ORIGINS DATABASE_URL REDIS_URL`
`CF_ACCOUNT_ID CF_API_TOKEN CF_WEBHOOK_SECRET CF_STREAM_SIGNING_KEY_ID CF_STREAM_SIGNING_KEY_PEM CF_CUSTOMER_SUBDOMAIN`
`STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET STRIPE_PRICE_MONTHLY STRIPE_PRICE_ANNUAL`
`PLATFORM_FEE_BPS STRIPE_CONNECT_RETURN_URL STRIPE_CONNECT_REFRESH_URL`
`RESEND_API_KEY EMAIL_FROM FRONTEND_BASE_URL`

> Native iOS/Android/TV apps are a separate effort (the `clients/` dirs are scaffolds). This
> checklist launches the **web** product.
