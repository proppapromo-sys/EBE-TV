"""
In-app-purchase verification dispatch (Apple StoreKit 2 + Google Play Billing). The app sends its
signed transaction (Apple) or purchaseToken (Google); we verify with the provider, then normalize.

The provider-call internals are stubbed with the exact endpoints/SDKs to use — wire them with your
credentials. Until then these return `not_configured` rather than granting access (fail closed).
"""
from . import apple, google


def verify_and_apply_iap(user, platform, payload) -> dict:
    if platform == "apple":
        return apple.verify_and_apply(user, payload)
    if platform == "google":
        return google.verify_and_apply(user, payload)
    return {"ok": False, "error": "unknown_platform", "detail": "platform must be apple|google"}
