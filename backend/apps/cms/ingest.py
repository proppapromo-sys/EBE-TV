"""
Bulk ingest — load a large library from one manifest instead of hand-entering each title.

A manifest is a dict of shows → seasons → episodes (see docs/BULK_INGEST.md). Each episode can
carry a `source_url` (Cloudflare PULLs + transcodes it), an existing `cf_uid`, or no video yet.
Everything is idempotent (shows on slug, episodes on (season, number)), so re-running a manifest
updates in place — safe to retry. Returns a summary with per-item errors; one bad show never aborts
the rest.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import (Caption, Collection, CollectionItem, Episode, Season,
                                 Show, Video)
from . import cloudflare

User = get_user_model()


def _new_summary():
    return {"shows_created": 0, "shows_updated": 0, "seasons_created": 0,
            "episodes_created": 0, "episodes_updated": 0, "videos_queued": 0,
            "videos_skipped": 0, "captions_added": 0, "errors": []}


def ingest_manifest(data, *, pull_video=True, default_status="draft") -> dict:
    summary = _new_summary()

    # Collections defined up front (so shows can be assigned to them below).
    defined = {}
    for c in data.get("collections", []):
        col, _ = Collection.objects.update_or_create(
            slug=c["slug"],
            defaults={"title": c.get("title", c["slug"]), "kind": c.get("kind", "row"),
                      "position": c.get("position", 0), "published": c.get("published", True)})
        defined[c["slug"]] = col

    for s in data.get("shows", []):
        try:
            _ingest_show(s, defined, pull_video, default_status, summary)
        except Exception as e:                          # isolate failures per show
            summary["errors"].append({"show": s.get("slug") or s.get("title"), "error": str(e)})
    return summary


def _ingest_show(s, defined, pull_video, default_status, summary):
    slug = s.get("slug") or slugify(s.get("title", ""))
    if not slug:
        raise ValueError("show needs a slug or title")
    defaults = {k: s[k] for k in ("title", "description", "poster_url", "hero_url", "genre")
                if k in s}
    defaults.setdefault("title", slug)
    defaults["status"] = s.get("status", default_status)
    owner = User.objects.filter(email=s["owner_email"]).first() if s.get("owner_email") else None
    if owner:
        defaults["owner"] = owner

    show, created = Show.objects.update_or_create(slug=slug, defaults=defaults)
    summary["shows_created" if created else "shows_updated"] += 1

    for cslug in s.get("collections", []):
        col = defined.get(cslug) or Collection.objects.filter(slug=cslug).first()
        if col:
            CollectionItem.objects.get_or_create(
                collection=col, show=show, defaults={"position": col.items.count()})

    for se in s.get("seasons", []):
        season, screated = Season.objects.get_or_create(
            show=show, number=se.get("number", 1), defaults={"title": se.get("title", "")})
        if screated:
            summary["seasons_created"] += 1
        for ep in se.get("episodes", []):
            _ingest_episode(season, ep, pull_video, default_status, summary)


def _ingest_episode(season, ep, pull_video, default_status, summary):
    num = ep.get("number", 1)
    fields = {k: ep[k] for k in ("description", "thumbnail_url", "duration_s") if k in ep}
    fields["title"] = ep.get("title", f"Episode {num}")
    fields["status"] = ep.get("status", default_status)
    if fields["status"] == "published":
        fields["published_at"] = ep.get("published_at") or timezone.now()

    episode, created = Episode.objects.get_or_create(season=season, number=num, defaults=fields)
    if created:
        summary["episodes_created"] += 1
    else:
        for k, v in fields.items():
            setattr(episode, k, v)
        episode.save()
        summary["episodes_updated"] += 1

    # Attach a video unless one is already present (idempotent re-runs won't re-pull).
    video = episode.video if (episode.video and episode.video.cf_stream_uid) else None
    if not video:
        uid = ep.get("cf_uid")
        source_url = ep.get("source_url")
        if not uid and source_url and pull_video:
            res = cloudflare.copy_from_url(source_url, name=episode.title,
                                           max_seconds=ep.get("max_seconds", 14400))
            if res.get("ok"):
                uid = res["uid"]
            else:
                summary["videos_skipped"] += 1        # e.g. Cloudflare not configured
        elif source_url and not pull_video:
            summary["videos_skipped"] += 1
        if uid:
            video = Video.objects.create(cf_stream_uid=uid, ready=bool(ep.get("ready", False)),
                                         duration_s=ep.get("duration_s", 0))
            episode.video = video
            episode.save(update_fields=["video"])
            summary["videos_queued"] += 1

    # Captions (declared per episode; optionally pushed to Cloudflare from a .vtt URL).
    if video:
        for cap in ep.get("captions", []):
            lang = cap.get("language")
            if not lang:
                continue
            _, made = Caption.objects.get_or_create(
                video=video, language=lang,
                defaults={"label": cap.get("label", ""), "ready": cap.get("ready", True)})
            if made:
                summary["captions_added"] += 1
            if cap.get("vtt_url") and pull_video:
                cloudflare.add_caption(video.cf_stream_uid, lang, cap["vtt_url"])


# ── CSV (flat, one row per episode) → manifest ──────────────────────────────────────────────
CSV_FIELDS = ["show_slug", "show_title", "show_description", "genre", "poster_url", "hero_url",
              "owner_email", "show_status", "collections", "season_number", "episode_number",
              "episode_title", "episode_description", "thumbnail_url", "duration_s",
              "source_url", "cf_uid", "episode_status"]


def csv_rows_to_manifest(rows) -> dict:
    """Group flat CSV rows (one per episode) into the nested shows→seasons→episodes manifest."""
    shows = {}
    for row in rows:
        slug = (row.get("show_slug") or slugify(row.get("show_title", ""))).strip()
        if not slug:
            continue
        show = shows.setdefault(slug, {
            "slug": slug, "title": row.get("show_title", slug).strip(),
            "description": row.get("show_description", "").strip(),
            "genre": [g for g in (row.get("genre", "") or "").split("|") if g],
            "poster_url": row.get("poster_url", "").strip(),
            "hero_url": row.get("hero_url", "").strip(),
            "owner_email": row.get("owner_email", "").strip(),
            "status": (row.get("show_status") or "").strip() or None,
            "collections": [c for c in (row.get("collections", "") or "").split("|") if c],
            "_seasons": {},
        })
        snum = int(row.get("season_number") or 1)
        season = show["_seasons"].setdefault(snum, {"number": snum, "episodes": []})
        if row.get("episode_number") or row.get("episode_title"):
            ep = {"number": int(row.get("episode_number") or len(season["episodes"]) + 1),
                  "title": row.get("episode_title", "").strip(),
                  "description": row.get("episode_description", "").strip(),
                  "thumbnail_url": row.get("thumbnail_url", "").strip(),
                  "duration_s": int(row.get("duration_s") or 0)}
            if row.get("source_url"):
                ep["source_url"] = row["source_url"].strip()
            if row.get("cf_uid"):
                ep["cf_uid"] = row["cf_uid"].strip()
            if row.get("episode_status"):
                ep["status"] = row["episode_status"].strip()
            season["episodes"].append(ep)

    out = []
    for show in shows.values():
        show["seasons"] = list(show.pop("_seasons").values())
        if show.get("status") is None:
            show.pop("status")
        out.append(show)
    return {"shows": out}
