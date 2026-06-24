"""
Cloudflare Stream signed playback tokens — the gate's output.

Every video has "Require signed URLs" enabled, so a manifest is only playable with a short-lived
token minted here AFTER the entitlement check. DRM license requests (Widevine/FairPlay/PlayReady)
are authorized by this same token, so an unsubscribed user can never obtain a license.
"""
import base64
import time

from django.conf import settings

try:
    import jwt
except ImportError:
    jwt = None


def configured() -> bool:
    return bool(jwt and settings.CF_STREAM_SIGNING_KEY_ID and settings.CF_STREAM_SIGNING_KEY_PEM)


def _signing_key() -> str:
    """Cloudflare's /stream/keys returns the RSA private key base64-encoded; an admin may paste
    either that or the decoded PEM. Accept both — decode unless it's already PEM-armored."""
    raw = settings.CF_STREAM_SIGNING_KEY_PEM.strip()
    if "BEGIN" in raw:
        return raw
    try:
        return base64.b64decode(raw).decode("utf-8")
    except Exception:
        return raw


def signed_token(video_uid, user_id, ttl=None) -> str:
    ttl = ttl or settings.PLAYBACK_TOKEN_TTL
    now = int(time.time())
    payload = {
        "sub": video_uid,
        "kid": settings.CF_STREAM_SIGNING_KEY_ID,
        "exp": now + ttl,
        "nbf": now,
        # tie the token to the user for abuse tracing (optional, informational):
        "u": str(user_id),
        # tighten if needed, e.g. country/ip access rules:
        # "accessRules": [{"type": "any", "action": "allow"}],
    }
    return jwt.encode(payload, _signing_key(), algorithm="RS256",
                      headers={"kid": settings.CF_STREAM_SIGNING_KEY_ID})


def manifests(token):
    base = f"https://{settings.CF_CUSTOMER_SUBDOMAIN}/{token}/manifest"
    return {"dash": f"{base}/video.mpd", "hls": f"{base}/video.m3u8"}
