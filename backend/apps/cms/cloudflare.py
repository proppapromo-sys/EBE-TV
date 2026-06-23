"""Cloudflare Stream — server-side admin calls (direct upload URL + webhook handling)."""
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
