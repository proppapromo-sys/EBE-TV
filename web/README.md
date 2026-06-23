# Web client — Next.js (App Router)

```bash
npm install
cp .env.local.example .env.local        # NEXT_PUBLIC_API_BASE=http://localhost:8000/api
npm run dev                              # http://localhost:3000
```

Pages: `/` browse · `/show/[slug]` detail · `/watch/[id]` player · `/subscribe` plans · `/login`.

The player (`app/watch/[id]/page.js`) calls `/api/play/{id}`, then uses **Shaka Player** for
DASH/Widevine and falls back to native **HLS/FairPlay** on Safari. All API + JWT logic lives in
`lib/api.js` — port it as-is to the React Native client.
