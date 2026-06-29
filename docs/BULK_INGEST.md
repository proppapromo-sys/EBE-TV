# Bulk ingest

Load a large library from one manifest instead of entering titles by hand. Idempotent — re-run to
update (shows match on `slug`, episodes on `(season, number)`).

```bash
python manage.py bulk_ingest --json library.json            # nested manifest
python manage.py bulk_ingest --csv  library.csv  --publish  # flat CSV, publish on import
python manage.py bulk_ingest --json library.json --no-pull  # metadata only, don't pull video
```

Or POST the JSON manifest (staff only): `POST /api/cms/bulk-ingest` with
`{"shows": [...], "publish": true}`.

## How video gets in
Each episode supplies one of:
- **`source_url`** — a public URL to a video file. Cloudflare **pulls and transcodes it** (the
  scalable path: point at your existing S3/CDN files). Readiness flips via the transcode webhook or
  `python manage.py sync_video_status`.
- **`cf_uid`** — reuse an asset already in Cloudflare Stream.
- *(neither)* — metadata-only; attach video later in the Studio.

Videos are only attached if the episode doesn't already have one, so re-runs never re-pull.

## JSON manifest
```json
{
  "collections": [
    { "slug": "ebe-originals", "title": "EBE Originals", "kind": "row", "position": 2 }
  ],
  "shows": [
    {
      "slug": "the-vault",
      "title": "The Vault",
      "description": "Heist anthology.",
      "genre": ["Drama", "Thriller"],
      "poster_url": "https://cdn.ebe.tv/the-vault/poster.jpg",
      "hero_url": "https://cdn.ebe.tv/the-vault/hero.jpg",
      "owner_email": "creator@ebe.tv",
      "status": "published",
      "collections": ["ebe-originals"],
      "seasons": [
        {
          "number": 1,
          "title": "Season 1",
          "episodes": [
            { "number": 1, "title": "Pilot", "duration_s": 2400,
              "source_url": "https://cdn.ebe.tv/the-vault/s1e1.mp4",
              "thumbnail_url": "https://cdn.ebe.tv/the-vault/s1e1.jpg",
              "captions": [{ "language": "en", "label": "English",
                             "vtt_url": "https://cdn.ebe.tv/the-vault/s1e1.en.vtt" }] },
            { "number": 2, "title": "The Job", "cf_uid": "existing-stream-uid" }
          ]
        }
      ]
    }
  ]
}
```

Field notes: `status` defaults to `draft` (use `--publish` or set `"status": "published"`);
`owner_email` links a creator so payouts attribute to them; `collections` lists row slugs to add
the show to; each episode may declare `captions` (a `vtt_url` is pushed to Cloudflare, which
embeds it in the manifest so the player's CC menu can offer it).

## CSV (flat — one row per episode)
Columns (header row required):
```
show_slug,show_title,show_description,genre,poster_url,hero_url,owner_email,show_status,
collections,season_number,episode_number,episode_title,episode_description,thumbnail_url,
duration_s,source_url,cf_uid,episode_status
```
`genre` and `collections` are `|`-separated. Rows are grouped into shows by `show_slug`.
