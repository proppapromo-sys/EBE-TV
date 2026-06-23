"""
Cloudflare Stream signed playback tokens — the gate's output.

Every video has "Require signed URLs" enabled, so a manifest is only playable with a short-lived
token minted here AFTER the entitlement check. DRM license requests (Widevine/FairPlay/PlayReady)
are authorized by this same token, so an unsubscribed user can never obtain a license.
"""
import time

from django.conf import settings

try:
    import jwt
except ImportError:
    jwt = None


def configured() -> bool:
    return bool(jwt and settings.CF_STREAM_SIGNING_KEY_ID and settings.CF_STREAM_SIGNING_KEY_PEM)


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
    return jwt.encode(payload, settings.CF_STREAM_SIGNING_KEY_PEM, algorithm="RS256",
                      headers={"kid": settings.CF_STREAM_SIGNING_KEY_ID})


def manifests(token):
    base = f"https://{settings.CF_CUSTOMER_SUBDOMAIN}/{token}/manifest"
    return {"dash": f"{base}/video.mpd", "hls": f"{base}/video.m3u8"}
