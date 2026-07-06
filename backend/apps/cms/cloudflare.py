"""Cloudflare Stream — server-side admin calls (direct upload URL, status polling, webhook auth)."""
import hashlib
import hmac

import requests
from django.conf import settings

API = "https://api.cloudflare.com/client/v4"


def configured() -> bool:
    return bool(settings.CF_ACCOUNT_ID and settings.CF_API_TOKEN)


def create_direct_upload(max_seconds=7200) -> dict:
    """One-time URL the CMS uploads the raw file to — the file never touches our server."""
    if not configured():
        return {"ok": False, "error": "cloudflare_not_configured",
                "detail": "set CF_ACCOUNT_ID / CF_API_TOKEN"}
    r = requests.post(
        f"{API}/accounts/{settings.CF_ACCOUNT_ID}/stream/direct_upload",
        headers={"Authorization": f"Bearer {settings.CF_API_TOKEN}"},
        json={"maxDurationSeconds": max_seconds, "requireSignedURLs": True,
              "allowedOrigins": ["*"]},
        timeout=20,
    )
    data = r.json()
    if not data.get("success"):
        return {"ok": False, "error": "cloudflare_error", "detail": data.get("errors")}
    res = data["result"]
    return {"ok": True, "uploadURL": res["uploadURL"], "uid": res["uid"]}


def copy_from_url(url, name="", max_seconds=14400) -> dict:
    """Bulk ingest's workhorse: tell Cloudflare to PULL a video from a public URL and transcode it,
    so a library is loaded by pointing at existing files instead of hand-uploading each one."""
    if not configured():
        return {"ok": False, "error": "cloudflare_not_configured"}
    r = requests.post(
        f"{API}/accounts/{settings.CF_ACCOUNT_ID}/stream/copy",
        headers={"Authorization": f"Bearer {settings.CF_API_TOKEN}"},
        json={"url": url, "meta": {"name": name}, "requireSignedURLs": True,
              "maxDurationSeconds": max_seconds},
        timeout=30,
    )
    data = r.json()
    if not data.get("success"):
        return {"ok": False, "error": "cloudflare_error", "detail": data.get("errors")}
    return {"ok": True, "uid": data["result"]["uid"]}


def add_caption(uid, language, vtt_url) -> dict:
    """Attach a subtitle track to a video from a public .vtt URL; Cloudflare embeds it in the
    manifest so the player can offer it. Graceful when unconfigured."""
    if not configured():
        return {"ok": False, "error": "cloudflare_not_configured"}
    r = requests.put(
        f"{API}/accounts/{settings.CF_ACCOUNT_ID}/stream/{uid}/captions/{language}",
        headers={"Authorization": f"Bearer {settings.CF_API_TOKEN}"},
        json={"url": vtt_url}, timeout=20,
    )
    data = r.json()
    if not data.get("success"):
        return {"ok": False, "error": "cloudflare_error", "detail": data.get("errors")}
    return {"ok": True}


def get_video_status(uid) -> dict:
    """Poll a video's transcode state — the webhook-free fallback for flipping `ready`.
    Returns {ok, ready, duration_s, state}."""
    if not configured():
        return {"ok": False, "error": "cloudflare_not_configured"}
    r = requests.get(
        f"{API}/accounts/{settings.CF_ACCOUNT_ID}/stream/{uid}",
        headers={"Authorization": f"Bearer {settings.CF_API_TOKEN}"},
        timeout=20,
    )
    data = r.json()
    if not data.get("success"):
        return {"ok": False, "error": "cloudflare_error", "detail": data.get("errors")}
    res = data["result"]
    return {"ok": True,
            "ready": res.get("readyToStream", False),
            "state": (res.get("status") or {}).get("state"),
            "duration_s": int(res.get("duration") or 0)}


def verify_webhook_signature(raw_body: bytes, header: str) -> bool:
    """Validate Cloudflare's `Webhook-Signature: time=<t>,sig1=<hex>` header.
    sig1 = HMAC-SHA256(secret, "<time>.<body>"). Returns True only when it matches.
    If no CF_WEBHOOK_SECRET is configured, verification is disabled (returns True)."""
    secret = settings.CF_WEBHOOK_SECRET
    if not secret:
        return True                     # not configured → don't block (dev / not yet wired)
    if not header:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    t, sig = parts.get("time"), parts.get("sig1")
    if not t or not sig:
        return False
    expected = hmac.new(secret.encode(), f"{t}.".encode() + raw_body,
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
